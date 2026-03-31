# Memory Evolution Skill

> 融合 MemSkill（元记忆）+ Memento-Skills（反思循环）+ 自我迭代法
> 版本：1.1.0 | 2026-03-31

## 这是什么

一套**可移植的 AI Agent 记忆进化体系**，让任何 OpenClaw 实例具备：

1. **元记忆技能库** — 不是存更多内容，而是学会"怎么记"
2. **自动反思循环** — 每次任务后自动评估，失败是训练信号
3. **数据驱动进化** — 积累 success/fail 数据，自动触发技能优化
4. **自我迭代流程** — 用户触发的深度复盘

## 核心理念

```
传统记忆：存什么 → 存内容（越多越好）
元记忆：  怎么存 → 存技能（精简高质量）
```

三篇论文支撑：
- **MemSkill**（arXiv:2602.02474）— 元记忆范式
- **Memento-Skills**（arXiv:2603.18743）— 反思闭环
- **5步自我迭代法**（娇姐话AI圈）— 复盘框架

## 反思循环：每次任务后自动执行

### 步骤1：ROUTE（路由）

任务完成后，判断属于哪个 skill：

| 触发条件 | Skill |
|---------|-------|
| 工具调用失败、命令报错 | `error-debug` |
| 深入分析项目或话题 | `deep-research` |
| 安装新工具/插件/Skill | `tool-install` |
| 保存/写文档/发飞书 | `doc-creation` |
| 写代码/修bug/重构 | `code-dev` |
| 检查系统/定时任务/备份 | `daily-ops` |
| 阅读后沉淀知识 | `learning-extract` |
| 同类错误≥2次、用户不满 | `self-evolve` |

### 步骤2：EXECUTE（执行）

按匹配 skill 的 `action` 执行任务。

### 步骤3：REFLECT（反思）

任务完成后，用 skill 的 `reflect_checks` 自检：
- 根因是否准确？
- 解决方案是否彻底？
- 是否需要更新规则库？
- 有没有重复犯的错？

### 步骤4：WRITE（记录）

**任务成功** → `success_count += 1`
**任务失败** → `fail_count += 1`，并记录到 `reflect_log`

### 步骤5：EVOLVE（进化）

当 `fail_count >= 3` 时：
1. 分析失败模式
2. 定位根因（能力/态度/流程）
3. 优化 skill 的 action 或 memory_focus
4. 写回 memory-skills.json
5. 如需新规则，追加到 iteration-rules.md

## 实际执行方式

### 心跳时执行

在 HEARTBEAT.md 中添加反思检查，每次心跳自动运行 `scripts/reflect.sh`。

### 任务完成时更新

每次完成任务后，Agent 应：
1. 判断匹配的 skill
2. 评估成功/失败
3. 更新 memory-skills.json 的计数器
4. 如果 fail_count >= 3，触发进化

### 查看状态

```bash
bash ~/.openclaw/workspace/scripts/reflect.sh
```

### 深度复盘（手动触发）

用户说"自我迭代"/"复盘"/"反思"时，执行完整 5 步流程。

## 自定义

### 修改技能库

编辑 `memory/memory-skills.json`，每个技能结构：

```json
{
  "id": "skill-id",
  "name": "技能名称",
  "trigger": "触发条件",
  "action": "执行步骤",
  "memory_focus": "只记什么",
  "reflect_checks": ["自检问题"],
  "priority": "high|medium|low",
  "success_count": 0,
  "fail_count": 0
}
```

### 适配不同角色

- **写作助手**：drafting / editing / publishing / research
- **项目管理者**：planning / tracking / reporting / review
- **学习伴侣**：note-taking / spaced-review / concept-mapping

## 来源

| 来源 | 贡献 |
|------|------|
| MemSkill (arXiv:2602.02474) | 元记忆范式 |
| Memento-Skills (arXiv:2603.18743) | 反思闭环 |
| 娇姐话AI圈 | 5步自我迭代法 |
| OpenSpace | 自动FIX + Skill派生 |
