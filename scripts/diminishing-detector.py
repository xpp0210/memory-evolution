#!/usr/bin/env python3
"""
diminishing-detector.py — 递减检测止损器 (P2自适应阈值版)

借鉴 insightx/self-evolution 的 diminishing returns 检测机制。

P2升级：自适应阈值
- 高频skill(≥10次)：SUCCESS_THRESHOLD=0.50，更严格
- 中频skill(3-9次)：SUCCESS_THRESHOLD=0.40，标准
- 低频skill(≤2次)：SUCCESS_THRESHOLD=0.30，放宽
"""
import json
import sys
from pathlib import Path
from datetime import datetime

WORKSPACE = Path(__file__).resolve().parent.parent
MEMORY_DIR = WORKSPACE / "memory"
DIAGNOSTICS_DIR = MEMORY_DIR / "diagnostics"
SKILLS_FILE = MEMORY_DIR / "memory-skills.json"

# P2自适应阈值
HIGH_USAGE = 10
MEDIUM_USAGE = 3
SUCCESS_THRESHOLD_HIGH = 0.50   # 高频skill(≥10次)：50%以上才健康
SUCCESS_THRESHOLD_MEDIUM = 0.40  # 中频skill(3-9次)：40%
SUCCESS_THRESHOLD_LOW = 0.30      # 低频skill(≤2次)：30%宽松
STRUGGLING_HIGH = 0.30
STRUGGLING_MEDIUM = 0.40
STAGNATION_ROUNDS = 3
MIN_SAMPLES = 3


def load_skills():
    with open(SKILLS_FILE) as f:
        data = json.load(f)
    return {s["id"]: s for s in data.get("skills", [])}


def check_skill(skill_id, skill):
    """P2升级：自适应阈值基于skill使用频率"""
    success = skill.get("success_count", 0)
    fail = skill.get("fail_count", 0)
    total = success + fail

    if total == 0:
        return {
            "id": skill_id,
            "name": skill.get("name", skill_id),
            "total": 0,
            "success": 0,
            "fail": 0,
            "status": "unused",
            "message": "从未使用",
            "action": "observe",
        }

    rate = success / total

    if total >= HIGH_USAGE:
        threshold_note = "高频(>=10)"
        if rate >= SUCCESS_THRESHOLD_HIGH:
            status, message, action = "healthy", f"高频skill成功率{rate:.0%}，良好", "maintain"
        elif rate >= STRUGGLING_HIGH:
            status, message, action = "needs_improvement", f"高频skill成功率{rate:.0%}，需提升", "optimize"
        else:
            status, message, action = "struggling", f"高频skill成功率{rate:.0%}，建议检查", "review_or_retire"
    elif total >= MEDIUM_USAGE:
        threshold_note = "中频(3-9)"
        if rate >= SUCCESS_THRESHOLD_MEDIUM:
            status, message, action = "healthy", f"成功率{rate:.0%}，良好", "maintain"
        elif rate >= STRUGGLING_MEDIUM:
            status, message, action = "needs_improvement", f"成功率{rate:.0%}，有提升空间", "optimize"
        else:
            status, message, action = "struggling", f"成功率{rate:.0%}，建议检查或淘汰", "review_or_retire"
    else:
        threshold_note = "低频(<=2)"
        if rate >= SUCCESS_THRESHOLD_LOW:
            status, message, action = "healthy", f"低频skill成功率{rate:.0%}，正常", "maintain"
        else:
            status, message, action = "needs_improvement", f"低频skill成功率{rate:.0%}，继续观察", "observe"

    return {
        "id": skill_id,
        "name": skill.get("name", skill_id),
        "total": total,
        "success": success,
        "fail": fail,
        "rate": round(rate, 3),
        "threshold_note": threshold_note,
        "status": status,
        "message": message,
        "action": action,
    }


def check_overall():
    """总体递减检测"""
    skills = load_skills()
    if not skills:
        print("❌ memory-skills.json不存在或为空")
        return []

    results = []
    for skill_id, skill in sorted(skills.items(), key=lambda x: -(x[1].get("success_count", 0) + x[1].get("fail_count", 0))):
        r = check_skill(skill_id, skill)
        if r and r["status"] != "healthy":
            results.append(r)

    return results


def cmd_check():
    """检查所有skills的状态"""
    results = check_overall()
    if not results:
        print("✅ 所有skill状态健康")
        return

    print(f"⚠️ {len(results)}个skill需要关注:\n")
    print(f"{'Skill':<30} {'使用':>6} {'成功':>5} {'失败':>5} {'阈值类型':>12} {'状态':>18}")
    print("-" * 100)
    for r in results:
        print(f"{r['name']:<30} {r['total']:>6} {r['success']:>5} {r['fail']:>5} "
              f"{r.get('threshold_note', 'N/A'):>12} {r['status']:>18}")


def cmd_skill(skill_id):
    """检查单个skill"""
    skills = load_skills()
    if skill_id not in skills:
        print(f"❌ Skill '{skill_id}' 不存在")
        return
    r = check_skill(skill_id, skills[skill_id])
    print(f"\n{r['name']} ({skill_id})")
    print(f"  使用: {r['total']}次（成功{r['success']} / 失败{r['fail']}）")
    if 'rate' in r:
        print(f"  成功率: {r['rate']:.0%}")
        print(f"  阈值类型: {r.get('threshold_note', 'N/A')}")
    print(f"  状态: {r['status']}")
    print(f"  建议: {r['message']}")
    print(f"  操作: {r['action']}")


def cmd_report():
    """生成完整诊断报告"""
    DIAGNOSTICS_DIR.mkdir(parents=True, exist_ok=True)
    skills = load_skills()
    all_results = []
    for skill_id, skill in skills.items():
        all_results.append(check_skill(skill_id, skill))

    struggling = [r for r in all_results if r["status"] == "struggling"]
    needs_improvement = [r for r in all_results if r["status"] == "needs_improvement"]
    healthy = [r for r in all_results if r["status"] == "healthy"]

    report = {
        "timestamp": datetime.now().isoformat(),
        "total_skills": len(skills),
        "struggling": struggling,
        "needs_improvement": needs_improvement,
        "healthy": healthy,
    }

    out_file = DIAGNOSTICS_DIR / f"diminishing-{datetime.now().strftime('%Y%m%d')}.json"
    with open(out_file, "w") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(f"📊 递减检测报告")
    print(f"   总skills: {len(skills)}")
    print(f"   ✅ healthy: {len(healthy)}")
    print(f"   🟡 needs_improvement: {len(needs_improvement)}")
    print(f"   ⚠️ struggling: {len(struggling)}")
    print(f"   报告: {out_file}")
    return report


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: diminishing-detector.py <check|skill|report> [skill_id]")
        sys.exit(1)

    cmd = sys.argv[1]
    if cmd == "check":
        cmd_check()
    elif cmd == "skill" and len(sys.argv) >= 3:
        cmd_skill(sys.argv[2])
    elif cmd == "report":
        cmd_report()
    else:
        print("用法: diminishing-detector.py <check|skill|report> [skill_id]")
