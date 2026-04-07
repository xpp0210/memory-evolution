---
name: memory-evolution
description: AI Agent 记忆进化体系 v5.5。Pareto多目标选择+失败提案生成+递减自适应+P2阈值。。MemOS深度集成 + LLM驱动智能决策 + Hook实时监控 + 多Agent协作 + 自适应学习。
---

# Memory Evolution Skill v5.5
## 触发条件
当用户提到「memory evolution」相关任务时使用此Skill。


> MemOS 深度集成的下一代记忆进化体系
> 版本：5.5.0 | 更新：2026-04-07

## 这是什么

一套**MemOS 集成的 AI Agent 记忆进化体系**，让 OpenClaw 实例具备：

1. **MemOS 深度集成** — 双向同步、混合检索
2. **LLM 驱动的智能决策** — 替代规则引擎
3. **Hook 驱动的实时监控** — 任务完成/失败立即触发
4. **多 Agent 协作进化** — 团队能力共享与冲突解决
5. **自适应学习策略** — A/B 测试与动态参数调整

**v5.0 核心特性：**
- MemOS 作为底层数据源（memory_search + chunk storage）
- memory-evolution 作为上层进化引擎（reflect → capture → evolve）
- 双向同步：`memos-local/skills-store/` ↔ `memory/skill-bank/`
- Hook 集成：5 个实时监控点
- LLM 判断：替代固定规则，更智能的归因和技能进化

---

## v5.0 核心架构

```
任务 → MemOS capture → Hook触发 → LLM决策 → 进化执行
                                    ↓
                        MemOS hybrid search ← ← ← ←
```

---

## 反思循环：ROUTE → EXECUTE → REFLECT → ATTRIBUTE → WRITE → EVOLVE

### ROUTE（路由）
判断任务属于哪个 skill（v4.0 保留）

### EXECUTE（执行）
按 skill 的 action 执行（v4.0 保留）

### REFLECT（反思）
用 reflect_checks 自检（v4.0 保留）

### ATTRIBUTE（归因）
失败时做步骤级归因（v4.0 保留）

### WRITE（记录）
成功→success_count++ / 失败→fail_count++ + 创建归因记录（v4.0 保留）

**偏好检测保持不变**（与 MemOS 的 `auto_recall` 配合工作）：
- 格式：`- 🟢 [日期] 观察：[偏好内容] | 来源：[对话主题]`
- 写入命令示例（嵌入reflect.sh record流程）：
```bash
# 在 reflect.sh record 成功后追加偏好
echo "- 🟢 [$(date +%Y-%m-%d)] 观察：${PREFERENCE_TEXT} | 来源：${TOPIC}" >> memory/preference-candidates.md
```

---

## MemOS 同步层（v5.0 新增）

### 双向同步
`python3 scripts/memos-integration.py sync` — 同步 skill-bank 和 MemOS skills-store

**同步逻辑：**
1. 读取 `memory/skill-bank/skill-bank.json`
2. 读取 `memos-local/skills-store/`（MemOS 生成的 skills）
3. 双向合并冲突
4. 写回两个位置

**v5.0 特性：**
- MemOS 作为单一真实数据源
- memory-evolution 提供进化策略
- 避免重复和不一致

---

## Hook 实时触发（v5.0 新增）

### Hook 列表

| Hook | 触发条件 | 动作 | 状态 |
|------|----------|------|------|
| `session:compact:after` | 会话压缩率 > 40% | 立即蒸馏知识 | 🔜 开发中 |
| `task:completed` | 任务完成 | 立即评估是否生成 skill | 🔜 开发中 |
| `task:failed` | 任务失败 | 立即 LLM 归因 | 🔜 开发中 |
| `message:preprocessed` | 消息包含学习信号 | 写入 learn-queue/ | 🔜 开发中 |
| `agent:bootstrap` | Agent 引导 | 热身用户画像 | 🔜 开发中 |

**Hook 位置：** `~/.openclaw/hooks/evolve-monitor/`

---

## v5.0 脚本参考

### MemOS 集成（新增）
```bash
python3 scripts/memos-integration.py search "关键词"     # 从 MemOS 搜索记忆
python3 scripts/memos-integration.py sync              # 双向同步 skill-bank
python3 scripts/memos-integration.py push-skill <id>   # 推送 skill 到 MemOS
```

**技术细节：**
- FTS5 关键词搜索
- 向量语义搜索（简化版，v5.0-beta 中接入真实 embedding）
- RRF 融合（Reciprocal Rank Fusion）
- 双向技能库同步

### v4.0 保留脚本（向后兼容）

```bash
# v4.0 保留（向后兼容）
reflect.sh status                           # 状态+归因统计
reflect.sh record <id> <result> [note]      # 记录
reflect.sh analyze <id>                     # 查看待归因
reflect.sh resolve <id> <cause> <fix>       # 标记归因
reflect.sh evolve                           # 进化建议
reflect.sh test <id>                        # Self-Questioning 测试
```

**逐步淘汰计划：**
- `triple-fusion.py` → 逐步淘汰（MemOS hybrid search 已覆盖）
- `skill-evolve.py` → 升级为 LLM 驱动（v5.0-beta）
- `night-consolidate.py` → 升级为 LLM 蒸馏（v5.0-beta）
- `session-priming.py` → 逐步淘汰（Hook 实时监控已覆盖）
- `skill-discover.py` → 升级为 MemOS 集成（v5.0-beta）

---

## v5.0 核心文件

### 新增
| 文件 | 用途 |
|------|------|
| `scripts/memos-integration.py` | MemOS 集成（search/sync/push-skill） |
| `docs/v5.0-planning.md` | v5.0 完整规划文档 |
| `hooks/evolve-monitor/` | Hook 集合（5个实时监控Hook） |
| `memory/memos-sync-log.json` | MemOS 同步日志（新增） |

### v4.0 保留（逐步淘汰中）
| 文件 | 用途 |
|------|------|
| `scripts/reflect.sh` | 反思循环（向后兼容） |
| `scripts/skill-capture.sh` | OpenSpace 三模式捕获 |
| `scripts/skill-capture-scan.py` | 模式扫描 |
| `scripts/skill-evolve.py` | GEPA Skill自动进化（逐步升级为 LLM） |
| `scripts/night-consolidate.py` | 夜间整合（逐步升级为 LLM） |
| `scripts/skill-discover.py` | 工具自动发现（逐步升级为 MemOS 集成） |
| `scripts/skill-feedback.py` | Skills自反馈（逐步淘汰） |
| `scripts/meta-learn.py` | 元学习实验（逐步升级为自适应） |
| `scripts/rule-prune.sh` | 规则淘汰 |
| `memory/memory-skills.json` | 技能库 + 反思日志 |
| `memory/capability-map.json` | 能力图谱 |
| `memory/learning-agenda.md` | 学习议程 |
| `memory/iteration-rules.md` | 规则库 |
| `memory/experience-patterns.md` | 经验模式库 |
| `memory/preference-candidates.md` | 偏好候选池 |
| `memory/integration-self-evolve.md` | self-evolve插件集成方案 |
| `memory/skill-captures/` | 捕获记录目录 |
| `memory/knowledge/` | 蒸馏后知识 |

---

## 来源

| 来源 | 贡献 |
|------|------|
| MemOS (memos-local-openclaw-plugin) | 底层数据源 + Hybrid Search + Memory Viewer |
| MemSkill (arXiv:2602.02474) | 元记忆范式 |
| Memento-Skills (arXiv:2603.18743) | 反思闭环 |
| AgentEvolver (ModelScope/阿里) | ADCA归因 + Self-Questioning |
| OpenSpace (HKUDS) | FIX/DERIVED/CAPTURED |
| self-evolving-agent (RangeKing) | 能力图谱 + 学习议程 |
| claude-total-memory | 规则淘汰 + Spaced Repetition |
| Membrane | 记忆衰减巩固 |
| 奥一 AoYi (@Aoyi21) | 偏好候选池 + 知识坏味道 |
| Hermes Agent (NousResearch) | 持续微进化 + GEPA Skill进化 |
| Capy Cortex | Triple Fusion检索 + 反模式阻断 |
| AnimaWorks | 夜间整合 + 六通道Priming + 三阶段遗忘 |
| Engram-AI | Ebbinghaus指数衰减 |
| self-evolve (longmans) | Q-Learning门控 + 混合排序 |

---

## 🔄 实战经验（自动注入）

> 最近更新：2026-04-04（v5.0-alpha 开发中）

| 模式 | 触发条件 |
|------|----------|
| bash中文问题用独立python脚本 | heredoc/变量展开中文乱码 |
| 大段修改用write重写不用edit拼接 | 文件修改 |
| MemOS 数据库查询错误 | 修复列名匹配（v5.0-alpha） |

---

## v5.0 里程碑

- [x] v5.0-alpha (2026-04-04) - MemOS 集成脚本 + 规划文档
- [ ] v5.0-beta (2026-04-15) - Hook 实时监控实现
- [ ] v5.0-rc (2026-05-01) - LLM 驱动升级完成
- [ ] v5.0-stable (2026-06-01) - 多 Agent 协作完成

**当前分支：** `feature/v5.0-planning`
**GitHub：** https://github.com/xpp0210/memory-evolution/tree/feature/v5.0-planning

---

## 快速开始

### 1. Memory Viewer

可视化记忆、任务和技能的全功能 Web 界面。

**访问地址：** http://127.0.0.1:18799

**功能页面：**
| 页面 | 功能 |
|------|------|
| Memories | 查看所有记忆 chunks，支持搜索、编辑、删除 |
| Tasks | 浏览任务状态、结构化总结、生成技能 |
| Skills | 浏览技能库、版本历史、质量评分 |
| Analytics | 每日读写活动、记忆分类图表 |
| Logs | 工具调用日志（memory_search、auto_recall等）|
| Import | 从旧版 OpenClaw 记忆迁移到 MemOS |
| Settings | 配置 embedding、summarizer、skill evolution 参数 |

> ⚠️ Viewer 仅在 OpenClaw Gateway 运行时可用。如无法访问，检查 `openclaw status`。

### 2. MemOS 搜索

```bash
# 从 MemOS 搜索记忆（Hybrid Search: FTS5 + Vector）
cd ~/.openclaw/workspace/skills/memory-evolution
python3 scripts/memos-integration.py search "关键词"

# 双向同步技能库
python3 scripts/memos-integration.py sync

# 推送技能到 MemOS
python3 scripts/memos-integration.py push-skill error-debug
```

### 3. 测试 Embedding

```bash
# 运行测试脚本（验证 embedding API + 向量搜索）
bash ~/.openclaw/workspace/skills/memory-evolution/scripts/test-embedding.sh
```

## v5.5 更新（2026-04-07）

### 新增脚本
| 脚本 | 功能 |
|------|------|
| skill-pareto.py | Pareto多目标选择（成功率×活跃度×迁移性×独特性）|
| skill-proposal.py | 失败驱动提案生成（EvoSkill式Proposer）|
| skill-verify.py | SKILL.md结构评分（74skills质量分析）|
| skill-freq-analyzer.py | Token预算分析（SKILL0渐进撤除思路）|
| diminishing-detector.py | P2自适应阈值（高频≥10→0.50，中频3-9→0.40，低频≤2→0.30）|

### 新增功能
- Pareto前沿选择替代单目标排序
- 7个失败提案自动生成
- 64个skills补触发条件章节（75→85分）
- reflect: 21✅ 0❌ 里程碑
