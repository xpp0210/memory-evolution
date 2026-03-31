#!/bin/bash
set -e

SKILL_DIR="$(cd "$(dirname "$0")/.." && pwd)"
WORKSPACE="${OPENCLAW_WORKSPACE:-$HOME/.openclaw/workspace}"
MEMORY_DIR="$WORKSPACE/memory"

echo "Memory Evolution Skill - Initialize"
echo "====================================="
echo "Skill dir:  $SKILL_DIR"
echo "Workspace:  $WORKSPACE"
echo ""

# 1. Create memory dir
mkdir -p "$MEMORY_DIR"

# 2. Copy memory-skills.json if not exists
if [ ! -f "$MEMORY_DIR/memory-skills.json" ]; then
    cp "$SKILL_DIR/templates/memory-skills.json" "$MEMORY_DIR/memory-skills.json"
    echo "[OK] Created memory-skills.json"
else
    echo "[SKIP] memory-skills.json already exists"
fi

# 3. Copy iteration-rules.md if not exists
if [ ! -f "$MEMORY_DIR/iteration-rules.md" ]; then
    cp "$SKILL_DIR/templates/iteration-rules.md" "$MEMORY_DIR/iteration-rules.md"
    echo "[OK] Created iteration-rules.md"
else
    echo "[SKIP] iteration-rules.md already exists"
fi

# 4. Append to AGENTS.md
AGENTS_FILE="$WORKSPACE/AGENTS.md"
MARKER="<!-- memory-evolution-skill -->"
if [ -f "$AGENTS_FILE" ] && ! grep -q "$MARKER" "$AGENTS_FILE"; then
    echo "" >> "$AGENTS_FILE"
    echo "$MARKER" >> "$AGENTS_FILE"
    cat "$SKILL_DIR/templates/agents-additions.md" >> "$AGENTS_FILE"
    echo "<!-- /memory-evolution-skill -->" >> "$AGENTS_FILE"
    echo "[OK] Appended to AGENTS.md"
else
    echo "[SKIP] AGENTS.md already contains memory-evolution sections"
fi

echo ""
echo "Done! Next steps:"
echo "  1. Review and customize memory-skills.json for your use case"
echo "  2. Add weekly skill review to HEARTBEAT.md"
echo "  3. Restart gateway: openclaw gateway restart"
