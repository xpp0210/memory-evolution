const handler = async (event: any) => {
  if (event.type !== "session:compact:after") return;

  const ctx = event.context || {};
  const tokensBefore = ctx.tokensBefore || 0;
  const tokensAfter = ctx.tokensAfter || 0;
  const compactedCount = ctx.compactedCount || 0;
  const sessionKey = event.sessionKey || "unknown";

  if (compactedCount < 5) return;

  const compressionRatio = tokensBefore > 0
    ? ((1 - tokensAfter / tokensBefore) * 100).toFixed(1)
    : "0";

  const timestamp = new Date().toISOString();
  const logLine = `[${timestamp}] compact: session=${sessionKey} before=${tokensBefore} after=${tokensAfter} compacted=${compactedCount} ratio=${compressionRatio}%\n`;

  const fs = require("fs");
  const path = require("path");
  const workspaceDir = ctx.workspaceDir || process.env.OPENCLAW_WORKSPACE_DIR || path.join(process.env.HOME, ".openclaw", "workspace");
  const logFile = path.join(workspaceDir, "data", "memory-evolution", "compact-events.log");

  try {
    fs.mkdirSync(path.dirname(logFile), { recursive: true });
    fs.appendFileSync(logFile, logLine);
  } catch (e: any) {
    console.error(`[evolve-compact-capture] log write failed: ${e.message}`);
  }

  // v5.0: Use LLM distill for significant compression (>40%)
  const { execFile } = require("child_process");
  const distillScript = path.join(workspaceDir, "skills", "memory-evolution", "scripts", "memory-llm-distill.py");
  const python3 = process.env.PYTHON3 || "python3";

  if (parseFloat(compressionRatio) > 40) {
    const todayLog = path.join(workspaceDir, "memory", `${new Date().toISOString().slice(0, 10)}.md`);

    // If today's log exists, distill it
    try {
      if (fs.existsSync(todayLog)) {
        execFile(python3, [
          "-c",
          `import importlib.util, sys; spec=importlib.util.spec_from_file_location('d','${distillScript}'); m=importlib.util.module_from_spec(spec); sys.argv=['distill','--source','${todayLog}']; spec.loader.exec_module(m)`
        ], {
          timeout: 120000,
          detached: true,
        }, (err: any) => {
          if (err) console.error(`[evolve-compact-capture v5] LLM distill failed: ${err.message}`);
        });
      }
    } catch (e: any) {
      console.error(`[evolve-compact-capture v5] exec failed: ${e.message}`);
    }
  }

  // Notify about significant compression
  if (compactedCount >= 15) {
    event.messages.push(
      `🧠 会话压缩完成：${compactedCount}条消息被压缩（${compressionRatio}%），已触发LLM知识蒸馏`
    );
  }
};

export default handler;
