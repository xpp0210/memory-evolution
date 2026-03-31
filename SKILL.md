# Memory Evolution Skill

> 融合 MemSkill（元记忆）+ Memento-Skills（反思循环）+ 自我迭代法
> 版本：1.0.0 | 2026-03-31

## 这是什么

一套**可移植的 AI Agent 记忆进化体系**，让任何 OpenClaw 实例具备：

1. **元记忆技能库** — 不是存更多内容，而是学会"怎么记"
2. **自动反思循环** — 每次任务后自动评估，失败是训练信号
3. **数据驱动进化** — 积累 success/fail 数据，自动触发技能优化
4. **自我迭代流程** — 用户触发的深度复盘

## 核心理念

```
传统记忆：  存什么 → 存内容（越多越好）
元记忆：    怎么存 → 存技能（精简高质量）
```

三篇论文支撑：
- **MemSkill**（arXiv:2602.02474）— 元记忆范式，技能条件化的记忆构建
- **Memento-Skills**（arXiv:2603.18743）— Read→Execute→Reflect→Write 闭环
- **5步自我迭代法**（娇姐话AI圈）— 实用的复盘框架

## 架构

```
┌─────────────────────────────────────────┐
│            Memory Skill Bank             │
│         (memory-skills.json)             │
│  8个核心技能 × trigger/action/focus      │
└──────────────┬──────────────────────────┘
               │
    ┌──────────┴──────────┐
    ▼                      ▼
┌────────┐          ┌──────────┐
│Reflect │          │ Designer  │
│ Loop   │          │ (进化引擎)│
└───┬────┘          └────┬─────┘
    │                     │
    ▼                     ▼
┌─────────────────────────────────────┐
│          输出目标                    │
│  iteration-rules.md (固化规则)       │
│  reflect_log       (归因记录)       │
│  MEMORY.md         (长期记忆)       │
└─────────────────────────────────────┘
```

## 工作流程

### 1. 任务开始时 → ROUTE

识别当前任务属于哪个 skill：
- 工具调用失败 → `error-debug`
- 深入研究项目 → `deep-research`
- 安装新工具 → `tool-install`
- 创建文档 → `doc-creation`
- 写代码 → `code-dev`
- 系统检查 → `daily-ops`
- 学习沉淀 → `learning-extract`
- 同类错误≥2次 → `self-evolve`

### 2. 任务执行中 → EXECUTE

按匹配 skill 的 `action` 字段执行。

### 3. 任务完成后 → REFLECT

用 skill 的 `reflect_checks` 自检：
- 用户对结果满意吗？
- 有没有中途纠正或重做？
- 哪个环节耗时最长？
- 有什么可以下次跳过的冗余步骤？

### 4. 评估结果 → ATTRIBUTE + WRITE

- **成功** → skill.success_count + 1
- **失败** → skill.fail_count + 1 + 记录归因到 reflect_log

### 5. 定期检查 → EVOLVE

- 某 skill `fail_count ≥ 3` → 触发 Designer 优化
- 发现新场景无匹配技能 → 自动提议新技能
- 每周心跳回顾各技能成功率

## 安装方法

### 方式一：快速安装（推荐）

```bash
# 1. 复制 skill 到你的 OpenClaw workspace
cp -r skills/memory-evolution/ ~/.openclaw/workspace/skills/

# 2. 复制模板文件
cp skills/memory-evolution/templates/memory-skills.json ~/.openclaw/workspace/memory/
cp skills/memory-evolution/templates/iteration-rules.md ~/.openclaw/workspace/memory/

# 3. 初始化记忆技能库
# （首次使用时，skill 会自动初始化）
```

### 方式二：自定义安装

1. 复制 `templates/memory-skills.json` 到 `~/.openclaw/workspace/memory/`
2. 复制 `templates/iteration-rules.md` 到 `~/.openclaw/workspace/memory/`
3. 在 AGENTS.md 中添加自动进化机制章节（参考 `templates/agents-additions.md`）
4. 在 HEARTBEAT.md 中加入每周技能回顾任务

## 文件清单

```
skills/memory-evolution/
├── SKILL.md                    ← 你正在读的这个文件
├── templates/
│   ├── memory-skills.json      ← 元记忆技能库模板
│   ├── iteration-rules.md      ← 固化规则库模板
│   └── agents-additions.md     ← 需要添加到 AGENTS.md 的内容
└── scripts/
    └── init-memory-skill.sh    ← 初始化脚本
```

## 自定义

### 修改技能库

编辑 `memory/memory-skills.json`，按需增删技能。每个技能结构：

```json
{
  "id": "your-skill-id",
  "name": "技能名称",
  "trigger": "触发条件描述",
  "action": "执行步骤",
  "memory_focus": "只记什么，不记什么",
  "reflect_checks": ["自检问题1", "自检问题2"],
  "priority": "high|medium|low",
  "success_count": 0,
  "fail_count": 0
}
```

### 适配不同角色

默认技能库面向**技术型 AI 助手**。如果你的角色不同：

- **写作助手**：替换为 `drafting` / `editing` / `publishing` / `research` 等技能
- **项目管理者**：替换为 `planning` / `tracking` / `reporting` / `review` 等技能
- **学习伴侣**：替换为 `note-taking` / `spaced-review` / `concept-mapping` 等技能

核心框架（反思循环 + 进化机制）不变，只替换技能内容。

## 来源与致谢

| 来源 | 贡献 |
|------|------|
| MemSkill（arXiv:2602.02474） | 元记忆范式、技能条件化记忆构建 |
| Memento-Skills（arXiv:2603.18743） | Read→Execute→Reflect→Write 闭环 |
| 娇姐话AI圈 | 5步自我迭代法 |
| OpenSpace | 自动FIX + Skill派生思想 |
