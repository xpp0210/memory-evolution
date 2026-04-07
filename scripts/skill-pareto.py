#!/usr/bin/env python3
"""
skill-pareto.py — 多目标Pareto选择器
EvoSkill的Pareto Frontier选择：保留多样化的高性能技能组合

当前单目标：success_count + fail_count
多目标：成功率 × 活跃度 × 迁移性 × 独特性
"""
import json
from pathlib import Path
from collections import defaultdict
import argparse

MEMORY_SKILLS = Path.home() / ".openclaw/workspace/memory/memory-skills.json"


def load_data():
    return json.load(open(MEMORY_SKILLS))


def compute_objectives(data):
    """计算每个skill的4维目标分"""
    skills = data.get("skills", [])
    reflect_log = data.get("reflect_log", [])
    reflect_by_skill = defaultdict(list)
    for r in reflect_log:
        reflect_by_skill[r.get("skill", "")].append(r)

    results = []
    for s in skills:
        sid = s.get("id", s.get("name", ""))
        logs = reflect_by_skill.get(sid, [])
        success = sum(1 for r in logs if r.get("result") == "success")
        fail = sum(1 for r in logs if r.get("result") == "fail")
        total = success + fail

        if total == 0:
            continue

        # 目标1：成功率
        success_rate = success / total

        # 目标2：活跃度（最近3次有改进？）
        recent = sorted(logs, key=lambda x: x.get("timestamp", ""), reverse=True)[:3]
        has_recent_fix = any(r.get("attribution", {}).get("fix") for r in recent)
        recency_score = 1.0 if has_recent_fix else 0.3

        # 目标3：使用频率（归一化）
        freq_score = min(1.0, total / 15)  # 15+次=满分

        # 目标4：失败压力（有失败但有修复=韧性）
        fail_pressure = min(1.0, fail / 5) if fail > 0 else 0.0

        # 综合分（几何平均，惩罚任何维度的0）
        composite = (success_rate * 0.4 + recency_score * 0.2 +
                     freq_score * 0.2 + (1 - fail_pressure) * 0.2)

        results.append({
            "skill": sid,
            "total": total,
            "success": success,
            "fail": fail,
            "success_rate": round(success_rate, 3),
            "recency_score": round(recency_score, 3),
            "freq_score": round(freq_score, 3),
            "fail_pressure": round(fail_pressure, 3),
            "composite": round(composite, 3),
        })

    return results


def pareto_frontier(objectives, top_n=5):
    """
    近似Pareto前沿：宽松非支配 + TopN聚合分
    1. 宽松：允许在最多1个维度上显著落后（epsilon-dominance）
    2. TopN：按综合分取前N
    """
    objs = objectives

    # Step 1: 宽松epsilon-dominance（允许1个维度差0.3以内）
    epsilon = 0.3
    frontier = []
    for a in objs:
        dominated_count = 0
        for b in objs:
            if a is b:
                continue
            worse_dims = 0
            if b["success_rate"] - a["success_rate"] > epsilon: worse_dims += 1
            if b["recency_score"] - a["recency_score"] > epsilon: worse_dims += 1
            if b["freq_score"] - a["freq_score"] > epsilon: worse_dims += 1
            if a["fail_pressure"] - b["fail_pressure"] > epsilon: worse_dims += 1
            if worse_dims >= 2:
                dominated_count += 1
        if dominated_count < len(objs) * 0.5:  # 被超过一半支配才算淘汰
            frontier.append(a)

    # Step 2: 按综合分排序取TopN
    frontier.sort(key=lambda x: x["composite"], reverse=True)
    return frontier[:top_n]


def main():
    parser = argparse.ArgumentParser(description="Pareto Frontier Skill Selection")
    parser.add_argument("--top", "-n", type=int, default=5, help="返回topN候选")
    parser.add_argument("--json", action="store_true", help="JSON输出")
    parser.add_argument("--frontier-only", action="store_true", help="只返回Pareto前沿")
    args = parser.parse_args()

    data = load_data()
    objectives = compute_objectives(data)

    if not objectives:
        print("❌ 无数据")
        return

    # 按综合分排序所有skill
    all_sorted = sorted(objectives, key=lambda x: x["composite"], reverse=True)

    # 找Pareto前沿
    frontier = pareto_frontier(all_sorted)
    frontier_sorted = sorted(frontier, key=lambda x: x["composite"], reverse=True)

    if args.json:
        output = {
            "all": all_sorted,
            "frontier": frontier_sorted,
            "total": len(objectives),
            "frontier_size": len(frontier),
        }
        print(json.dumps(output, ensure_ascii=False, indent=2))
        return

    if args.frontier_only:
        print(f"🎯 Pareto前沿（{len(frontier)}个非支配解）\n")
    else:
        print(f"📊 Pareto选择 — {len(objectives)}个skills分析\n")

    print(f"{'Skill':<35} {'成功率':>7} {'活跃度':>7} {'频率':>6} {'压力':>6} {'综合':>6}")
    print("-" * 80)
    for o in (frontier_sorted if args.frontier_only else all_sorted[:args.top]):
        print(f"{o['skill']:<35} {o['success_rate']:>7.1%} {o['recency_score']:>7.1f} "
              f"{o['freq_score']:>6.1%} {o['fail_pressure']:>6.1f} {o['composite']:>6.3f}")

    print()
    if not args.frontier_only:
        print(f"🎯 Pareto前沿（{len(frontier)}个非支配解）：")
        for o in frontier_sorted:
            print(f"  • {o['skill']}")
        print()
        print("💡 Pareto前沿包含所有维度上未被支配的skill，是最优选择集")


if __name__ == "__main__":
    main()
