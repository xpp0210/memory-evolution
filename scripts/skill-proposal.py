#!/usr/bin/env python3
"""
skill-proposal.py — 失败驱动技能提案生成器
EvoSkill的Proposer角色：分析reflect_log → 自动生成skill改进建议

输出: memory/evolution/pending-skill-proposals.json
"""
import json
from pathlib import Path
from collections import defaultdict
from datetime import datetime

MEMORY_SKILLS = Path.home() / ".openclaw/workspace/memory/memory-skills.json"
OUTPUT = Path.home() / ".openclaw/workspace/memory/evolution/pending-skill-proposals.json"


def load_reflect_log():
    data = json.load(open(MEMORY_SKILLS))
    return data.get("reflect_log", [])


def extract_failures(reflect_log):
    """提取所有失败和有根因分析的成功记录"""
    records = []
    for r in reflect_log:
        if r.get("result") == "fail":
            records.append({
                "skill": r.get("skill"),
                "type": "fail",
                "note": r.get("note", ""),
                "timestamp": r.get("timestamp"),
                "attribution": r.get("attribution", {}),
            })
        elif r.get("attribution"):
            records.append({
                "skill": r.get("skill"),
                "type": "success_with_fix",
                "note": r.get("note", ""),
                "timestamp": r.get("timestamp"),
                "attribution": r.get("attribution", {}),
            })
    return records


def cluster_by_root_cause(records):
    """按根因聚类"""
    clusters = defaultdict(list)
    for r in records:
        cause = r["attribution"].get("root_cause", r["note"][:50] if r["note"] else "unknown")
        clusters[cause].append(r)
    return clusters


def generate_proposal(skill, cluster):
    """为每个聚类生成skill改进提案"""
    failures = [r for r in cluster if r["type"] == "fail"]
    fixes = [r["attribution"].get("fix", "") for r in cluster if r["attribution"].get("fix")]

    if failures:
        primary = "fail"
        description = f"{len(failures)}次失败，最近: {failures[-1]['note']}"
    else:
        primary = "fix_applied"
        description = f"应用了{len(fixes)}次修复"

    return {
        "skill": skill,
        "primary_issue": primary,
        "description": description,
        "failure_count": len(failures),
        "existing_fixes": list(dict.fromkeys(fixes))[:3],  # deduplicate
        "proposal": generate_fix_suggestion(skill, cluster),
        "priority": "high" if len(failures) >= 2 else ("medium" if failures else "low"),
    }


def generate_fix_suggestion(skill, cluster):
    """基于聚类中的修复经验生成具体建议"""
    fixes = [r["attribution"].get("fix", "") for r in cluster if r["attribution"].get("fix")]
    if fixes:
        return f"已有修复方案: {'; '.join(fixes[:2])}"
    failures = [r for r in cluster if r["type"] == "fail"]
    if failures:
        return f"需要人工分析: {failures[0].get('note', '见日志')}"
    return "观察中，暂无建议"


def main():
    reflect_log = load_reflect_log()
    records = extract_failures(reflect_log)

    if not records:
        print("✅ 无失败记录，跳过提案")
        return

    clusters = cluster_by_root_cause(records)
    proposals = []

    for cause, cluster in clusters.items():
        skills_in_cluster = set(r["skill"] for r in cluster)
        for skill in skills_in_cluster:
            same_skill_cluster = [r for r in cluster if r["skill"] == skill]
            proposals.append(generate_proposal(skill, same_skill_cluster))

    # Deduplicate by skill
    seen = set()
    unique = []
    for p in proposals:
        key = (p["skill"], p["description"][:30])
        if key not in seen:
            seen.add(key)
            unique.append(p)

    # Sort by priority
    priority_order = {"high": 0, "medium": 1, "low": 2}
    unique.sort(key=lambda x: (priority_order.get(x["priority"], 3), -x["failure_count"]))

    output = {
        "generated_at": datetime.now().isoformat(),
        "total_proposals": len(unique),
        "proposals": unique,
    }

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    json.dump(output, open(OUTPUT, "w"), ensure_ascii=False, indent=2)

    print(f"✅ 生成{len(unique)}个提案 → {OUTPUT}")
    for p in unique:
        fix_info = f" | 已有: {p['existing_fixes'][0][:40]}" if p["existing_fixes"] else ""
        print(f"  {'🔴' if p['priority']=='high' else '🟡' if p['priority']=='medium' else '🟢'} [{p['skill']}] {p['description'][:50]}{fix_info}")


if __name__ == "__main__":
    main()
