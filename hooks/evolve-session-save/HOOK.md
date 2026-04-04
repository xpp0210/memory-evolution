---
name: evolve-session-save
description: "会话重置时自动保存关键上下文到memory"
metadata:
  openclaw:
    emoji: "💾"
    events:
      - "command:new"
      - "command:reset"
    requires:
      bins: ["bash"]
---
# evolve-session-save

在 `/new` 或 `/reset` 时，自动保存当前会话关键信息到 memory/ 目录，确保会话记忆不丢失。
