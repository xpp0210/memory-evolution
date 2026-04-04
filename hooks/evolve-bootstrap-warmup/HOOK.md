---
name: evolve-bootstrap-warmup
description: "Agent启动时注入最近记忆进化状态到bootstrap上下文"
metadata:
  openclaw:
    emoji: "🔥"
    events:
      - "agent:bootstrap"
    requires:
      bins: ["bash"]
---
# evolve-bootstrap-warmup

在Agent bootstrap阶段，构建用户画像摘要（姓名/角色/技术栈/偏好/固化规则）并注入到上下文，同时加载最近的进化状态（能力图谱、今日记忆、待补强项、梦境洞察），让每次新会话都"带着记忆和画像醒来"。

v2: 借鉴claw_lance_memory的agent:bootstrap注入思路，新增用户画像自动构建 + procedures偏好提取 + 梦境洞察注入。
