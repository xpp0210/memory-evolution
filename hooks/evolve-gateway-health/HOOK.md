---
name: evolve-gateway-health
description: "Gateway启动时自动运行记忆进化系统健康检查"
metadata:
  openclaw:
    emoji: "🏥"
    events:
      - "gateway:startup"
    requires:
      bins: ["bash"]
---
# evolve-gateway-health

Gateway启动时自动运行 `evolve check`，检测系统健康状态，发现问题主动通知。
