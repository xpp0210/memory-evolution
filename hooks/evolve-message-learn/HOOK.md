---
name: evolve-message-learn
description: "监听消息中的学习信号（URL、代码、技术术语），自动记录到待学习队列"
metadata:
  openclaw:
    emoji: "📚"
    events:
      - "message:preprocessed"
    requires:
      bins: ["bash"]
---
# evolve-message-learn

从用户消息中识别学习信号（GitHub链接、技术文章URL、代码片段、关键技术术语），自动触发 `evolve capture` 记录到待学习队列，不遗漏任何知识来源。
