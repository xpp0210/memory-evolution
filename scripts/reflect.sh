#!/bin/bash
# reflect.sh — 自进化反思循环
# 用法：
#   reflect.sh status                    查看状态
#   reflect.sh record <skill_id> <success|fail> [note]  记录结果
#   reflect.sh evolve                    检查并触发进化

set -euo pipefail

SKILLS_FILE="$HOME/.openclaw/workspace/memory/memory-skills.json"
RULES_FILE="$HOME/.openclaw/workspace/memory/iteration-rules.md"

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
print(f'Version: {data.get(\"version\", \"?\")} | Skills: {len(data.get(\"skills\", []))} | Reflect log: {len(data.get(\"reflect_log\", []))}')
for s in data.get('skills', []):
    total = s['success_count'] + s['fail_count']
    rate = f\"{s['success_count']/total*100:.0f}%\" if total else 'N/A'
    flag = '⚠️' if s['fail_count'] >= 3 else '✅' if total > 0 else '⏳'
    print(f'  {flag} {s[\"id\"]:20s} ✅{s[\"success_count\"]:3d} ❌{s[\"fail_count\"]:3d} ({rate})')
needs = [s for s in data.get('skills', []) if s['fail_count'] >= 3]
if needs:
    print(f'\n🚨 Need evolution: {\", \".join(s[\"id\"] for s in needs)}')
"
    ;;

  record)
    SKILL_ID="${2:-}"
    RESULT="${3:-}"
    NOTE="${4:-}"
    
    if [ -z "$SKILL_ID" ] || [ -z "$RESULT" ]; then
      echo "Usage: reflect.sh record <skill_id> <success|fail> [note]"
      exit 1
    fi
    
    python3 -c "
import json, datetime
with open('$SKILLS_FILE') as f:
    data = json.load(f)
for s in data.get('skills', []):
    if s['id'] == '$SKILL_ID':
        if '$RESULT' == 'success':
            s['success_count'] += 1
        else:
            s['fail_count'] += 1
        data.setdefault('reflect_log', []).append({
            'skill': '$SKILL_ID',
            'result': '$RESULT',
            'note': '''$NOTE''' or '',
            'timestamp': datetime.datetime.now().isoformat()
        })
        break
else:
    print(f'⚠️ Skill $SKILL_ID not found, skipping')
    exit(0)
with open('$SKILLS_FILE', 'w') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
total = s['success_count'] + s['fail_count']
print(f'✅ $SKILL_ID: $RESULT (total: {total}, success_rate: {s[\"success_count\"]/total*100:.0f}%)')
if s['fail_count'] >= 3:
    print(f'🚨 $SKILL_ID fail_count={s[\"fail_count\"]} >= 3, needs evolution!')
"
    ;;

  evolve)
    python3 -c "
import json
with open('$SKILLS_FILE') as f:
    data = json.load(f)
needs = [s for s in data.get('skills', []) if s['fail_count'] >= 3]
if not needs:
    print('✅ No skills need evolution')
    exit(0)
for s in needs:
    print(f'🚨 {s[\"id\"]}: {s[\"fail_count\"]} fails, action={s.get(\"action\",\"?\")}')
    print(f'   reflect_checks: {s.get(\"reflect_checks\", [])}')
    print(f'   → Analyze failure pattern → Update action/memory_focus → Reset counters')
"
    ;;

  *)
    echo "Usage: reflect.sh {status|record|evolve}"
    echo "  status                      Show skill bank status"
    echo "  record <id> <success|fail>  Record task result"
    echo "  evolve                      Check skills needing evolution"
    ;;
esac
