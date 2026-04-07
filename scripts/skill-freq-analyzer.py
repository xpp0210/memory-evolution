#!/usr/bin/env python3
"""
skill-freq-analyzer.py — Phase 11预备
分析reflect_log中skill使用频率，为SKILL0式渐进撤除提供数据支持

输出：
1. skill使用频率排名
2. 高频skill名单（可内化候选）
3. 低频skill名单（可精简/归档）
4. 技能Token预算建议（基于使用频率分配详细度）
"""
import json
from pathlib import Path
from collections import defaultdict
import argparse

MEMORY_SKILLS = Path.home() / ".openclaw/workspace/memory/memory-skills.json"


def load_reflect_log():
    data = json.load(open(MEMORY_SKILLS))
    return data.get("reflect_log", [])


def analyze_skill_usage(reflect_log):
    """分析skill使用频率和效率"""
    skill_stats = defaultdict(lambda: {"success": 0, "fail": 0, "notes": []})

    for r in reflect_log:
        skill = r.get("skill", "unknown")
        result = r.get("result", "success")
        note = r.get("note", "")
        skill_stats[skill][result] += 1
        if note:
            skill_stats[skill]["notes"].append(note[:80])

    results = []
    for skill, stats in skill_stats.items():
        total = stats["success"] + stats["fail"]
        success_rate = stats["success"] / total if total > 0 else 0
        results.append({
            "skill": skill,
            "total": total,
            "success": stats["success"],
            "fail": stats["fail"],
            "success_rate": round(success_rate, 2),
            "high_freq": total >= 10,
            "low_freq": total <= 2,
        })

    return sorted(results, key=lambda x: x["total"], reverse=True)


def token_budget_recommendation(usage_stats):
    """
    基于SKILL0思路：高频skill应该更精简，低频skill可以更详细
    分配Token预算：
    - 高频(≥10次)：<500 tokens（精简核心步骤）
    - 中频(3-9次)：500-1500 tokens（标准SKILL.md）
    - 低频(≤2次)：1500-3000 tokens（完整细节）
    """
    recommendations = []
    for s in usage_stats:
        if s["high_freq"]:
            budget = "<500 tokens"
            action = "精简：核心步骤+关键边界，中文缩写版"
        elif s["low_freq"]:
            budget = "1500-3000 tokens"
            action = "保持完整：详细步骤+示例+常见错误"
        else:
            budget = "500-1500 tokens"
            action = "标准：保留完整结构"

        recommendations.append({
            "skill": s["skill"],
            "total": s["total"],
            "budget": budget,
            "action": action,
            "priority": "🔴高频" if s["high_freq"] else ("🟡中频" if not s["low_freq"] else "🟢低频"),
        })
    return recommendations


def main():
    parser = argparse.ArgumentParser(description="Skill频率分析与Token预算建议")
    parser.add_argument("--json", action="store_true", help="JSON输出")
    args = parser.parse_args()

    reflect_log = load_reflect_log()
    stats = analyze_skill_usage(reflect_log)

    if args.json:
        print(json.dumps({
            "usage": stats,
            "recommendations": token_budget_recommendation(stats),
        }, ensure_ascii=False, indent=2))
        return

    print("📊 Skill使用频率分析\n")
    print(f"{'Skill':<35} {'总使用':>6} {'成功':>5} {'失败':>5} {'成功率':>7} {'频率':>6}")
    print("-" * 75)
    for s in stats:
        freq_label = "🔴高频" if s["high_freq"] else ("🟢低频" if s["low_freq"] else "🟡中频")
        print(f"{s['skill']:<35} {s['total']:>6} {s['success']:>5} {s['fail']:>5} {s['success_rate']:>7.0%} {freq_label:>6}")

    print("\n📋 Token预算建议（SKILL0渐进撤除思路）\n")
    for r in token_budget_recommendation(stats):
        print(f"{r['priority']} {r['skill']:<30} {r['budget']:<20} → {r['action']}")


if __name__ == "__main__":
    main()
