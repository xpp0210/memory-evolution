#!/bin/bash
# reflect.sh — 自进化反思循环执行脚本
# 每次心跳或任务完成后调用，更新 memory-skills.json 的计数器

set -euo pipefail

SKILLS_FILE="$HOME/.openclaw/workspace/memory/memory-skills.json"
RULES_FILE="$HOME/.openclaw/workspace/memory/iteration-rules.md"
DAILY_LOG="$HOME/.openclaw/workspace/memory/$(date +%Y-%m-%d).md"

if [ ! -f "$SKILLS_FILE" ]; then
  echo "❌ memory-skills.json not found"
  exit 1
fi

# Show current stats
echo "=== Memory Skill Bank Status ==="
python3 -c "
import json, sys
with open('$SKILLS_FILE') as f:
    data = json.load(f)
print(f'Version: {data.get(\"version\", \"?\")}')
print(f'Skills: {len(data.get(\"skills\", []))}')
print(f'Reflect entries: {len(data.get(\"reflect_log\", []))}')
print()
for s in data.get('skills', []):
    total = s['success_count'] + s['fail_count']
    rate = f\"{s['success_count']/total*100:.0f}%\" if total else 'N/A'
    status = '⚠️' if s['fail_count'] >= 3 else '✅' if total > 0 else '⏳'
    print(f'  {status} {s[\"id\"]:20s} ✅{s[\"success_count\"]:3d} ❌{s[\"fail_count\"]:3d} ({rate})')
    
# Check for skills needing evolution
needs_evolve = [s for s in data.get('skills', []) if s['fail_count'] >= 3]
if needs_evolve:
    print()
    print('🚨 Skills needing evolution (fail≥3):')
    for s in needs_evolve:
        print(f'  - {s[\"id\"]}: {s[\"fail_count\"]} fails')
"
