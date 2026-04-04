---
name: evolve-compact-capture
description: "LCM压缩后自动蒸馏关键知识到记忆进化系统"
metadata:
  openclaw:
    emoji: "🧠"
    events:
      - "session:compact:after"
    requires:
      bins: ["bash"]
---
# evolve-compact-capture

在LCM上下文压缩完成后，自动触发记忆进化系统的蒸馏流程，将被压缩的关键知识保存到knowledge库，防止信息流失。
