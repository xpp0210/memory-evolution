#!/bin/bash
# skill-capture.sh — OpenSpace FIX/DERIVED/CAPTURED 自动技能捕获
# 借鉴 OpenSpace (HKUDS) 三模式进化机制
# 
# 用法：
#   skill-capture.sh fix <skill_id> <error_desc>           FIX模式：修复失败技能
#   skill-capture.sh derived <task_pattern> <frequency>     DERIVED模式：从重复模式派生新技能
#   skill-capture.sh captured <task_desc> <steps_file>      CAPTURED模式：从成功任务捕获技能
#   skill-capture.sh scan                                    扫描待捕获的任务模式
#   skill-capture.sh status                                  查看捕获统计

set -euo pipefail

SKILLS_FILE="$HOME/.openclaw/workspace/memory/memory-skills.json"
CAPTURE_DIR="$HOME/.openclaw/workspace/memory/skill-captures"
EXPERIENCE_FILE="$HOME/.openclaw/workspace/memory/experience-patterns.md"
RULES_FILE="$HOME/.openclaw/workspace/memory/iteration-rules.md"

mkdir -p "$CAPTURE_DIR"

CMD="${1:-status}"

case "$CMD" in

  status)
    python3 -c "
import json, os, glob

# Count captures
capture_dir = '$CAPTURE_DIR'
fixes = glob.glob(f'{capture_dir}/fix-*.json')
derived = glob.glob(f'{capture_dir}/derived-*.json')
captured = glob.glob(f'{capture_dir}/captured-*.json')

print('📊 技能捕获统计 (OpenSpace FIX/DERIVED/CAPTURED)')
print('='*50)
print(f'  FIX     (修复): {len(fixes)} 条')
print(f'  DERIVED (派生): {len(derived)} 条')
print(f'  CAPTURED(捕获): {len(captured)} 条')
print(f'  总计: {len(fixes)+len(derived)+len(captured)} 条')

# Show recent
all_files = sorted(fixes + derived + captured, key=os.path.getmtime, reverse=True)
if all_files:
    print(f'\n最近捕获:')
    for f in all_files[:5]:
        with open(f) as fh:
            d = json.load(fh)
        mode = 'FIX' if 'fix' in os.path.basename(f) else 'DERIVED' if 'derived' in os.path.basename(f) else 'CAPTURED'
        status = d.get('status', '?')
        print(f'  [{mode}] {d.get(\"skill_id\",\"?\")} - {d.get(\"description\",\"?\")[:50]} ({status})')
"
    ;;

  fix)
    # FIX模式：技能执行失败时，分析原因并生成修复方案
    SKILL_ID="${2:?Usage: skill-capture.sh fix <skill_id> <error_desc>}"
    ERROR_DESC="${3:-无描述}"
    TIMESTAMP=$(date +%Y%m%d-%H%M%S)
    CAPTURE_FILE="$CAPTURE_DIR/fix-${SKILL_ID}-${TIMESTAMP}.json"

    python3 -c "
import json, datetime

skill_id = '$SKILL_ID'
error_desc = '''$ERROR_DESC'''
ts = '$TIMESTAMP'

# Load skill info
with open('$SKILLS_FILE') as f:
    data = json.load(f)

skill = None
for s in data.get('skills', []):
    if s['id'] == skill_id:
        skill = s
        break

if not skill:
    print(f'❌ Skill {skill_id} not found')
    exit(1)

# Get failure history
failures = [r for r in data.get('reflect_log', [])
            if r.get('skill') == skill_id and r.get('result') in ('fail', 'partial')]

# Get existing rules for this skill
skill_rules = []
with open('$RULES_FILE') as f:
    content = f.read()
    if skill_id in content:
        skill_rules = ['已有相关规则（见 iteration-rules.md）']

capture = {
    'mode': 'FIX',
    'skill_id': skill_id,
    'skill_name': skill.get('name', ''),
    'timestamp': datetime.datetime.now().isoformat(),
    'status': 'pending_review',
    'description': error_desc,
    'failure_count': len(failures),
    'failure_history': [
        {'note': f.get('note', ''), 'time': f.get('timestamp', '')}
        for f in failures[-5:]
    ],
    'existing_action': skill.get('action', ''),
    'existing_checks': skill.get('reflect_checks', []),
    'existing_rules': skill_rules,
    'fix_analysis': {
        'error_pattern': None,        # 待LLM填写：错误模式是什么？
        'root_cause_category': None,   # 待LLM填写：工具/网络/理解/格式/资源
        'fix_type': None,              # 待LLM填写：patch(小修)/restructure(重构)/new_rule(新规则)
        'suggested_action_update': None,
        'suggested_check_addition': None,
        'suggested_rule': None
    }
}

with open('$CAPTURE_FILE'.replace('\\$TIMESTAMP', ts), 'w') as f:
    json.dump(capture, f, indent=2, ensure_ascii=False)

print(f'🔧 FIX捕获已创建: {skill_id}')
print(f'   失败次数: {len(failures)}')
print(f'   错误描述: {error_desc}')
print(f'   文件: fix-{skill_id}-{ts}.json')
print()
print('📋 下一步：让安宝分析此捕获，填写 fix_analysis 字段')
print(f'   文件路径: $CAPTURE_DIR/fix-{skill_id}-{ts}.json')
" 2>&1 | sed "s/\$TIMESTAMP/$TIMESTAMP/g; s/\$CAPTURE_DIR/$(echo $CAPTURE_DIR | sed 's/\//\\\//g')/g; s/\$SKILL_ID/$SKILL_ID/g"

    # Simpler approach - just create the file directly
    python3 << PYEOF
import json, datetime, os

skill_id = "$SKILL_ID"
error_desc = """$ERROR_DESC"""
ts = "$TIMESTAMP"

with open("$SKILLS_FILE") as f:
    data = json.load(f)

skill = None
for s in data.get("skills", []):
    if s["id"] == skill_id:
        skill = s
        break

if not skill:
    print(f"Skill {skill_id} not found")
    exit(0)

failures = [r for r in data.get("reflect_log", [])
            if r.get("skill") == skill_id and r.get("result") in ("fail", "partial")]

capture = {
    "mode": "FIX",
    "skill_id": skill_id,
    "skill_name": skill.get("name", ""),
    "timestamp": datetime.datetime.now().isoformat(),
    "status": "pending_review",
    "description": error_desc,
    "failure_count": len(failures),
    "failure_history": [
        {"note": f.get("note", ""), "time": f.get("timestamp", "")}
        for f in failures[-5:]
    ],
    "existing_action": skill.get("action", ""),
    "existing_checks": skill.get("reflect_checks", []),
    "fix_analysis": {
        "error_pattern": None,
        "root_cause_category": None,
        "fix_type": None,
        "suggested_action_update": None,
        "suggested_check_addition": None,
        "suggested_rule": None
    }
}

path = os.path.join("$CAPTURE_DIR", f"fix-{skill_id}-{ts}.json")
with open(path, "w") as f:
    json.dump(capture, f, indent=2, ensure_ascii=False)

print(f"FIX captured: fix-{skill_id}-{ts}.json")
PYEOF
    ;;

  derived)
    # DERIVED模式：检测到重复任务模式，派生新技能
    TASK_PATTERN="${2:?Usage: skill-capture.sh derived <task_pattern> <frequency>}"
    FREQUENCY="${3:-3}"
    TIMESTAMP=$(date +%Y%m%d-%H%M%S)

    python3 << PYEOF
import json, datetime, os

task_pattern = """$TASK_PATTERN"""
frequency = int("$FREQUENCY")
ts = "$TIMESTAMP"

# Generate skill ID from pattern
import re
skill_id = re.sub(r'[^a-z0-9]+', '-', task_pattern.lower()[:30]).strip('-')

# Check if similar skill already exists
with open("$SKILLS_FILE") as f:
    data = json.load(f)

existing_ids = [s["id"] for s in data.get("skills", [])]
if skill_id in existing_ids:
    skill_id = f"{skill_id}-v2"

capture = {
    "mode": "DERIVED",
    "skill_id": skill_id,
    "timestamp": datetime.datetime.now().isoformat(),
    "status": "pending_design",
    "description": f"从重复任务模式派生: {task_pattern}",
    "frequency": frequency,
    "source_pattern": task_pattern,
    "derived_skill": {
        "id": skill_id,
        "name": None,               # 待设计
        "trigger": task_pattern,
        "action": None,             # 待设计
        "memory_focus": None,       # 待设计
        "reflect_checks": [],       # 待设计
        "priority": "medium",
        "success_count": 0,
        "fail_count": 0
    },
    "source_skills": [],            # 从哪些已有skill拆分出来
    "rationale": f"该任务模式出现{frequency}次，值得独立为专门技能"
}

path = os.path.join("$CAPTURE_DIR", f"derived-{skill_id}-{ts}.json")
with open(path, "w") as f:
    json.dump(capture, f, indent=2, ensure_ascii=False)

print(f"DERIVED captured: derived-{skill_id}-{ts}.json")
print(f"  新技能ID: {skill_id}")
print(f"  任务模式: {task_pattern}")
print(f"  出现频率: {frequency}次")
print()
print("下一步: 让安宝设计 derived_skill 的完整定义")
PYEOF
    ;;

  captured)
    # CAPTURED模式：从成功完成的复杂任务中捕获可复用流程
    TASK_DESC="${2:?Usage: skill-capture.sh captured <task_desc> <steps_file>}"
    STEPS_FILE="${3:-}"
    TIMESTAMP=$(date +%Y%m%d-%H%M%S)

    python3 << PYEOF
import json, datetime, os, re

task_desc = """$TASK_DESC"""
steps_file = """$STEPS_FILE"""
ts = "$TIMESTAMP"

# Read steps if file provided
steps_content = ""
if steps_file and os.path.exists(steps_file):
    with open(steps_file) as f:
        steps_content = f.read()

# Generate skill ID
skill_id = re.sub(r'[^a-z0-9]+', '-', task_desc.lower()[:30]).strip('-')

capture = {
    "mode": "CAPTURED",
    "skill_id": skill_id,
    "timestamp": datetime.datetime.now().isoformat(),
    "status": "pending_extraction",
    "description": f"从成功任务捕获: {task_desc}",
    "task_description": task_desc,
    "execution_steps": steps_content if steps_content else "（步骤待补充）",
    "captured_skill": {
        "id": skill_id,
        "name": None,
        "trigger": None,
        "action": None,
        "memory_focus": None,
        "reflect_checks": [],
        "priority": "medium",
        "success_count": 1,
        "fail_count": 0
    },
    "reusable_patterns": [],        # 待提取
    "tools_used": [],               # 待提取
    "error_points_avoided": []      # 待提取
}

path = os.path.join("$CAPTURE_DIR", f"captured-{skill_id}-{ts}.json")
with open(path, "w") as f:
    json.dump(capture, f, indent=2, ensure_ascii=False)

print(f"CAPTURED captured: captured-{skill_id}-{ts}.json")
print(f"  任务: {task_desc}")
print()
print("下一步: 让安宝从执行过程中提取可复用的 skill 定义")
PYEOF
    ;;

  scan)
    # 扫描 reflect_log 中的模式，发现可派生的新技能
    python3 << PYEOF
import json
from collections import Counter

with open("$SKILLS_FILE") as f:
    data = json.load(f)

log = data.get("reflect_log", [])

# 1. Find repeated failure patterns → FIX candidates
fail_notes = [r.get("note", "") for r in log if r.get("result") in ("fail", "partial")]
fail_counter = Counter(fail_notes)

print("🔍 扫描结果")
print("="*60)

if fail_counter:
    print("\n🔧 FIX 候选（重复失败模式）:")
    for note, count in fail_counter.most_common(5):
        if count >= 2:
            print(f"  [{count}x] {note[:80]}")

# 2. Find success clusters → DERIVED candidates
success_by_skill = {}
for r in log:
    if r.get("result") == "success":
        sid = r.get("skill", "unknown")
        success_by_skill.setdefault(sid, []).append(r.get("note", ""))

print("\n🧬 DERIVED 候选（高频成功技能可拆分）:")
for sid, notes in success_by_skill.items():
    if len(notes) >= 5:
        print(f"  {sid}: {len(notes)} 次成功，检查是否有子模式")
        # Simple pattern detection
        for note in notes:
            if note and len(note) > 10:
                print(f"    - {note[:80]}")

# 3. Find complex successful tasks → CAPTURED candidates
print("\n📸 CAPTURED 候选（复杂成功任务可捕获）:")
for r in log[-10:]:
    if r.get("result") == "success" and len(r.get("note", "")) > 30:
        print(f"  [{r.get('skill','')}] {r.get('note','')[:80]}")

# 4. Pending captures
import glob, os
pending = []
for f in glob.glob("$CAPTURE_DIR/*.json"):
    with open(f) as fh:
        d = json.load(fh)
    if d.get("status", "").startswith("pending"):
        pending.append(d)

if pending:
    print(f"\n⏳ 待处理捕获: {len(pending)} 条")
    for p in pending:
        print(f"  [{p['mode']}] {p.get('skill_id','')} - {p.get('status','')}")

PYEOF
    ;;

  apply)
    # 将已审查的捕获应用到 memory-skills.json
    CAPTURE_FILE="${2:?Usage: skill-capture.sh apply <capture_file>}"

    if [ ! -f "$CAPTURE_FILE" ]; then
      echo "❌ 文件不存在: $CAPTURE_FILE"
      exit 1
    fi

    python3 << PYEOF
import json, os

capture_file = "$CAPTURE_FILE"

with open(capture_file) as f:
    capture = json.load(f)

if capture.get("status") == "pending_review":
    print("⚠️ 捕获尚未审查。先让安宝填写分析字段。")
    exit(1)

mode = capture.get("mode")
skill_id = capture.get("skill_id")

with open("$SKILLS_FILE") as f:
    data = json.load(f)

if mode == "FIX":
    # Patch existing skill
    for s in data.get("skills", []):
        if s["id"] == skill_id:
            fix = capture.get("fix_analysis", {})
            if fix.get("suggested_action_update"):
                s["action"] = fix["suggested_action_update"]
            if fix.get("suggested_check_addition"):
                checks = s.get("reflect_checks", [])
                new_checks = fix["suggested_check_addition"]
                if isinstance(new_checks, list):
                    checks.extend(new_checks)
                else:
                    checks.append(new_checks)
                s["reflect_checks"] = checks
            # Reset fail counter
            s["fail_count"] = 0
            print(f"✅ FIX applied to {skill_id}")
            break

elif mode in ("DERIVED", "CAPTURED"):
    derived = capture.get("derived_skill") or capture.get("captured_skill")
    if derived and derived.get("action"):
        # Add new skill
        skills = data.get("skills", [])
        existing_ids = [s["id"] for s in skills]
        if derived["id"] not in existing_ids:
            skills.append(derived)
            data["skills"] = skills
            print(f"✅ {mode} applied: new skill {derived['id']}")
        else:
            print(f"⚠️ Skill {derived['id']} already exists")
    else:
        print(f"⚠️ Skill definition incomplete, cannot apply")
        exit(1)

# Add to evolution log
evo_log = data.get("evolution_log", [])
evo_log.append({
    "date": capture.get("timestamp", ""),
    "action": f"{mode}: {capture.get('description', '')[:80]}",
    "inspired_by": f"OpenSpace {mode} mode"
})
data["evolution_log"] = evo_log

with open("$SKILLS_FILE", "w") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

# Mark capture as applied
capture["status"] = "applied"
with open(capture_file, "w") as f:
    json.dump(capture, f, indent=2, ensure_ascii=False)

print(f"📝 捕获已标记为 applied")

# If there's a suggested rule, append to iteration-rules
rule = None
if mode == "FIX":
    rule = capture.get("fix_analysis", {}).get("suggested_rule")
if rule:
    print(f"📋 建议规则: {rule}")
    print(f"   请手动添加到 $RULES_FILE")

PYEOF
    ;;

  *)
    echo "skill-capture.sh — OpenSpace FIX/DERIVED/CAPTURED 自动技能捕获"
    echo ""
    echo "三模式说明："
    echo "  FIX     — 技能执行失败时，捕获错误模式并生成修复方案"
    echo "  DERIVED — 发现重复任务模式时，派生新的专门技能"
    echo "  CAPTURED— 复杂任务成功完成后，捕获为可复用技能"
    echo ""
    echo "命令："
    echo "  fix <skill_id> <error>            捕获失败模式"
    echo "  derived <pattern> <frequency>      从重复模式派生技能"
    echo "  captured <desc> [steps_file]       从成功任务捕获技能"
    echo "  scan                               扫描待捕获的模式"
    echo "  apply <capture_file>               应用已审查的捕获"
    echo "  status                             查看统计"
    ;;
esac

# ============================================================
# 经验评分晋升系统（claude-skills memory-analyst 移植）
# ============================================================
# 每条经验按三维度打分，总分>=6 晋升为规则

score_experience() {
    local capture_file="$1"
    
    if [ ! -f "$capture_file" ]; then
        echo "❌ 文件不存在: $capture_file"
        return 1
    fi
    
    local desc=$(python3 -c "
import json, sys
d = json.load(open('$capture_file'))
print(d.get('description', d.get('error_description', '未知')))
")
    
    echo "📊 经验评分: ${desc:0:60}..."
    echo "   请为三个维度打分 (0-3):"
    echo ""
    echo "   Durability (持久性):"
    echo "     0 = 一次性经验，不会再遇到"
    echo "     1 = 偶尔会遇到"
    echo "     2 = 经常遇到"
    echo "     3 = 几乎每天都会遇到"
    echo ""
    echo "   Impact (影响力):"
    echo "     0 = 无影响"
    echo "     1 = 节省几分钟"
    echo "     2 = 避免重大错误或节省大量时间"
    echo "     3 = 改变工作方式"
    echo ""
    echo "   Scope (作用范围):"
    echo "     0 = 仅当前项目"
    echo "     1 = 当前类型的任务"
    echo "     2 = 跨类型的多个任务"
    echo "     3 = 所有任务都适用"
}

# 自动评分（基于已有统计数据推断）
auto_score() {
    local skill_id="$1"
    
    python3 << 'PYEOF'
import json, os, sys

BASE = os.path.expanduser("~/.openclaw/workspace")
skill_id = sys.argv[1] if len(sys.argv) > 1 else ""

# Load stats
skills_file = os.path.join(BASE, "memory/memory-skills.json")
exp_file = os.path.join(BASE, "memory/experience-patterns.md")

with open(skills_file) as f:
    data = json.load(f)

for skill in data.get("skills", []):
    if skill.get("id") == skill_id:
        s = skill.get("success_count", 0)
        f_count = skill.get("fail_count", 0)
        total = s + f_count
        
        # Auto-score based on history
        durability = min(3, total // 3)  # 使用次数越多越持久
        impact = 3 if f_count > 2 else (2 if f_count > 0 else 1)  # 失败过=有影响
        scope = 3 if total > 10 else (2 if total > 5 else 1)  # 使用范围
        
        total_score = durability + impact + scope
        verdict = "🚀 晋升为规则" if total_score >= 6 else "📝 保留为经验"
        
        print(f"📊 自动评分: {skill_id}")
        print(f"   Durability: {durability}/3 (使用{total}次)")
        print(f"   Impact: {impact}/3 (失败{f_count}次)")
        print(f"   Scope: {scope}/3")
        print(f"   总分: {total_score}/9 → {verdict}")
        
        if total_score >= 6:
            print(f"\n   💡 建议写入 iteration-rules.md:")
            print(f"   reflect.sh resolve {skill_id} '<根因>' '<规则>'")
        break
else:
    print(f"⚠️ Skill {skill_id} not found")
PYEOF
}

# 用法提示
if [ "${1:-}" = "score" ] && [ -n "${2:-}" ]; then
    score_experience "$2"
elif [ "${1:-}" = "auto-score" ] && [ -n "${2:-}" ]; then
    auto_score "$2"
fi
