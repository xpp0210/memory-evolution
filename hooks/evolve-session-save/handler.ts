const handler = async (event: any) => {
  const action = event.action; // "new" or "reset"
  if (event.type !== "command" || !["new", "reset"].includes(action)) return;

  const ctx = event.context || {};
  const sessionKey = event.sessionKey || "unknown";
  const workspaceDir = ctx.workspaceDir || process.env.OPENCLAW_WORKSPACE_DIR ||
    require("path").join(process.env.HOME, ".openclaw", "workspace");

  const fs = require("fs");
  const path = require("path");

  // Fire-and-forget: run session-save script
  const { execFile } = require("child_process");
  const now = new Date();
  const dateStr = now.toISOString().slice(0, 10);
  const memoryDir = path.join(workspaceDir, "memory");

  try {
    fs.mkdirSync(memoryDir, { recursive: true });

    // Record session transition event
    const entry = {
      timestamp: now.toISOString(),
      action,
      sessionKey,
    };

    const stateFile = path.join(memoryDir, "session-transitions.json");
    let transitions: any[] = [];
    try {
      transitions = JSON.parse(fs.readFileSync(stateFile, "utf-8"));
    } catch { /* empty file or missing */ }

    // Keep last 50 transitions
    transitions.push(entry);
    if (transitions.length > 50) transitions = transitions.slice(-50);
    fs.writeFileSync(stateFile, JSON.stringify(transitions, null, 2));

    // Trigger reflect if we had a meaningful session
    // (reflected via evolve diagnose)
    execFile("bash", [
      path.join(workspaceDir, "scripts", "evolve"), "diagnose",
      `session-${action}`, "partial", "auto-triggered by ${action} command",
    ], {
      timeout: 30000,
      env: { ...process.env, OPENCLAW_WORKSPACE_DIR: workspaceDir },
      detached: true,
    }, (err: any) => {
      if (err) console.error(`[evolve-session-save] diagnose failed: ${err.message}`);
    });

  } catch (e: any) {
    console.error(`[evolve-session-save] error: ${e.message}`);
  }
};

export default handler;
