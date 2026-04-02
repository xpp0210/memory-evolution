#!/usr/bin/env python3
"""
skill-feedback.py — Skills自反馈机制（AutoSkill启发）

将reflect.sh的经验记录自动回注到对应SKILL.md中，
让Skills从静态文档变成"活的"——不断从实际使用中学习。

用法：
  skill-feedback.py inject <skill_id>              将最新经验注入SKILL.md
  skill-feedback.py inject-all                      扫描所有skill，注入新经验
  skill-feedback.py status                          查看反馈统计
"""

import sys
import json
import os
import re
from datetime import datetime

BASE = os.path.expanduser("~/.openclaw/workspace")
SKILLS_FILE = os.path.join(BASE, "memory/memory-skills.json")
EXPERIENCE_FILE = os.path.join(BASE, "memory/experience-patterns.md")
RULES_FILE = os.path.join(BASE, "memory/iteration-rules.md")

# Skill directories to search
SKILL_DIRS = [
    os.path.join(BASE, "skills"),
    os.path.expanduser("~/.agents/skills"),
    os.path.expanduser("~/.nvm/versions/node/v22.17.1/lib/node_modules/openclaw/skills"),
    os.path.expanduser("~/.nvm/versions/node/v22.17.1/lib/node_modules/openclaw/dist/extensions"),
]

# Global cache: skill_id_lower → SKILL.md absolute path
_SKILL_INDEX = None

def _build_skill_index():
    """Walk all skill directories and build a complete index of dir_name → SKILL.md path."""
    index = {}
    extra_dirs = [
        os.path.expanduser("~/.openclaw/skills"),
        os.path.expanduser("~/.nvm/versions/node/v22.17.1/lib/node_modules/openclaw/skills"),
    ]
    all_dirs = SKILL_DIRS + extra_dirs
    for base in all_dirs:
        if not os.path.isdir(base):
            continue
        try:
            entries = os.listdir(base)
        except OSError:
            continue
        for entry in entries:
            skill_md = os.path.join(base, entry, "SKILL.md")
            if os.path.isfile(skill_md):
                index[entry.lower()] = skill_md
    return index

def find_skill_md(skill_id):
    """Find SKILL.md file for a skill using dynamic index + fuzzy matching."""
    global _SKILL_INDEX
    if _SKILL_INDEX is None:
        _SKILL_INDEX = _build_skill_index()

    sid = skill_id.lower()

    # 1. Exact match
    if sid in _SKILL_INDEX:
        return _SKILL_INDEX[sid]

    # 2. Manual aliases for known mismatches
    aliases = {
        "deep-research": ["deep-research"],
        "doc-creation": ["feishu-doc", "lark-doc"],
        "tool-install": ["tool-install"],
        "error-debug": ["error-debug"],
        "code-dev": ["coding-agent", "code-dev"],
        "daily-ops": ["daily-ops"],
        "learning-extract": ["learning-extract"],
        "self-evolve": ["memory-evolution", "skill-evolve"],
        "gh-topic-to-article": ["gh-topic-to-article"],
        "feishu-doc": ["feishu-doc", "lark-doc"],
    }
    for alias in aliases.get(sid, []):
        if alias in _SKILL_INDEX:
            return _SKILL_INDEX[alias]

    # 3. Fuzzy: strip common prefixes/suffixes
    for cand in [sid, sid.replace("skill-", ""), "skill-" + sid.lstrip("skill-")]:
        if cand in _SKILL_INDEX:
            return _SKILL_INDEX[cand]

    # 4. Substring match (skill_id contains dir name or vice versa)
    for dir_name, path in _SKILL_INDEX.items():
        if sid in dir_name or dir_name in sid:
            return path

    return None

def get_skill_experiences(skill_id):
    """Get experiences related to a skill"""
    experiences = []
    
    if not os.path.exists(EXPERIENCE_FILE):
        return experiences
    
    with open(EXPERIENCE_FILE) as f:
        content = f.read()
    
    # Find the section for this skill
    section_match = re.search(
        rf"## {re.escape(skill_id)}\n(.*?)(?=\n## |\Z)",
        content, re.DOTALL
    )
    
    if section_match:
        section = section_match.group(1)
        # Extract table rows (patterns)
        for line in section.split("\n"):
            if line.startswith("|") and not line.startswith("| 模式") and not line.startswith("|---"):
                parts = [p.strip() for p in line.split("|")]
                parts = [p for p in parts if p]
                if len(parts) >= 2:
                    experiences.append({
                        "pattern": parts[0],
                        "trigger": parts[1] if len(parts) > 1 else "",
                    })
    
    return experiences

def get_skill_rules(skill_id):
    """Get rules related to a skill"""
    rules = []
    
    if not os.path.exists(RULES_FILE):
        return rules
    
    with open(RULES_FILE) as f:
        content = f.read()
    
    # Simple extraction: find rules mentioning the skill's domain
    for line in content.split("\n"):
        if line.startswith("|") and "✅" in line:
            # It's an active rule
            parts = [p.strip() for p in line.split("|")]
            parts = [p for p in parts if p]
            if len(parts) >= 3:
                rules.append({
                    "problem": parts[1] if len(parts) > 1 else "",
                    "rule": parts[2] if len(parts) > 2 else "",
                })
    
    return rules

def inject_feedback(skill_id):
    """Inject experiences and rules into SKILL.md"""
    skill_md = find_skill_md(skill_id)
    
    if not skill_md:
        return None, f"SKILL.md not found for {skill_id}"
    
    with open(skill_md) as f:
        content = f.read()
    
    # Check if feedback section already exists
    if "## 🔄 实战经验" in content:
        # Update existing section
        pass
    
    experiences = get_skill_experiences(skill_id)
    
    if not experiences:
        return skill_md, f"无新经验可注入 ({skill_id})"
    
    # Build feedback section
    feedback_lines = ["\n## 🔄 实战经验（自动注入）\n"]
    feedback_lines.append(f"> 最近更新：{datetime.now().strftime('%Y-%m-%d')}\n")
    feedback_lines.append("| 模式 | 触发条件 |")
    feedback_lines.append("|------|----------|")
    for exp in experiences:
        feedback_lines.append(f"| {exp['pattern']} | {exp['trigger']} |")
    feedback_lines.append("")
    
    feedback_section = "\n".join(feedback_lines)
    
    if "## 🔄 实战经验" in content:
        # Replace existing feedback section
        content = re.sub(
            r"## 🔄 实战经验.*?(?=\n## |\Z)",
            feedback_section.rstrip(),
            content,
            flags=re.DOTALL
        )
    else:
        # Append before the last section or at the end
        content = content.rstrip() + "\n" + feedback_section
    
    with open(skill_md, "w") as f:
        f.write(content)
    
    return skill_md, f"注入 {len(experiences)} 条经验到 {os.path.basename(os.path.dirname(skill_md))}/SKILL.md"


def cmd_inject(skill_id):
    path, msg = inject_feedback(skill_id)
    if path:
        print(f"✅ {msg}")
        print(f"   文件: {path}")
    else:
        print(f"⚠️ {msg}")


def cmd_inject_all():
    with open(SKILLS_FILE) as f:
        data = json.load(f)
    
    skills = data.get("skills", [])
    print(f"🔄 扫描 {len(skills)} 个Skills...")
    print("=" * 50)
    
    injected = 0
    skipped = 0
    
    for skill in skills:
        sid = skill.get("id", "")
        path, msg = inject_feedback(sid)
        if path:
            print(f"  ✅ {msg}")
            injected += 1
        else:
            skipped += 1
    
    print(f"\n📊 结果: {injected} 注入, {skipped} 跳过")


def cmd_status():
    with open(SKILLS_FILE) as f:
        data = json.load(f)
    
    skills = data.get("skills", [])
    
    print("📊 Skills自反馈统计")
    print("=" * 50)
    
    for skill in skills:
        sid = skill.get("id", "?")
        skill_md = find_skill_md(sid)
        has_feedback = False
        if skill_md:
            with open(skill_md) as f:
                has_feedback = "## 🔄 实战经验" in f.read()
        
        experiences = get_skill_experiences(sid)
        status = "🔄 已注入" if has_feedback else "📝 待注入" if experiences else "— 无经验"
        exp_count = len(experiences)
        
        print(f"  {sid}: {exp_count} 条经验, {status}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(0)
    
    cmd = sys.argv[1]
    
    if cmd == "inject" and len(sys.argv) >= 3:
        cmd_inject(sys.argv[2])
    elif cmd == "inject-all":
        cmd_inject_all()
    elif cmd == "status":
        cmd_status()
    else:
        print(__doc__)
