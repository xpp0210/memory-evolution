# 🧠 Memory Evolution v4.0 — AI Agent 记忆进化体系

> 让任何 OpenClaw 实例从"被动记忆"进化为"主动学习、自我进化"
> 融合 10+ 开源项目精华 + 实战经验打磨

## 这是什么

一套**可移植的 AI Agent 记忆进化体系**。不是简单的记忆存储，而是一个完整的**反思→归因→学习→进化**循环，让 Agent 越用越聪明。

## 产生原因

大多数 AI Agent 的记忆系统只做"存取"——写进去，需要时读出来。但真正的学习需要：

- **反思失败**：不只是记录失败，而是归因到具体步骤
- **提取模式**：成功时提炼可复用的经验
- **淘汰过期规则**：不用的规则会腐烂，需要自动清理
- **巩固有效知识**：反复验证的知识应该被强化
- **夜间整合**：白天积累的碎片需要整合为结构化知识

v4.0 融合了 10+ 个前沿项目的核心思想，构建了一套完整的进化体系。

## 融合项目

| 项目 | 核心贡献 |
|------|----------|
| **MemSkill** | 元记忆技能库，学会"怎么记" |
| **Memento** | 记忆架构分层设计 |
| **AgentEvolver** | ADCA 步骤级归因，失败时精确定位问题 |
| **OpenSpace** | FIX/DERIVED/CAPTURED 三类技能自动捕获 |
| **Membrane** | Ebbinghaus 记忆衰减与巩固机制 |
| **Capy Cortex** | 知识坏味道检测，保持知识库健康 |
| **Hermes GEPA** | Skill 自动进化，基于反馈迭代改进 |
| **AnimaWorks** | Self-Questioning 自动生成测试场景 |
| **Engram-AI** | 记忆检索优化 |
| **self-evolve** | 能力图谱 level/evidence/limits 跟踪 |
| **claude-total-memory** | 规则淘汰 success_rate<20% 自动暂停 |

## 核心特性

### 🔄 反思循环：ROUTE → EXECUTE → REFLECT → ATTRIBUTE → WRITE → EVOLVE

完整六阶段循环，不是简单的"执行+记录"：

1. **ROUTE** — 判断任务属于哪个 skill
2. **EXECUTE** — 按 skill 的 action 执行
3. **REFLECT** — 用 reflect_checks 自检
4. **ATTRIBUTE** — 失败时做步骤级归因（failure_step → root_cause → fix_suggestion）
5. **WRITE** — 成功/失败计数，创建归因记录
6. **EVOLVE** — 触发技能进化或规则更新

### 🔍 Triple Fusion 检索

三层检索策略，确保召回率和准确率：
- **语义检索**：embedding 相似度
- **关键词检索**：精确匹配
- **时间衰减**：近期记忆权重更高

### 📊 能力图谱

每个能力跟踪三个维度：
- **level**：beginner / intermediate / advanced / expert
- **evidence**：支撑该等级的证据列表
- **limits**：已知边界和不足

### 🎯 学习议程

同时只维护 1-3 个高杠杆学习目标，聚焦而非分散。

### 🧹 知识健康

- **知识坏味道检测**：发现过时、矛盾、冗余的知识
- **规则淘汰**：success_rate < 20% 自动暂停，避免僵尸规则
- **记忆衰减与巩固**：基于 Ebbinghaus 遗忘曲线，反复成功的知识被巩固，不用的自然衰减

### 💡 偏好候选池

静默学习用户习惯，不主动打扰。当检测到明确偏好信号时自动记录候选。

### 🌙 夜间整合（autoDream 四阶段）

```
阶段1: 扫描 → 收集当天新增记忆碎片
阶段2: 归类 → 按主题/项目聚类
阶段3: 提炼 → 提取可复用模式和规则候选
阶段4: 写入 → 更新知识库、淘汰过期规则
```

### 🛠 技能捕获

三类自动捕获机制：
- **FIX** — 修复 bug 时捕获为技能
- **DERIVED** — 从成功任务中推导新技能
- **CAPTURED** — 显式标记值得保存的操作模式

## 文件结构

```
memory-evolution/
├── SKILL.md              # 核心技能定义（v4.0, 294行）
├── README.md             # 本文件
├── scripts/
│   ├── reflect.sh        # 反思循环脚本
│   ├── skill-capture.sh  # 技能捕获脚本
│   ├── skill-discover.py # 技能发现
│   ├── skill-feedback.py # 技能反馈收集
│   ├── skill-proposal.py # 失败驱动提案生成（EvoSkill式）
│   ├── skill-pareto.py   # Pareto多目标选择（成功率×活跃度×迁移性）
│   ├── skill-verify.py   # SKILL.md结构评分
│   ├── skill-freq-analyzer.py  # Token预算分析（SKILL0式）
│   ├── diminishing-detector.py  # 递减检测（P2自适应阈值）
│   └── meta-learn.py     # 元学习引擎
├── templates/
│   └── capability-map.json  # 能力图谱模板
└── LICENSE
```

## 快速开始

1. 将 `memory-evolution/` 放入 OpenClaw 的 skills 目录
2. 确保 `scripts/` 下的脚本有执行权限：`chmod +x scripts/*.sh scripts/*.py`
3. OpenClaw 会自动加载 SKILL.md，开始使用反思循环

## 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| v4.0 | 2026-04-02 | 融合10+项目，完整进化体系 |
| v1.0 | 2026-03 | 初始版本，基于3篇论文 |

## License

MIT
