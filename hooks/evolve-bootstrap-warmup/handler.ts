const handler = async (event: any) => {
  if (event.type !== "agent:bootstrap") return;

  const ctx = event.context || {};
  const bootstrapFiles = ctx.bootstrapFiles;
  if (!bootstrapFiles || !Array.isArray(bootstrapFiles)) return;

  const fs = require("fs");
  const path = require("path");
  const workspaceDir = ctx.workspaceDir || process.env.OPENCLAW_WORKSPACE_DIR ||
    path.join(process.env.HOME, ".openclaw", "workspace");

  const warmupParts: string[] = [];

  // === 借鉴claw_lance: 用户画像注入 ===
  // 从USER.md + procedures.md生成精简画像，注入到每次会话开头
  const userProfile = buildUserProfile(workspaceDir);
  if (userProfile) warmupParts.push(userProfile);

  // 1. Recent capability map
  const capMap = path.join(workspaceDir, "data", "memory-evolution", "capability-map.json");
  try {
    const map = JSON.parse(fs.readFileSync(capMap, "utf-8"));
    const topSkills = (map.skills || [])
      .sort((a: any, b: any) => (b.success_count || 0) - (a.success_count || 0))
      .slice(0, 5)
      .map((s: any) => `${s.skill_id}(${s.success_count}次)`)
      .join(", ");
    if (topSkills) warmupParts.push(`## 能力Top5\n${topSkills}`);
  } catch { /* no capability map yet */ }

  // 2. Today's memory
  const today = new Date().toISOString().slice(0, 10);
  const todayFile = path.join(workspaceDir, "memory", `${today}.md`);
  try {
    if (fs.existsSync(todayFile)) {
      const content = fs.readFileSync(todayFile, "utf-8");
      if (content.length > 500) {
        warmupParts.push(`## 今日记忆摘要\n${content.slice(0, 500)}...`);
      } else if (content.trim()) {
        warmupParts.push(`## 今日记忆\n${content}`);
      }
    }
  } catch { /* ignore */ }

  // 3. Yesterday's memory (brief)
  const yesterday = new Date(Date.now() - 86400000).toISOString().slice(0, 10);
  const yesterdayFile = path.join(workspaceDir, "memory", `${yesterday}.md`);
  try {
    if (fs.existsSync(yesterdayFile)) {
      const content = fs.readFileSync(yesterdayFile, "utf-8");
      if (content.trim()) {
        warmupParts.push(`## 昨日记忆(简)\n${content.slice(0, 300)}`);
      }
    }
  } catch { /* ignore */ }

  // 4. Active reinforcement plan
  const planFile = path.join(workspaceDir, "data", "memory-evolution", "reinforcement-plan.json");
  try {
    if (fs.existsSync(planFile)) {
      const plan = JSON.parse(fs.readFileSync(planFile, "utf-8"));
      const pending = (plan.items || []).filter((i: any) => i.status === "pending");
      if (pending.length > 0) {
        warmupParts.push(`## 待补强(${pending.length}项)\n${pending.slice(0, 3).map((i: any) => `- ${i.name || i.id}`).join("\n")}`);
      }
    }
  } catch { /* ignore */ }

  // 5. Recent dream insights (from Auto-Dream)
  const dreamLog = path.join(workspaceDir, "memory", "dream-log.md");
  try {
    if (fs.existsSync(dreamLog)) {
      const content = fs.readFileSync(dreamLog, "utf-8");
      // Extract last dream's insights section
      const lastDream = content.split("## 🌀 Dream Report").pop();
      if (lastDream) {
        const insightMatch = lastDream.match(/### 🔮 Insights\n([\s\S]*?)(?=\n###)/);
        if (insightMatch) {
          warmupParts.push(`## 最近梦境洞察\n${insightMatch[1].trim().slice(0, 300)}`);
        }
      }
    }
  } catch { /* ignore */ }

  if (warmupParts.length === 0) return;

  const warmupContent = `# 会话预热上下文\n\n${warmupParts.join("\n\n")}\n`;
  const warmupPath = path.join(workspaceDir, "EVOLVE-WARMUP.md");
  try {
    fs.writeFileSync(warmupPath, warmupContent);
    if (!bootstrapFiles.some((f: string) => f.includes("EVOLVE-WARMUP"))) {
      bootstrapFiles.push(warmupPath);
    }
  } catch (e: any) {
    console.error(`[evolve-bootstrap-warmup] write failed: ${e.message}`);
  }
};

function buildUserProfile(workspaceDir: string): string | null {
  const fs = require("fs");
  const path = require("path");

  // 从USER.md提取核心信息
  const userFile = path.join(workspaceDir, "USER.md");
  // 从procedures.md提取偏好
  const procFile = path.join(workspaceDir, "memory", "procedures.md");
  // 从iteration-rules.md提取固化规则
  const rulesFile = path.join(workspaceDir, "memory", "iteration-rules.md");

  const lines: string[] = ["## 用户画像（自动注入）"];

  try {
    if (fs.existsSync(userFile)) {
      const content = fs.readFileSync(userFile, "utf-8");
      // Extract key info: name, role, tech stack, preferences
      const nameMatch = content.match(/[-*]\s*\*?\*?姓名[：:]\*?\*?\s*(.+)/);
      const roleMatch = content.match(/[-*]\s*\*?\*?(?:角色|职位|工作)[：:]\*?\*?\s*(.+)/);
      const stackMatch = content.match(/\*\*核心\*\*[：:]\s*(.+)/);
      if (nameMatch) lines.push(`- 姓名: ${nameMatch[1].trim()}`);
      if (roleMatch) lines.push(`- 角色: ${roleMatch[1].trim()}`);
      if (stackMatch) lines.push(`- 核心技术栈: ${stackMatch[1].trim()}`);
    }
  } catch { /* ignore */ }

  try {
    if (fs.existsSync(procFile)) {
      const content = fs.readFileSync(procFile, "utf-8");
      // Extract non-comment, non-empty preference lines
      const prefs = content.split("\n")
        .filter(l => l.trim() && !l.trim().startsWith("<!--") && !l.trim().startsWith("#") && !l.trim().startsWith("_") && !l.trim().startsWith("---"))
        .slice(0, 5)
        .map(l => `- ${l.trim().replace(/^[-*]\s*/, "")}`);
      if (prefs.length > 0) lines.push(`- 偏好: ${prefs.join("; ")}`);
    }
  } catch { /* ignore */ }

  try {
    if (fs.existsSync(rulesFile)) {
      const content = fs.readFileSync(rulesFile, "utf-8");
      const ruleCount = (content.match(/^\d+\./gm) || []).length;
      if (ruleCount > 0) lines.push(`- 固化规则: ${ruleCount}条`);
    }
  } catch { /* ignore */ }

  return lines.length > 1 ? lines.join("\n") : null;
}

export default handler;
