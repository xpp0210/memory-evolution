---
name: memory-evolution
description: AI Agent 记忆进化体系 v4.0。融合10+项目精华。支持 ROUTE→REFLECT→WRITE 循环、Triple Fusion检索、GEPA Skill自动进化、夜间整合、六通道Priming、Ebbinghaus衰减、能力图谱、规则淘汰。
---

# Memory Evolution Skill v4.0

> 融合10+项目：MemSkill + Memento + AgentEvolver + OpenSpace + Membrane + Capy Cortex + Hermes GEPA + AnimaWorks + Engram-AI + self-evolve
> 版本：4.0.0 | 2026-04-02

## 这是什么

一套**可移植的 AI Agent 记忆进化体系**，让 OpenClaw 实例具备：

1. **元记忆技能库** — 学会"怎么记"
2. **ADCA归因循环** — 步骤级失败归因（AgentEvolver）
3. **Self-Questioning** — 自动生成测试场景
4. **经验模式提取** — 成功里程碑时提取可复用模式
5. **FIX/DERIVED/CAPTURED** — 自动技能捕获（OpenSpace）
6. **偏好候选池** — 静默学习用户习惯
7. **知识坏味道检测** — 发现知识库健康问题
8. **能力图谱** — 跟踪每个能力的level/evidence/limits（self-evolving-agent）
9. **学习议程** — 同时只维护1-3个高杠杆学习目标
10. **规则淘汰** — success_rate<20%自动暂停（claude-total-memory）
11. **记忆衰减与巩固** — 反复成功的知识巩固，不用的自然衰减（Membrane）

## 反思循环：ROUTE → EXECUTE → REFLECT → ATTRIBUTE → WRITE → EVOLVE

### ROUTE（路由）
判断任务属于哪个 skill

### EXECUTE（执行）
按 skill 的 action 执行

### REFLECT（反思）
用 reflect_checks 自检

### ATTRIBUTE（归因）
失败时做步骤级归因：failure_step → root_cause → fix_suggestion → rule_candidate

### WRITE（记录）
成功→success_count++ / 失败→fail_count++ + 创建归因记录

**偏好检测**：在WRITE阶段同时检查用户原始输入，若包含明确偏好信号（"我喜欢"、"以后都这样"、"别用XX用YY"、"默认用"、"记住我偏好"等），自动追加到 `memory/preference-candidates.md`：
- 格式：`- 🟢 [日期] 观察：[偏好内容] | 来源：[对话主题]`
- 写入命令示例（嵌入reflect.sh record流程）：
```bash
# 在 reflect.sh record 成功后追加偏好
echo "- 🟢 [$(date +%Y-%m-%d)] 观察：${PREFERENCE_TEXT} | 来源：${TOPIC}" >> memory/preference-candidates.md
```

### EVOLVE（进化）
- 失败驱动：fail_count≥3 且归因已分析 → 强制进化
- 成功驱动：success_count 达 5/10/20/50 → 提取经验模式
- **v3新增**：完成后对比 capability-map.json，识别最弱能力，更新 learning-agenda.md

## 能力图谱 ⭐ v3

文件：`memory/capability-map.json`

每个能力跟踪：level(1-5) / evidence / limits / failure_modes / success_count / fail_count / last_used

level定义：
- 1：能用但常出错
- 2：基本可靠，偶有问题
- 3：稳定可靠，已知边界
- 4：高水平，能教别人
- 5：专家级，能自动进化

## 学习议程 ⭐ v3

文件：`memory/learning-agenda.md`

同时只维护1-3个高杠杆学习目标。每个目标包含：
- 为什么（为什么重要）
- 怎么做（具体提升路径）
- 通过标准（怎样算学会）
- 状态（进行中/完成/搁置）

任务完成后自动对比 capability-map，识别最弱能力。

## 规则淘汰机制 ⭐ v3

文件：`memory/iteration-rules.md`（v2格式）

每条规则跟踪：apply_count / success_count / 状态
- success_rate = success / apply
- success_rate < 20% 且 apply >= 10 → ⛔ suspended
- 心跳时扫描，suspended 规则移至"已暂停"区
- 被暂停规则可在下次触发时重新激活

## 记忆衰减与巩固 ⭐ v3

文件：`memory/experience-patterns.md`

每个模式跟踪：apply / success / last_used / 权重
- 🟢高：14天内使用
- 🟡中：14-30天未用，检索降权
- 🔴低：30天以上未用，考虑归档
- ⛔归档：60天以上未用，移至archive

**Skill Fingerprinting**：新模式入库前检查与现有模式相似度，>0.85阈值时合并。

## OpenSpace 三模式自动技能捕获

### FIX — 修复失败技能
```bash
skill-capture.sh fix <skill_id> "错误描述"
```

### DERIVED — 从重复模式派生新技能
```bash
skill-capture.sh derived "任务模式" 频次
```

### CAPTURED — 从成功任务捕获技能
```bash
skill-capture.sh captured "任务描述" [步骤文件]
```

### 自动扫描
```bash
python3 scripts/skill-capture-scan.py
```

## reflect.sh v3 命令参考

```bash
reflect.sh status                           # 状态+归因统计
reflect.sh record <id> <result> [note]      # 记录
reflect.sh analyze <id>                     # 查看待归因
reflect.sh resolve <id> <cause> <fix>       # 标记归因
reflect.sh evolve                           # 进化建议
reflect.sh test <id>                        # Self-Questioning 测试
```

## Triple Fusion 检索 ⭐ v4.0

> 借鉴 Capy Cortex：三路融合检索替代单一搜索

```bash
python3 scripts/triple-fusion.py search "关键词"     # 三路融合搜索
python3 scripts/triple-fusion.py index               # 重建索引
python3 scripts/triple-fusion.py status              # 索引状态
```

三路：FTS5全文 + TF-IDF向量 + 实体图 → Reciprocal Rank Fusion合并

## GEPA Skill自动进化 ⭐ v4.0

> 借鉴 Hermes Agent + DSPy：自动变异和优化SKILL.md

```bash
python3 scripts/skill-evolve.py evolve <skill_id>    # 进化一个skill
python3 scripts/skill-evolve.py batch                 # 批量进化top5高频skill
python3 scripts/skill-evolve.py review <skill_id>     # 查看候选版本
python3 scripts/skill-evolve.py apply <skill_id>      # 应用候选版本
```

4种变异：rephrase / add_example / add_boundary / restructure
约束门控：大小≤120% + 语义保持(60%标题重叠)

## 夜间整合 ⭐ v4.0

> 借鉴 AnimaWorks：白天episodic→夜间蒸馏成knowledge

```bash
python3 scripts/night-consolidate.py run              # 执行整合
python3 scripts/night-consolidate.py report           # 查看报告
```

三阶段遗忘：>30天标记陈旧 → >45天合并相似 → >60天归档

## 六通道 Priming ⭐ v4.0

> 借鉴 AnimaWorks：会话开始时6维度并行搜索

```bash
python3 scripts/session-priming.py                    # 执行priming
```

6通道：用户Profile / 最近活动 / 记忆Skills / 活跃Skills / 待办 / 偏好

## Ebbinghaus 指数衰减 ⭐ v4.0

> 借鉴 Engram-AI：指数衰减替代线性衰减

```
strength = e^(-t/S)
S = 7.0 × (1 + 成功召回次数)
strength < 0.3 → 🔴降权, < 0.05 → 归档
```

## 反模式阻断 ⭐ v4.0

> 借鉴 Capy Cortex：执行前拦截已知危险命令

9种危险模式：rm -rf /, git push --force, DROP TABLE, chmod 777 等

## 核心文件

| 文件 | 用途 |
|------|------|
| `scripts/reflect.sh` | 反思循环 (v3, 含反模式阻断+Ebbinghaus衰减) |
| `scripts/skill-capture.sh` | OpenSpace 三模式捕获 + DIS/IMP/SCO评分 |
| `scripts/skill-capture-scan.py` | 模式扫描（含 --auto-apply） |
| `scripts/triple-fusion.py` | Triple Fusion检索引擎 ⭐v4 |
| `scripts/skill-evolve.py` | GEPA Skill自动进化 ⭐v4 |
| `scripts/night-consolidate.py` | 夜间整合+三阶段遗忘 ⭐v4 |
| `scripts/session-priming.py` | 六通道Priming ⭐v4 |
| `scripts/skill-discover.py` | 工具自动发现 |
| `scripts/skill-feedback.py` | Skills自反馈 |
| `scripts/meta-learn.py` | 元学习实验 + Q-Learning门控 |
| `scripts/rule-prune.sh` | 规则淘汰 |
| `memory/memory-skills.json` | 技能库 + 反思日志 |
| `memory/capability-map.json` | 能力图谱 |
| `memory/learning-agenda.md` | 学习议程 |
| `memory/iteration-rules.md` | 规则库(v2格式+淘汰) |
| `memory/experience-patterns.md` | 经验模式库(含Ebbinghaus衰减) |
| `memory/preference-candidates.md` | 偏好候选池 |
| `memory/integration-self-evolve.md` | self-evolve插件集成方案 |
| `memory/skill-captures/` | 捕获记录目录 |
| `memory/knowledge/` | 蒸馏后知识 ⭐v4 |
| `.evolved/` | Skill进化候选版本 ⭐v4 |

## 来源

| 来源 | 贡献 |
|------|------|
| MemSkill (arXiv:2602.02474) | 元记忆范式 |
| Memento-Skills (arXiv:2603.18743) | 反思闭环 |
| AgentEvolver (ModelScope/阿里) | ADCA归因 + Self-Questioning |
| OpenSpace (HKUDS) | FIX/DERIVED/CAPTURED |
| self-evolving-agent (RangeKing) | 能力图谱 + 学习议程 |
| claude-total-memory | 规则淘汰 + Spaced Repetition |
| Membrane | 记忆衰减巩固 |
| 奥一 AoYi (@Aoyi21) | 偏好候选池 + 知识坏味道 |
| Hermes Agent (NousResearch) | 持续微进化 + GEPA Skill进化 ⭐v4 |
| Capy Cortex | Triple Fusion检索 + 反模式阻断 ⭐v4 |
| AnimaWorks | 夜间整合 + 六通道Priming + 三阶段遗忘 ⭐v4 |
| Engram-AI | Ebbinghaus指数衰减 ⭐v4 |
| self-evolve (longmans) | Q-Learning门控 + 混合排序 |

## 🔄 实战经验（自动注入）

> 最近更新：2026-04-02

| 模式 | 触发条件 |
|------|----------|
| bash中文问题用独立python脚本 | heredoc/变量展开中文乱码 |
| 大段修改用write重写不用edit拼接 | 文件修改 |

## 工具自动发现 ⭐ v3.1

> 借鉴 Forage：遇到能力缺口→自动搜索→即时安装→学会使用

```bash
python3 scripts/skill-discover.py search "关键词"      # 搜索可用Skills
python3 scripts/skill-discover.py gap "任务描述"        # 推断能力缺口
python3 scripts/skill-discover.py status                # 查看统计
```

## Skills自反馈 ⭐ v3.1

> 借鉴 AutoSkill：将实战经验自动回注到SKILL.md，让Skills变成"活的"

```bash
python3 scripts/skill-feedback.py inject <skill_id>     # 注入经验到SKILL.md
python3 scripts/skill-feedback.py inject-all            # 批量注入
python3 scripts/skill-feedback.py status                # 查看统计
```

## 元学习实验 ⭐ v3.1

> 借鉴 ALMA：在现有系统上实验不同进化策略，自动发现最优方案

6种可实验策略：reflect-first / batch-reflect / capture-first / micro-skill / experience-weighted / failure-prediction

```bash
python3 scripts/meta-learn.py experiment <name> <strategy>  # 启动实验
python3 scripts/meta-learn.py evaluate <name> <result>      # 评估结果
python3 scripts/meta-learn.py best                           # 查看最优策略
python3 scripts/meta-learn.py history                        # 实验历史
```

### 新增文件

| 文件 | 用途 |
|------|------|
| `scripts/skill-discover.py` | 工具自动发现（Forage启发） |
| `scripts/skill-feedback.py` | Skills自反馈（AutoSkill启发） |
| `scripts/meta-learn.py` | 元学习实验（ALMA启发） |
| `memory/skill-discoveries.json` | 发现历史 |
| `memory/meta-experiments.json` | 实验历史 |
