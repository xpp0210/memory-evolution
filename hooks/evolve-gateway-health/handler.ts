const handler = async (event: any) => {
  if (event.type !== "gateway:startup") return;

  const workspaceDir = process.env.OPENCLAW_WORKSPACE_DIR ||
    require("path").join(process.env.HOME, ".openclaw", "workspace");
  const path = require("path");
  const { execFile } = require("child_process");

  // Fire-and-forget health check
  execFile("bash", [
    path.join(workspaceDir, "scripts", "evolve"), "check",
  ], {
    timeout: 60000,
    env: { ...process.env, OPENCLAW_WORKSPACE_DIR: workspaceDir },
  }, (err: any, stdout: any, stderr: any) => {
    if (err) {
      console.error(`[evolve-gateway-health] check failed: ${err.message}`);
      return;
    }
    // Check for issues in output
    const output = (stdout || "") + (stderr || "");
    if (output.includes("FAIL") || output.includes("CRITICAL") || output.includes("❌")) {
      event.messages.push(
        `🏥 记忆进化系统健康检查发现问题：\n${output.slice(0, 500)}`
      );
    } else {
      console.log(`[evolve-gateway-health] system healthy`);
    }
  });
};

export default handler;
