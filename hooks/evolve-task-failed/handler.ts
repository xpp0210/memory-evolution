const handler = async (event: any) => {
  // Trigger on error/failure signals in messages
  const ctx = event.context || {};
  const body = ctx.bodyForAgent || "";

  // Detect failure signals
  const failureSignals = ["❌", "失败", "error", "failed", "超时", "timeout", "SIGKILL", "异常"];
  const hasFailure = failureSignals.some(s => body.toLowerCase().includes(s.toLowerCase()));

  if (!hasFailure) return;

  const fs = require("fs");
  const path = require("path");
  const workspaceDir = ctx.workspaceDir || process.env.OPENCLAW_WORKSPACE_DIR || path.join(process.env.HOME, ".openclaw", "workspace");

  // Write to learn-queue
  const queueDir = path.join(workspaceDir, "data", "memory-evolution", "learn-queue");
  const timestamp = new Date().toISOString().replace(/[:.]/g, "-");
  const queueFile = path.join(queueDir, `failed-${timestamp}.json`);

  const entry = {
    type: "task_failed",
    timestamp: new Date().toISOString(),
    sessionKey: event.sessionKey || "unknown",
    error: body.slice(0, 500),
    signals: failureSignals.filter(s => body.toLowerCase().includes(s.toLowerCase())),
  };

  try {
    fs.mkdirSync(queueDir, { recursive: true });
    fs.writeFileSync(queueFile, JSON.stringify(entry, null, 2));

    // v5.0: Trigger LLM attribute (root cause analysis) asynchronously
    const { execFile } = require("child_process");
    const reflectScript = path.join(workspaceDir, "skills", "memory-evolution", "scripts", "reflect-llm.py");

    // Extract error snippet for attribution
    const errorSnippet = body.slice(0, 200).replace(/"/g, '\\"').replace(/\n/g, " ");

    execFile("python3", [
      "-c",
      `import importlib.util,sys; spec=importlib.util.spec_from_file_location('r','${reflectScript}'); m=importlib.util.module_from_spec(spec); sys.argv=['reflect-llm.py','attribute','--task','auto-detected','--error','${errorSnippet}']; spec.loader.exec_module(m)`
    ], {
      timeout: 120000,
      detached: true,
    }, (err: any) => {
      if (err) console.error(`[evolve-task-failed] attribute failed: ${err.message}`);
    });
  } catch (e: any) {
    console.error(`[evolve-task-failed] failed: ${e.message}`);
  }
};

export default handler;
