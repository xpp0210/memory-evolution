#!/bin/bash
# reflect.sh v3 — 自进化反思循环（借鉴 AgentEvolver 三大机制）
# 用法：
#   reflect.sh status                           查看状态
#   reflect.sh record <skill_id> <result> [note]  记录结果
#   reflect.sh evolve                            检查并触发进化
#   reflect.sh analyze <skill_id>                对某skill做深度归因分析
#   reflect.sh test <skill_id>                   自动生成测试任务（Self-Questioning）
#
# v3 新增（借鉴 AgentEvolver）：
#   - 失败归因：记录 failure_attribution（哪步错/为什么/怎么改）
#   - 经验摘要：成功时提取可复用 pattern
#   - 自动测试：Self-Questioning 风格的任务生成

set -euo pipefail

SKILLS_FILE="$HOME/.openclaw/workspace/memory/memory-skills.json"
RULES_FILE="$HOME/.openclaw/workspace/memory/iteration-rules.md"
EXPERIENCE_FILE="$HOME/.openclaw/workspace/memory/experience-patterns.md"

if [ ! -f "$SKILLS_FILE" ]; then
  echo "❌ memory-skills.json not found at $SKILLS_FILE"
  exit 1
fi

CMD="${1:-status}"

case "$CMD" in
  status)
    python3 -c "
import json
with open('$SKILLS_FILE') as f:
    data = json.load(f)
skills = data.get('skills', [])
print(f'Version: {data.get(\"version\", \"?\")} | Skills: {len(skills)} | Reflect log: {len(data.get(\"reflect_log\", []))}')
for s in skills:
    status_icon = '✅' if s['fail_count'] == 0 else ('⚠️' if s['fail_count'] < 3 else '🚨')
    print(f'  {status_icon} {s[\"id\"]:<20} ✅  {s[\"success_count\"]:>2} ❌  {s[\"fail_count\"]:>2} ({s[\"success_count\"]/max(s[\"success_count\"]+s[\"fail_count\"],1)*100:.0f}%)')

# Show attribution stats
attribs = [r for r in data.get('reflect_log', []) if r.get('attribution')]
if attribs:
    print(f'\n📊 归因分析记录: {len(attribs)} 条')
    for a in attribs[-3:]:
        print(f'  {a[\"skill\"]}: {a.get(\"attribution\",{}).get(\"root_cause\",\"?\")[:60]}')
"
    ;;

  record)
    SKILL_ID="${2:?Usage: reflect.sh record <skill_id> <success|fail|partial> [note]}"
    RESULT="${3:?Result must be success|fail|partial}"
    NOTE="${4:-}"
    TIMESTAMP=$(date -Iseconds)

    # === 反模式阻断 (Capy Cortex Guardian) ===
    # Check if note contains known dangerous patterns
    DANGEROUS_PATTERNS=(
      "rm -rf /"
      "rm -rf ~"
      "git push --force"
      "DROP TABLE"
      "chmod 777 /"
      ":(){:|:&};:"
      "dd if=/dev/zero"
      "mkfs"
      "> /dev/sda"
    )
    for pat in "${DANGEROUS_PATTERNS[@]}"; do
      if echo "$NOTE" | grep -qi "$pat"; then
        echo "🚫 CORTEX GUARDIAN: 检测到危险模式 '$pat'，已阻断记录"
        echo "   如果这是误判，请使用安全替代命令后重新记录"
        exit 1
      fi
    done

    python3 -c "
import json, sys

skill_id = '$SKILL_ID'
result = '$RESULT'
note = '''$NOTE'''
timestamp = '$TIMESTAMP'

with open('$SKILLS_FILE') as f:
    data = json.load(f)

# Find or create skill
skills = data.get('skills', [])
skill = None
for s in skills:
    if s['id'] == skill_id:
        skill = s
        break

if not skill:
    print(f'⚠️ Skill {skill_id} not found, skipping')
    sys.exit(0)

# Update counters
if result == 'success':
    skill['success_count'] = skill.get('success_count', 0) + 1
elif result in ('fail', 'partial'):
    skill['fail_count'] = skill.get('fail_count', 0) + 1

skill['last_reflect'] = timestamp

# Add to reflect_log
log_entry = {
    'skill': skill_id,
    'result': result,
    'note': note,
    'timestamp': timestamp
}

# v3: ADCA attribution for failures
if result in ('fail', 'partial'):
    log_entry['attribution'] = {
        'status': 'pending',  # pending → analyzed → resolved
        'failure_step': None,  # 哪步出错
        'root_cause': None,    # 根本原因
        'fix_suggestion': None # 建议修复
    }

# v3: Experience pattern for successes
if result == 'success' and skill['success_count'] in (5, 10, 20, 50):
    log_entry['milestone'] = f'success_count={skill[\"success_count\"]}'
    log_entry['pattern_extraction'] = 'pending'

if 'reflect_log' not in data:
    data['reflect_log'] = []
data['reflect_log'].append(log_entry)

with open('$SKILLS_FILE', 'w') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

# Summary
fail_count = skill['fail_count']
success_count = skill['success_count']
total = success_count + fail_count
rate = success_count / max(total, 1) * 100

print(f'{'✅' if result == 'success' else '❌' if result == 'fail' else '⚠️'} {skill_id}: {result} | 累计 {success_count}✅ {fail_count}❌ ({rate:.0f}%)')

if result in ('fail', 'partial') and fail_count >= 3:
    print(f'🚨 {skill_id} fail_count={fail_count} >= 3, 需要进化! 运行 reflect.sh evolve 查看详情')
elif result in ('fail', 'partial'):
    print(f'💡 归因待分析: reflect.sh analyze {skill_id}')

if result == 'success' and skill['success_count'] in (5, 10, 20, 50):
    print(f'🎯 里程碑! success_count={skill[\"success_count\"]}，可提取经验模式')
"
    ;;

  analyze)
    SKILL_ID="${2:?Usage: reflect.sh analyze <skill_id>}"
    python3 -c "
import json

skill_id = '$SKILL_ID'

with open('$SKILLS_FILE') as f:
    data = json.load(f)

# Find skill
skill = None
for s in data.get('skills', []):
    if s['id'] == skill_id:
        skill = s
        break

if not skill:
    print(f'❌ Skill {skill_id} not found')
    exit(1)

# Get pending attributions for this skill
attribs = [r for r in data.get('reflect_log', [])
           if r.get('skill') == skill_id
           and r.get('result') in ('fail', 'partial')
           and r.get('attribution', {}).get('status') == 'pending']

if not attribs:
    print(f'✅ {skill_id} 无待分析归因')
    exit(0)

print(f'🔍 {skill_id} 归因分析（{len(attribs)} 条待处理）')
print('='*60)

for i, a in enumerate(attribs, 1):
    print(f'\n--- 失败 #{i} ---')
    print(f'  时间: {a[\"timestamp\"]}')
    print(f'  备注: {a.get(\"note\", \"无\")}')
    print(f'  状态: {a[\"attribution\"][\"status\"]}')
    print()
    print('  ADCA归因框架（请在后续任务中由LLM填写）:')
    print('  1. failure_step: 任务执行到哪一步失败的？')
    print('  2. root_cause: 根本原因是什么？（工具/网络/理解/格式）')
    print('  3. fix_suggestion: 建议怎么修复？')
    print('  4. rule_candidate: 是否需要写入 iteration-rules.md？')

print()
print('💡 提示：下次任务对话中让安宝分析这些失败，填写归因字段')
print(f'   归因完成后运行: reflect.sh resolve {skill_id}')
"
    ;;

  resolve)
    # 归因分析完成后，标记为 resolved 并可选写入规则
    SKILL_ID="${2:?Usage: reflect.sh resolve <skill_id>}"
    ROOT_CAUSE="${3:-}"
    FIX="${4:-}"

    if [ -n "$ROOT_CAUSE" ]; then
      python3 -c "
import json

skill_id = '$SKILL_ID'
root_cause = '''$ROOT_CAUSE'''
fix = '''$FIX'''

with open('$SKILLS_FILE') as f:
    data = json.load(f)

# Update pending attributions
updated = 0
for r in data.get('reflect_log', []):
    if r.get('skill') == skill_id and r.get('attribution', {}).get('status') == 'pending':
        r['attribution']['status'] = 'analyzed'
        r['attribution']['root_cause'] = root_cause
        r['attribution']['fix_suggestion'] = fix
        updated += 1

with open('$SKILLS_FILE', 'w') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print(f'✅ {skill_id}: {updated} 条归因已更新')
print(f'   根因: {root_cause}')
print(f'   修复: {fix}')

# Reset fail counter if fix applied
for s in data.get('skills', []):
    if s['id'] == skill_id:
        old = s['fail_count']
        s['fail_count'] = 0
        print(f'   fail_count: {old} → 0 (重置)')
        break

with open('$SKILLS_FILE', 'w') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)
"
    fi
    ;;

  evolve)
    python3 -c "
import json
with open('$SKILLS_FILE') as f:
    data = json.load(f)
skills = data.get('skills', [])
needs = [s for s in skills if s['fail_count'] >= 3]
milestones = [s for s in skills if s['success_count'] >= 5 and s['success_count'] % 5 == 0]

if not needs and not milestones:
    print('✅ No skills need evolution or milestone extraction')
    exit(0)

if needs:
    print('🚨 需要进化的 Skills:')
    for s in needs:
        print(f'  {s[\"id\"]}: {s[\"fail_count\"]} fails')
        # Check if there are pending attributions
        pending = [r for r in data.get('reflect_log', [])
                   if r.get('skill') == s['id'] and r.get('attribution', {}).get('status') == 'pending']
        if pending:
            print(f'    → {len(pending)} 条待归因，先运行 reflect.sh analyze {s[\"id\"]}')
        else:
            print(f'    → 无待归因记录，直接根据 reflect_checks 优化')

if milestones:
    print('\n🎯 里程碑 Skills（可提取经验模式）:')
    for s in milestones:
        print(f'  {s[\"id\"]}: {s[\"success_count\"]} 成功')
        print(f'    → 提取可复用 pattern → 写入 experience-patterns.md')
"
    ;;

  test)
    # Self-Questioning: 自动生成测试任务
    SKILL_ID="${2:?Usage: reflect.sh test <skill_id>}"
    python3 -c "
import json

skill_id = '$SKILL_ID'

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

# Get failure history for context
failures = [r for r in data.get('reflect_log', [])
            if r.get('skill') == skill_id and r.get('result') in ('fail', 'partial')]

# Get success patterns
successes = [r for r in data.get('reflect_log', [])
             if r.get('skill') == skill_id and r.get('result') == 'success']

print(f'🧪 Self-Questioning 测试任务生成: {skill_id}')
print('='*60)
print(f'技能: {skill[\"name\"]}')
print(f'触发条件: {skill[\"trigger\"]}')
print(f'执行动作: {skill[\"action\"]}')
print(f'历史: {len(successes)} 成功 / {len(failures)} 失败')
print()
print('生成的测试场景:')
print()

# Generate test scenarios based on skill definition
checks = skill.get('reflect_checks', [])
for i, check in enumerate(checks, 1):
    print(f'  测试 {i}: 验证「{check}」')
    if failures:
        print(f'    → 历史失败模式: {\";\".join(f.get(\"note\",\"\") for f in failures[-2:])}')
    print(f'    → 预期: 执行任务后该检查点应通过')
    print()

# Edge case suggestions
print('边缘场景建议:')
print(f'  - 网络超时情况下的 {skill_id} 行为')
print(f'  - 输入为空或异常时的 {skill_id} 处理')
print(f'  - 并发执行 {skill_id} 的稳定性')
print()
print('💡 将以上测试场景交给安宝执行，结果用 reflect.sh record 记录')
"
    ;;

  decay)
    # 记忆衰减：检查 experience-patterns.md，按 last_used 降权或归档
    EXPERIENCE_FILE="$HOME/.openclaw/workspace/memory/experience-patterns.md"
    ARCHIVE_DIR="$HOME/.openclaw/workspace/memory/archive"
    mkdir -p "$ARCHIVE_DIR"

    if [ ! -f "$EXPERIENCE_FILE" ]; then
      echo "❌ $EXPERIENCE_FILE not found"
      exit 1
    fi

    python3 << 'PYEOF'
import re, datetime, os, shutil, math

exp_file = __import__('os').path.expanduser("~/.openclaw/workspace/memory/experience-patterns.md")
archive_dir = __import__('os').path.expanduser("~/.openclaw/workspace/memory/archive")

with open(exp_file) as f:
    content = f.read()

today = datetime.date.today()

# Find patterns with last_used dates
# Format: | pattern | trigger | apply | success | last_used | weight |
row_pat = re.compile(
    r'^\|\s*(.+?)\s*\|\s*(.+?)\s*\|\s*(\d+)\s*\|\s*(\d+)\s*\|\s*(\d{4}-\d{2}-\d{2})\s*\|\s*(.+?)\s*\|',
    re.MULTILINE
)

# ── Ebbinghaus Exponential Decay ──
# 记忆强度 = e^(-t/S)
# S = 初始稳定性 * (1 + 成功召回次数)
# t = 距上次使用的天数
INITIAL_STABILITY = 7.0  # days — half-life without reinforcement

def memory_strength(days_since_use, success_count):
    """Ebbinghaus exponential decay."""
    S = INITIAL_STABILITY * (1 + success_count)
    return math.exp(-days_since_use / S)

red = []       # strength < 0.3
archive = []   # strength < 0.05
ok = []

for m in row_pat.finditer(content):
    pattern = m.group(1).strip()
    last_used_str = m.group(5).strip()
    success_count = int(m.group(3))
    try:
        last_used = datetime.date.fromisoformat(last_used_str)
    except ValueError:
        continue
    days = (today - last_used).days
    strength = memory_strength(days, success_count)

    if strength < 0.05:
        archive.append((pattern[:50], days, last_used_str, strength))
    elif strength < 0.3:
        red.append((pattern[:50], days, last_used_str, strength))
    else:
        ok.append((pattern[:50], strength))

print("📉 记忆衰减报告 (Ebbinghaus Exponential Decay)")
print("=" * 70)
print(f"扫描日期: {today}")
print(f"公式: strength = e^(-t/S), S = {INITIAL_STABILITY} × (1 + 成功次数)")

if ok:
    ok.sort(key=lambda x: -x[1])
    print(f"\n🟢 活跃经验: {len(ok)} 条")
    for p, s in ok[:5]:
        print(f"  [强度 {s:.2f}] {p}")
    if len(ok) > 5:
        print(f"  ... 还有 {len(ok)-5} 条")

if red:
    print(f"\n🔴 降权 (强度<0.3, {len(red)} 条):")
    for p, d, lu, s in sorted(red, key=lambda x: x[3]):
        print(f"  [强度 {s:.3f} | {d}天] {p} (last: {lu})")

if archive:
    print(f"\n⛔ 建议归档 (强度<0.05, {len(archive)} 条):")
    for p, d, lu, s in sorted(archive, key=lambda x: x[3]):
        print(f"  [强度 {s:.4f} | {d}天] {p} (last: {lu})")
    print(f"\n  归档目录: {archive_dir}")
    print(f"  运行: bash scripts/reflect.sh decay --apply")

if '--apply' in __import__('sys').argv and archive:
    ts = today.isoformat()
    archive_path = os.path.join(archive_dir, f"experience-archive-{ts}.md")
    with open(archive_path, 'w') as af:
        af.write(f"# 经验归档 ({ts})\n\n")
        for p, d, lu, s in archive:
            af.write(f"- [强度 {s:.4f} | {d}天] {p} (last: {lu})\n")
    print(f"\n✅ 已归档 {len(archive)} 条到 {archive_path}")
PYEOF
    ;;

  *)
    echo "reflect.sh v3 — 自进化反思循环"
    echo ""
    echo "用法:"
    echo "  status                           显示技能状态和归因统计"
    echo "  record <id> <result> [note]      记录结果（success|fail|partial）"
    echo "  analyze <id>                     查看待归因的失败记录"
    echo "  resolve <id> <cause> <fix>       标记归因为已分析并重置计数"
    echo "  evolve                           检查需要进化/里程碑的技能"
    echo "  test <id>                        自动生成测试任务（Self-Questioning）"
    echo ""
    echo "v3 新增（借鉴 AgentEvolver）:"
    echo "  - ADCA归因: 失败记录包含 failure_step/root_cause/fix_suggestion"
    echo "  - 里程碑检测: 成功5/10/20/50次时提示提取经验模式"
    echo "  - Self-Questioning: 为技能自动生成测试场景"
    ;;
esac
