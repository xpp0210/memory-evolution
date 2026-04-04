const handler = async (event: any) => {
  // Trigger on session end or significant tool completion
  const ctx = event.context || {};
  const body = ctx.bodyForAgent || "";

  // Detect task completion signals in messages
  const completionSignals = ["✅", "完成", "done", "成功", "已修复", "fixed"];
  const hasCompletion = completionSignals.some(s => body.includes(s));

  if (!hasCompletion) return;

  const fs = require("fs");
  const path = require("path");
  const workspaceDir = ctx.workspaceDir || process.env.OPENCLAW_WORKSPACE_DIR || path.join(process.env.HOME, ".openclaw", "workspace");

  // Write to learn-queue for async processing
  const queueDir = path.join(workspaceDir, "data", "memory-evolution", "learn-queue");
  const timestamp = new Date().toISOString().replace(/[:.]/g, "-");
  const queueFile = path.join(queueDir, `completed-${timestamp}.json`);

  const entry = {
    type: "task_completed",
    timestamp: new Date().toISOString(),
    sessionKey: event.sessionKey || "unknown",
    summary: body.slice(0, 500),
    signals: completionSignals.filter(s => body.includes(s)),
  };

  try {
    fs.mkdirSync(queueDir, { recursive: true });
    fs.writeFileSync(queueFile, JSON.stringify(entry, null, 2));

    // v5.0: Trigger LLM reflect asynchronously
    const { execFile } = require("child_process");
    const reflectScript = path.join(workspaceDir, "skills", "memory-evolution", "scripts", "reflect-llm.py");

    execFile("python3", [
      "-c",
      `import importlib.util,sys,json,urllib.parse; spec=importlib.util.spec_from_file_location('r','${reflectScript}'); m=importlib.util.module_from_spec(spec); sys.argv=['reflect-llm.py','reflect','--task',urllib.parse.quote('${body.slice(0,100).replace(/'/g,"")}' ),'--status','success']; spec.loader.exec_module(m)`
    ], {
      timeout: 120000,
      detached: true,
    }, (err: any) => {
      if (err) console.error(`[evolve-task-completed] reflect failed: ${err.message}`);
    });
  } catch (e: any) {
    console.error(`[evolve-task-completed] failed: ${e.message}`);
  }
};

export default handler;
