#!/usr/bin/env python3
"""
meta-learn.py — 元学习实验层（ALMA启发）

在现有memory-evolution上增加"策略搜索"能力：
- 尝试不同的记忆/进化策略
- 评估哪种策略对我们更有效
- 自动切换到最优策略

不是重写记忆系统，而是在现有系统上增加一个"实验框架"，
让系统自己发现什么策略最适合当前任务。

用法：
  meta-learn.py experiment <name> <strategy>    启动一个策略实验
  meta-learn.py evaluate <name> <result>        评估实验结果
  meta-learn.py best                             查看当前最优策略
  meta-learn.py history                          实验历史
"""

import sys
import json
import os
from datetime import datetime, timedelta

BASE = os.path.expanduser("~/.openclaw/workspace")
EXPERIMENTS_FILE = os.path.join(BASE, "memory/meta-experiments.json")

# Available strategies to experiment with
STRATEGIES = {
    "reflect-first": {
        "name": "先反思再行动",
        "description": "任务完成后立即reflect.sh record，再执行下一步",
        "applies_to": "所有任务",
        "expected_benefit": "更及时的错误捕获"
    },
    "batch-reflect": {
        "name": "批量反思",
        "description": "积累5个任务后批量reflect.sh分析",
        "applies_to": "低风险任务",
        "expected_benefit": "减少反思开销，发现跨任务模式"
    },
    "capture-first": {
        "name": "先捕获再反思",
        "description": "复杂任务完成后先skill-capture captured，再reflect",
        "applies_to": "复杂多步骤任务",
        "expected_benefit": "捕获更完整的流程"
    },
    "micro-skill": {
        "name": "微技能拆分",
        "description": "将大skill拆成更小的微skill，每个<10行action",
        "applies_to": "高频使用的skill",
        "expected_benefit": "更精准的技能匹配和复用"
    },
    "experience-weighted": {
        "name": "经验加权检索",
        "description": "执行任务时优先参考高权重经验模式",
        "applies_to": "重复类型任务",
        "expected_benefit": "减少重复错误"
    },
    "failure-prediction": {
        "name": "失败预测",
        "description": "任务开始前检查failure_modes，主动规避",
        "applies_to": "capability-map中fail_count>0的技能",
        "expected_benefit": "预防性避坑"
    }
}


def load_experiments():
    if os.path.exists(EXPERIMENTS_FILE):
        with open(EXPERIMENTS_FILE) as f:
            return json.load(f)
    return {
        "experiments": [],
        "strategy_scores": {k: {"wins": 0, "losses": 0, "total": 0} for k in STRATEGIES},
        "active_strategy": None
    }


def save_experiments(data):
    with open(EXPERIMENTS_FILE, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def cmd_experiment(name, strategy_key):
    if strategy_key not in STRATEGIES:
        print(f"❌ 未知策略: {strategy_key}")
        print(f"可用策略: {', '.join(STRATEGIES.keys())}")
        return
    
    strategy = STRATEGIES[strategy_key]
    data = load_experiments()
    
    experiment = {
        "name": name,
        "strategy": strategy_key,
        "strategy_name": strategy["name"],
        "started": datetime.now().isoformat(),
        "status": "running",
        "applies_to": strategy["applies_to"],
        "expected_benefit": strategy["expected_benefit"],
        "tasks_completed": 0,
        "tasks_succeeded": 0,
        "result": None
    }
    
    data["experiments"].append(experiment)
    data["active_strategy"] = strategy_key
    save_experiments(data)
    
    print(f"🧪 实验启动: {name}")
    print(f"   策略: {strategy['name']}")
    print(f"   描述: {strategy['description']}")
    print(f"   预期收益: {strategy['expected_benefit']}")
    print(f"\n接下来执行3-5个任务后，运行:")
    print(f"   meta-learn.py evaluate {name} <success|fail>")


def cmd_evaluate(name, result):
    data = load_experiments()
    
    # Find experiment
    exp = None
    for e in reversed(data["experiments"]):
        if e["name"] == name:
            exp = e
            break
    
    if not exp:
        print(f"❌ 未找到实验: {name}")
        return
    
    exp["status"] = "completed"
    exp["result"] = result
    exp["completed"] = datetime.now().isoformat()
    
    # Update strategy scores
    strategy = exp["strategy"]
    scores = data["strategy_scores"].get(strategy, {"wins": 0, "losses": 0, "total": 0})
    scores["total"] = scores.get("total", 0) + 1
    if result == "success":
        scores["wins"] = scores.get("wins", 0) + 1
    else:
        scores["losses"] = scores.get("losses", 0) + 1
    data["strategy_scores"][strategy] = scores
    
    # Auto-switch to best strategy
    if data.get("active_strategy") == strategy:
        data["active_strategy"] = None  # Reset, will pick best next time
    
    save_experiments(data)
    
    print(f"📊 实验评估: {name} → {'✅ 成功' if result == 'success' else '❌ 失败'}")
    print(f"   策略: {exp['strategy_name']}")
    
    # Show best strategy
    best = max(data["strategy_scores"].items(), 
               key=lambda x: x[1]["wins"] / max(x[1]["total"], 1))
    best_key, best_scores = best
    if best_scores["total"] > 0:
        rate = best_scores["wins"] / best_scores["total"] * 100
        print(f"\n🏆 当前最优策略: {STRATEGIES[best_key]['name']} ({rate:.0f}% 成功率)")


def cmd_best():
    data = load_experiments()
    
    print("🏆 策略排名")
    print("=" * 50)
    
    ranked = sorted(
        data["strategy_scores"].items(),
        key=lambda x: x[1]["wins"] / max(x[1]["total"], 1),
        reverse=True
    )
    
    for i, (key, scores) in enumerate(ranked, 1):
        strategy = STRATEGIES[key]
        total = scores.get("total", 0)
        wins = scores.get("wins", 0)
        rate = wins / total * 100 if total > 0 else 0
        active = " ← 当前" if data.get("active_strategy") == key else ""
        print(f"  {i}. {strategy['name']}: {wins}/{total} ({rate:.0f}%){active}")
        print(f"     {strategy['description'][:60]}")


def cmd_history():
    data = load_experiments()
    
    print("📜 实验历史")
    print("=" * 50)
    
    for exp in reversed(data["experiments"][-10:]):
        status = "🟢" if exp["result"] == "success" else "🔴" if exp["result"] == "fail" else "🟡"
        print(f"  {status} {exp['name']} — {exp['strategy_name']}")
        if exp.get("result"):
            print(f"     结果: {exp['result']} | {exp.get('started', '')[:10]}")


# ============================================================
# Q-Learning 门控（self-evolve policy.ts 移植）
# ============================================================

def should_learn(reward, confidence, used_tools=True, mode="balanced"):
    """
    学习门控：不是所有经验都值得学习
    
    参数:
        reward: [-1, 1] 反馈分数（正=好，负=差）
        confidence: [0, 1] 置信度
        used_tools: 是否使用了工具
        mode: tools_only / balanced / all
    
    返回: bool 是否值得学习
    """
    if mode == "tools_only" and not used_tools:
        return False
    
    if not used_tools and mode == "balanced":
        min_reward = 0.8   # 没用工具时门槛更高
        min_conf = 0.9
    else:
        min_reward = 0.15
        min_conf = 0.55
    
    return abs(reward) >= min_reward and confidence >= min_conf


def rank_candidates(candidates, lambda_param=0.3):
    """
    混合排序：相似度 + Q值 加权
    
    参数:
        candidates: list of {name, similarity, q_value, ...}
        lambda_param: 0=纯相似度, 1=纯Q值
    
    返回: 排序后的candidates（加了score字段）
    """
    if not candidates:
        return []
    
    import statistics
    
    sims = [c.get('similarity', 0.5) for c in candidates]
    qs = [c.get('q_value', 0) for c in candidates]
    
    # Z-score normalization
    def z_score(values):
        if len(values) <= 1:
            return [0.0] * len(values)
        mean = statistics.mean(values)
        std = statistics.stdev(values)
        if std == 0:
            return [0.0] * len(values)
        return [(v - mean) / std for v in values]
    
    sim_z = z_score(sims)
    q_z = z_score(qs)
    
    for i, c in enumerate(candidates):
        c['score'] = (1 - lambda_param) * sim_z[i] + lambda_param * q_z[i]
    
    return sorted(candidates, key=lambda x: x['score'], reverse=True)


def cmd_gate():
    """测试学习门控"""
    print("🚪 Q-Learning 门控测试")
    print("=" * 50)
    
    test_cases = [
        {"reward": 0.9, "confidence": 0.8, "used_tools": True, "label": "高奖励+高信心+有工具"},
        {"reward": 0.1, "confidence": 0.8, "used_tools": True, "label": "低奖励+高信心"},
        {"reward": 0.9, "confidence": 0.3, "used_tools": True, "label": "高奖励+低信心"},
        {"reward": 0.5, "confidence": 0.7, "used_tools": False, "label": "中奖励+无工具"},
        {"reward": -0.8, "confidence": 0.9, "used_tools": True, "label": "负反馈+高信心（该学习避坑）"},
    ]
    
    for tc in test_cases:
        result = should_learn(tc["reward"], tc["confidence"], tc["used_tools"])
        icon = "✅ 学习" if result else "⏭️ 跳过"
        print(f"  {icon} | {tc['label']} (r={tc['reward']}, c={tc['confidence']})")
    
    print("\n📊 混合排序测试:")
    candidates = [
        {"name": "deep-research", "similarity": 0.95, "q_value": 0.8},
        {"name": "doc-creation", "similarity": 0.8, "q_value": 0.3},
        {"name": "tool-install", "similarity": 0.6, "q_value": 0.9},
        {"name": "error-debug", "similarity": 0.7, "q_value": 0.6},
    ]
    ranked = rank_candidates(candidates)
    for c in ranked:
        print(f"  {c['name']}: score={c['score']:.3f} (sim={c['similarity']}, q={c['q_value']})")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(0)
    
    cmd = sys.argv[1]
    
    if cmd == "experiment" and len(sys.argv) >= 4:
        cmd_experiment(sys.argv[2], sys.argv[3])
    elif cmd == "evaluate" and len(sys.argv) >= 4:
        cmd_evaluate(sys.argv[2], sys.argv[3])
    elif cmd == "best":
        cmd_best()
    elif cmd == "history":
        cmd_history()
    elif cmd == "gate":
        cmd_gate()
    else:
        print(__doc__)
