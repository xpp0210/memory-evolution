# 🧠 Memory Evolution — AI Agent 记忆进化体系

> 让任何 OpenClaw 实例从"被动记忆"进化为"主动学习"
> 融合 3 篇前沿研究论文 + 实战经验打磨

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![OpenClaw](https://img.shields.io/badge/OpenClaw-Compatible-blue.svg)](https://github.com/openclaw/openclaw)

---

## 📖 这个项目是什么

Memory Evolution 是一套**可移植的 AI Agent 记忆进化框架**，解决了一个核心问题：

**AI Agent 的记忆只会增长，不会进化。**

每次对话，Agent 记住更多信息，但从不反思"我记住了什么、记住了多少是有用的、哪些记忆方式需要改进"。这导致：

- 📈 记忆文件持续膨胀（500行 → 1000行 → 失控）
- 🔁 同类错误反复出现（上次踩的坑下次还踩）
- 🤷 用户不满意但 Agent 不知道为什么
- 🧊 记忆变成冰冷的日志，而非活的经验

**Memory Evolution 让 Agent 学会"如何记忆"而非"记住更多"。**

---

## 🌱 产生的原因

### 问题背景

在长期使用 [OpenClaw](https://github.com/openclaw/openclaw)（开源 AI Agent 平台）的过程中，我们遇到了真实的记忆管理困境：

1. **MEMORY.md 膨胀**：从初始几十行增长到 967 行，信息密度持续下降
2. **重复犯错**：同样的工具调用错误在 3 天内出现了 4 次
3. **记忆无结构**：各种信息混在一起——技术笔记、用户偏好、工具配置、经验教训
4. **进化靠人工**：只有用户明确说"复盘"时，Agent 才会反思改进

### 灵感来源

我们发现了三篇互补的研究，恰好覆盖了记忆进化的三个维度：

| 维度 | 论文 | 核心贡献 |
|------|------|---------|
| **怎么记** | [MemSkill](https://arxiv.org/abs/2602.02474) (ViktorAxelsen) | 元记忆范式——不是记内容，而是存"记忆技能" |
| **怎么学** | [Memento-Skills](https://arxiv.org/abs/2603.18743) (Memento-Teams) | Read→Execute→Reflect→Write 闭环——失败是训练信号 |
| **怎么改** | 5步自我迭代法（@娇姐话AI圈） | 实用复盘框架——读日志→找模式→定根因→定措施→写规范 |

三篇研究的交集构成了 Memory Evolution 的核心：

```
MemSkill：      存技能，不存内容
Memento：       失败后自动反思，不是简单重试
自我迭代法：    把反思结果固化为可执行规则
```

### 为什么做成独立项目

最初这套体系深度绑定在我们的 OpenClaw 实例中（散布在 AGENTS.md、MEMORY.md、memory-skills.json 等多个文件）。但当其他 OpenClaw 用户看到效果后，也想使用。

问题是：**没有标准化的安装方式，也没有脱离具体配置的通用框架。**

所以我们把它独立出来，做成一个可移植的 Skill 包——复制到任何 OpenClaw 实例即可使用。

---

## 🏗️ 核心架构

### 整体结构

```
┌──────────────────────────────────────────────┐
│              Memory Skill Bank                │
│           (memory-skills.json)                │
│                                              │
│  ┌─────────┐ ┌──────────┐ ┌──────────────┐  │
│  │ Skill 1 │ │ Skill 2  │ │   ...Skill N │  │
│  │trigger  │ │ trigger  │ │   trigger    │  │
│  │action   │ │ action   │ │   action     │  │
│  │focus    │ │ focus    │ │   focus      │  │
│  │reflect  │ │ reflect  │ │   reflect    │  │
│  └─────────┘ └──────────┘ └──────────────┘  │
└──────────────┬───────────────────────────────┘
               │
    ┌──────────┴──────────────┐
    │                         │
    ▼                         ▼
┌─────────┐           ┌───────────┐
│ Reflect │           │  Designer  │
│  Loop   │           │ (进化引擎) │
│(每次任务)│           │(fail≥3触发)│
└────┬────┘           └─────┬─────┘
     │                       │
     ▼                       ▼
┌──────────────────────────────────────┐
│              输出目标                 │
│                                      │
│  iteration-rules.md  固化规则库      │
│  reflect_log         归因记录        │
│  MEMORY.md           长期记忆        │
└──────────────────────────────────────┘
```

### 四大核心机制

#### 1️⃣ 元记忆技能库（MemSkill）

**核心理念**：不存记忆内容，存"记忆技能"。

传统方式：
```
记忆：ClawTeam 安装在 ~/tools/ClawTeam-OpenClaw/
记忆：代理冲突需要 unset http_proxy
记忆：飞书文档要先 write 再 upload
...（越来越多，越来越杂）
```

元记忆方式：
```json
{
  "id": "tool-install",
  "trigger": "安装新工具/插件",
  "action": "安全评估→虚拟环境→安装→验证→更新记录",
  "memory_focus": "只记：工具名、版本、路径、已知问题。不记：安装步骤"
}
```

**效果**：从"记住每件事"变成"知道该记什么"。记忆体积减少 60%+，检索效率提升。

#### 2️⃣ 自动反思循环（Memento）

**核心理念**：失败不是重试的理由，而是进化的训练信号。

```
每次任务完成后（不需要用户触发）：

  ROUTE    → 匹配对应的 Skill
  EXECUTE  → 按 Skill 的 action 执行
  REFLECT  → 用 reflect_checks 自检
  ATTRIBUTE → 失败时归因到具体环节
  WRITE    → 更新 success_count / fail_count
  EVOLVE   → fail_count≥3 时自动触发优化
```

每个 Skill 都有专属的自检问题：

```json
"reflect_checks": [
  "根因是否准确？",
  "解决方案是否彻底？",
  "是否需要更新规则库？"
]
```

**效果**：从"被动等用户说不满"变成"主动发现并修复问题"。

#### 3️⃣ 数据驱动进化（Designer）

**核心理念**：用数据决定何时进化，而不是凭感觉。

```json
{
  "success_count": 12,
  "fail_count": 3,    // ← 触发阈值
  "last_reflect": "2026-03-31T09:15:00"
}
```

当某个 Skill 的 `fail_count ≥ 3` 时，自动触发 Designer 流程：
1. 分析失败案例的模式
2. 定位根因（能力/态度/流程）
3. 优化 Skill 的 action 或 memory_focus
4. 写回 Skill Bank

**效果**：Skill 越用越精准，而非越用越臃肿。

#### 4️⃣ 自我迭代规范（5步法）

**核心理念**：深度复盘需要结构化流程，不是随便想想。

触发条件：同类错误 ≥ 2 次 / 用户不满 / 任务严重偏差

```
Step 1 — 读日志：❌ 标出错节点，✅ 标出好节点
Step 2 — 找模式：不孤立看单次，找反复出现的问题
Step 3 — 定根因：能力问题？态度问题？流程问题？
Step 4 — 定措施：具体、可验证、可执行（禁止"下次注意"）
Step 5 — 写规范：固化到 iteration-rules.md
```

**效果**：经验不流失，每次迭代都在前一次基础上累积。

---

## 📦 内置技能（默认 8 个）

| ID | 名称 | 触发场景 | 优先级 |
|----|------|---------|--------|
| `error-debug` | 技术调试 | 工具调用失败、命令报错 | 🔴 高 |
| `tool-install` | 工具安装 | 安装新工具/插件/Skill | 🔴 高 |
| `self-evolve` | 自我进化 | 同类错误≥2次、用户不满 | 🔴 高 |
| `deep-research` | 深度研究 | 深入分析项目或话题 | 🟡 中 |
| `doc-creation` | 文档创作 | 保存/写文档/发飞书 | 🟡 中 |
| `code-dev` | 代码开发 | 写代码/修bug/重构 | 🟡 中 |
| `learning-extract` | 学习提取 | 阅读后沉淀知识 | 🟡 中 |
| `daily-ops` | 日常运维 | 检查系统/定时任务/备份 | 🟢 低 |

每个技能都可以根据你的使用场景自由增删改。

---

## 🚀 安装与使用

### 前置条件

- [OpenClaw](https://github.com/openclaw/openclaw) 已安装并运行
- 基本熟悉 OpenClaw 的 workspace 目录结构

### 方式一：一键安装（推荐）

```bash
# 1. 克隆到 skills 目录
cd ~/.openclaw/workspace/skills
git clone https://github.com/xiepengpeng/memory-evolution.git

# 2. 运行初始化脚本
cd memory-evolution
bash scripts/init-memory-skill.sh

# 3. 重启 OpenClaw 使 skill 生效
openclaw gateway restart
```

初始化脚本会自动：
- ✅ 创建 `memory/` 目录
- ✅ 复制 `memory-skills.json`（如果不存在）
- ✅ 复制 `iteration-rules.md`（如果不存在）
- ✅ 追加反思循环到 `AGENTS.md`（不覆盖已有内容）

### 方式二：手动安装

```bash
# 1. 克隆
git clone https://github.com/xiepengpeng/memory-evolution.git
cd memory-evolution

# 2. 复制模板文件
mkdir -p ~/.openclaw/workspace/memory
cp templates/memory-skills.json ~/.openclaw/workspace/memory/
cp templates/iteration-rules.md ~/.openclaw/workspace/memory/

# 3. 将 templates/agents-additions.md 的内容合并到你的 AGENTS.md
cat templates/agents-additions.md >> ~/.openclaw/workspace/AGENTS.md

# 4. 重启
openclaw gateway restart
```

### 验证安装

```bash
# 检查文件是否就位
ls ~/.openclaw/workspace/memory/memory-skills.json
ls ~/.openclaw/workspace/memory/iteration-rules.md
ls ~/.openclaw/workspace/skills/memory-evolution/SKILL.md
```

---

## 🎯 使用方式

### 自动模式（推荐）

安装后无需任何操作。Agent 会在每次任务完成后自动执行反思循环：

```
你：帮我研究 Memento-Skills 这个项目
Agent：[执行研究任务]
       [任务完成 → 自动 REFLECT]
       [匹配 skill: deep-research]
       [自检：是否找到≥3个来源？核心洞察到位？]
       [更新 success_count]
```

你不会感知到反思循环的存在——它在后台静默运行。

### 手动触发深度复盘

当需要深度复盘时，对 Agent 说：

```
"自我迭代" / "复盘" / "反思"
```

Agent 会执行完整的 5 步迭代流程，并更新规则库。

### 查看进化数据

```bash
# 查看技能成功率
cat ~/.openclaw/workspace/memory/memory-skills.json | python3 -c "
import json, sys
data = json.load(sys.stdin)
for s in data['skills']:
    total = s['success_count'] + s['fail_count']
    rate = f\"{s['success_count']/total*100:.0f}%\" if total else 'N/A'
    print(f\"{s['id']:20s} ✅{s['success_count']:3d} ❌{s['fail_count']:3d} ({rate})\")
"

# 查看固化规则
cat ~/.openclaw/workspace/memory/iteration-rules.md

# 查看归因记录
cat ~/.openclaw/workspace/memory/memory-skills.json | python3 -c "
import json, sys
data = json.load(sys.stdin)
for entry in data.get('reflect_log', []):
    print(f\"{entry['date']} | {entry['skill_id']} | {entry['outcome']}\")
    print(f\"  归因: {entry['attribution']}\")
"
```

---

## 🔧 自定义

### 替换技能（适配不同角色）

默认 8 个技能面向**技术型 AI 助手**。编辑 `memory/memory-skills.json` 按需替换：

**写作助手**：
```json
{"id": "drafting", "trigger": "用户要求写文章", "action": "..."}
{"id": "editing", "trigger": "修改润色现有文本", "action": "..."}
{"id": "publishing", "trigger": "发布到平台", "action": "..."}
```

**项目管理**：
```json
{"id": "planning", "trigger": "制定计划", "action": "..."}
{"id": "tracking", "trigger": "跟踪进度", "action": "..."}
{"id": "reporting", "trigger": "生成报告", "action": "..."}
```

### 调整进化阈值

默认 `fail_count ≥ 3` 触发优化。在 `agents-additions.md` 中修改这个数字：
- 更激进：设为 2（快速迭代，但可能过度优化）
- 更保守：设为 5（稳定优先，但问题修复慢）

---

## 📊 效果对比

基于我们 2 周的实际使用：

| 指标 | 使用前 | 使用后 |
|------|--------|--------|
| MEMORY.md 行数 | 967 行（失控） | ~400 行（稳定） |
| 同类错误重复率 | ~40% | <10% |
| 记忆有用率 | ~30%（大量冗余） | ~80%（精简聚焦） |
| 进化触发方式 | 仅用户手动 | 自动 + 手动双重 |

---

## 📁 项目结构

```
memory-evolution/
├── README.md                        ← 你正在读的文件
├── SKILL.md                         ← OpenClaw Skill 定义文件
├── LICENSE                          ← MIT 协议
├── templates/
│   ├── memory-skills.json           ← 元记忆技能库模板（8个技能）
│   ├── iteration-rules.md           ← 固化规则库模板
│   └── agents-additions.md          ← 需追加到 AGENTS.md 的内容
└── scripts/
    └── init-memory-skill.sh         ← 一键初始化脚本
```

---

## 🧪 技术细节

### 反思循环的数据结构

```json
{
  "reflect_log": [
    {
      "date": "2026-03-31",
      "skill_id": "doc-creation",
      "outcome": "partial",
      "attribution": "飞书上传步骤遗漏了内容验证环节",
      "action_taken": "在 action 中增加'验证内容质量'步骤",
      "evolved": true
    }
  ]
}
```

### 五层记忆系统分工

安装 Memory Evolution 后，Agent 的记忆系统分为五层：

| 层级 | 工具 | 职责 | 生命周期 |
|------|------|------|---------|
| 1 | iteration-rules.md | 固化规则（A/B/C三类） | 永久 |
| 2 | memory-skills.json | 元记忆技能库 | 进化型 |
| 3 | MEMORY.md | 精选长期记忆 | 定期精简 |
| 4 | memory/YYYY-MM-DD.md | 每日原始日志 | 30天归档 |
| 5 | MemOS Local | 自动记忆捕获 | 自动管理 |

---

## 🤝 贡献

欢迎贡献！以下方式都可以：

- 🐛 提 Issue 报告问题
- 💡 提 Issue 分享你的使用场景
- 🔀 提交 PR 优化技能或添加新技能
- 📝 分享你的自定义技能库配置

### 贡献新技能

在 `templates/memory-skills.json` 中添加技能后提 PR：

```json
{
  "id": "your-skill-id",
  "name": "技能名称",
  "trigger": "触发条件",
  "action": "执行步骤",
  "memory_focus": "只记什么，不记什么",
  "reflect_checks": ["自检问题1", "自检问题2", "自检问题3"],
  "priority": "high|medium|low",
  "success_count": 0,
  "fail_count": 0,
  "last_reflect": null
}
```

---

## 📚 致谢与参考

| 来源 | 贡献 |
|------|------|
| [MemSkill](https://arxiv.org/abs/2602.02474) (arXiv:2602.02474) | 元记忆范式，技能条件化的记忆构建 |
| [Memento-Skills](https://arxiv.org/abs/2603.18743) (arXiv:2603.18743) | Read→Execute→Reflect→Write 反思闭环 |
| @娇姐话AI圈 | 5步自我迭代法 |
| [OpenClaw](https://github.com/openclaw/openclaw) | 开源 AI Agent 平台 |

---

## 📄 License

MIT License — 自由使用、修改、分发。

---

> **Memory Evolution** — 不是记住更多，而是记住更准。🧠
