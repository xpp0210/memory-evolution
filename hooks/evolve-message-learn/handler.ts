const handler = async (event: any) => {
  if (event.type !== "message:preprocessed") return;

  const ctx = event.context || {};
  const body = ctx.bodyForAgent || "";
  const from = ctx.from || "";

  // Skip if no content or too short
  if (!body || body.length < 20) return;

  const fs = require("fs");
  const path = require("path");
  const workspaceDir = process.env.OPENCLAW_WORKSPACE_DIR ||
    path.join(process.env.HOME, ".openclaw", "workspace");

  // Learning signal patterns
  const signals: { type: string; matches: string[] }[] = [];

  // 1. GitHub URLs
  const githubRe = /https?:\/\/github\.com\/[^\s)\]"']+/g;
  const githubMatches = body.match(githubRe);
  if (githubMatches) {
    signals.push({ type: "github", matches: [...new Set(githubMatches)] });
  }

  // 2. Technical article URLs (medium, dev.to, blog, etc.)
  const articleRe = /https?:\/\/(?:medium\.com|dev\.to|blog\.[^\s]+\.(com|io|dev)|juejin\.cn|zhuanlan\.zhihu\.com|mp\.weixin\.qq\.com|docs\.[^\s]+|arxiv\.org)\/[^\s)\]"']+/gi;
  const articleMatches = body.match(articleRe);
  if (articleMatches) {
    signals.push({ type: "article", matches: [...new Set(articleMatches)] });
  }

  // 3. X/Twitter links (potential long-form content)
  const twitterRe = /https?:\/\/(?:x\.com|twitter\.com)\/\w+\/status\/\d+/g;
  const twitterMatches = body.match(twitterRe);
  if (twitterMatches) {
    signals.push({ type: "tweet", matches: [...new Set(twitterMatches)] });
  }

  // 4. Code blocks (```...```)
  const codeBlockRe = /```[\s\S]*?```/g;
  const codeMatches = body.match(codeBlockRe);
  if (codeMatches && codeMatches.length > 0) {
    const langs = codeMatches
      .map((b: string) => b.split("\n")[0].replace(/`/g, "").trim())
      .filter((l: string) => l && l.length < 20);
    signals.push({ type: "code", matches: [...new Set(langs)] });
  }

  // 5. Key tech terms (weighted list)
  const techTerms = [
    "agent", "RAG", "fine-tun", "embedd", "vector", "MCP",
    "tool-use", "multi-agent", "workflow", "pipeline",
    "Spring AI", "LangChain", "Claude", "OpenAI", "LLM",
    "hook", "plugin", "skill", "memory", "context window",
    "inference", "prompt", "chain-of-thought", "CoT",
    "function call", "retriev", "benchmark", "evaluat",
    "蒸馏", "进化", "自诊断", "反思",
  ];
  const foundTerms = techTerms.filter(t =>
    body.toLowerCase().includes(t.toLowerCase())
  );
  if (foundTerms.length >= 2) {
    signals.push({ type: "terms", matches: [...new Set(foundTerms)] });
  }

  if (signals.length === 0) return;

  // Write to learning queue
  const queueDir = path.join(workspaceDir, "data", "memory-evolution", "learn-queue");
  const queueFile = path.join(queueDir, `${new Date().toISOString().replace(/[:.]/g, "-")}.json`);

  const entry = {
    timestamp: new Date().toISOString(),
    from,
    signals,
    preview: body.slice(0, 200),
  };

  try {
    fs.mkdirSync(queueDir, { recursive: true });
    fs.writeFileSync(queueFile, JSON.stringify(entry, null, 2));

    // Trim queue to last 100 items
    const files = fs.readdirSync(queueDir)
      .filter((f: string) => f.endsWith(".json"))
      .sort();
    if (files.length > 100) {
      files.slice(0, files.length - 100).forEach((f: string) => {
        fs.unlinkSync(path.join(queueDir, f));
      });
    }
  } catch (e: any) {
    console.error(`[evolve-message-learn] write failed: ${e.message}`);
  }
};

export default handler;
