#!/usr/bin/env python3
"""
team-evolve.py — 多Agent协作进化协调器 (v5.0 Phase 4)

用法:
  python3 team-evolve.py sync           # 同步团队能力图谱
  python3 team-evolve.py merge-skills    # 合并冲突技能
  python3 team-evolve.py consensus       # 共识学习（投票选最优策略）
  python3 team-evolve.py report          # 生成团队进化报告
"""

import json
import os
import sys
import hashlib
from datetime import datetime
from pathlib import Path

WORKSPACE = Path(os.environ.get("OPENCLAW_WORKSPACE_DIR", 
    Path.home() / ".openclaw" / "workspace"))
MEMORY_DIR = WORKSPACE / "memory"
TEAM_CAP_PATH = MEMORY_DIR / "team-capability-map.json"
SKILL_MERGES_PATH = MEMORY_DIR / "skill-merges.json"
LOCAL_CAP_PATH = MEMORY_DIR / "capability-map.json"


def load_json(path, default=None):
    if path.exists():
        with open(path) as f:
            return json.load(f)
    return default or {}


def save_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def skill_hash(skill_data):
    """Generate content hash for skill dedup."""
    content = json.dumps(skill_data, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(content.encode()).hexdigest()[:12]


def cmd_sync():
    """Sync local capability map into team capability map."""
    local_cap = load_json(LOCAL_CAP_PATH)
    team_cap = load_json(TEAM_CAP_PATH, {"agents": {}, "last_sync": None})
    
    agent_id = os.environ.get("OPENCLAW_AGENT_ID", "main")
    
    # Merge local capabilities into team
    team_cap["agents"][agent_id] = {
        "capabilities": local_cap,
        "last_seen": datetime.now().isoformat(),
        "skill_count": len(local_cap),
    }
    team_cap["last_sync"] = datetime.now().isoformat()
    
    # Compute team-level aggregation
    all_skills = {}
    for aid, data in team_cap["agents"].items():
        for skill, info in data.get("capabilities", {}).items():
            if skill not in all_skills:
                all_skills[skill] = {"agents": [], "max_level": "L0"}
            all_skills[skill]["agents"].append(aid)
            # Keep max level
            levels = ["L0", "L1", "L2", "L3", "L4", "L5"]
            if levels.index(info.get("level", "L0")) > levels.index(all_skills[skill]["max_level"]):
                all_skills[skill]["max_level"] = info["level"]
    
    team_cap["team_skills"] = all_skills
    team_cap["total_skills"] = len(all_skills)
    
    save_json(TEAM_CAP_PATH, team_cap)
    print(f"✅ Synced {len(local_cap)} capabilities for agent '{agent_id}'")
    print(f"   Team total: {len(all_skills)} unique skills across {len(team_cap['agents'])} agents")
    return team_cap


def cmd_merge_skills():
    """Detect and merge conflicting/duplicate skills across agents."""
    team_cap = load_json(TEAM_CAP_PATH)
    merges = load_json(SKILL_MERGES_PATH, {"merges": [], "last_run": None})
    
    team_skills = team_cap.get("team_skills", {})
    conflicts = []
    
    for skill, info in team_skills.items():
        if len(info["agents"]) > 1:
            # Multiple agents have same skill — potential conflict
            conflicts.append({
                "skill": skill,
                "agents": info["agents"],
                "max_level": info["max_level"],
                "needs_merge": True,
            })
    
    if not conflicts:
        print("No conflicts found.")
        merges["last_run"] = datetime.now().isoformat()
        save_json(SKILL_MERGES_PATH, merges)
        return
    
    print(f"Found {len(conflicts)} skills shared by multiple agents:")
    for c in conflicts:
        print(f"  - {c['skill']}: agents={c['agents']}, max_level={c['max_level']}")
    
    # Auto-resolve: keep highest level, merge evidence
    for conflict in conflicts:
        merge_entry = {
            "skill": conflict["skill"],
            "resolved_level": conflict["max_level"],
            "merged_from": conflict["agents"],
            "timestamp": datetime.now().isoformat(),
            "strategy": "max_level",
        }
        merges["merges"].append(merge_entry)
    
    merges["last_run"] = datetime.now().isoformat()
    save_json(SKILL_MERGES_PATH, merges)
    print(f"\n✅ Auto-resolved {len(conflicts)} conflicts (strategy: max_level)")


def cmd_consensus():
    """Consensus learning — vote on best evolution strategy.
    
    Uses local LLM to evaluate strategies when available,
    falls back to simple voting.
    """
    team_cap = load_json(TEAM_CAP_PATH)
    local_cap = load_json(LOCAL_CAP_PATH)
    
    # Identify weak skills (L0-L1) for improvement
    weak_skills = [s for s, info in local_cap.items() 
                   if info.get("level", "L0") in ("L0", "L1")]
    
    # Identify team-unique skills (only one agent has them)
    team_skills = team_cap.get("team_skills", {})
    unique_skills = [s for s, info in team_skills.items() 
                     if len(info.get("agents", [])) == 1]
    
    # Generate strategy recommendations
    strategies = []
    
    if weak_skills:
        strategies.append({
            "id": "strengthen_weak",
            "priority": "HIGH",
            "description": f"Strengthen {len(weak_skills)} weak skills: {', '.join(weak_skills[:5])}",
            "target_skills": weak_skills,
            "action": "practice_and_capture",
        })
    
    if unique_skills:
        strategies.append({
            "id": "share_unique",
            "priority": "MEDIUM", 
            "description": f"Share {len(unique_skills)} unique skills to other agents",
            "target_skills": unique_skills,
            "action": "publish_to_shared",
        })
    
    # Check for gap skills (team doesn't have)
    known_skill_categories = [
        "error-debug", "deep-research", "tool-install", "doc-creation",
        "code-dev", "daily-ops", "learning-extract", "self-evolve",
        "code-review", "testing", "deployment", "monitoring",
    ]
    gaps = [s for s in known_skill_categories if s not in team_skills]
    if gaps:
        strategies.append({
            "id": "fill_gaps",
            "priority": "LOW",
            "description": f"Fill {len(gaps)} capability gaps: {', '.join(gaps)}",
            "target_skills": gaps,
            "action": "learn_new_skill",
        })
    
    print("=== Consensus Report ===")
    print(f"Weak skills: {len(weak_skills)}")
    print(f"Unique skills: {len(unique_skills)}")
    print(f"Gap skills: {len(gaps)}")
    print(f"\nRecommended strategies ({len(strategies)}):")
    for s in strategies:
        print(f"  [{s['priority']}] {s['id']}: {s['description']}")
    
    return {"strategies": strategies, "weak": weak_skills, "unique": unique_skills, "gaps": gaps}


def cmd_report():
    """Generate team evolution report."""
    team_cap = load_json(TEAM_CAP_PATH)
    merges = load_json(SKILL_MERGES_PATH)
    
    agents = team_cap.get("agents", {})
    team_skills = team_cap.get("team_skills", {})
    merge_count = len(merges.get("merges", []))
    
    # Level distribution
    level_dist = {}
    for skill, info in team_skills.items():
        lv = info.get("max_level", "L0")
        level_dist[lv] = level_dist.get(lv, 0) + 1
    
    print("=== Team Evolution Report ===")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"Agents: {len(agents)}")
    print(f"Total skills: {len(team_skills)}")
    print(f"Skill merges: {merge_count}")
    print(f"\nLevel distribution:")
    for lv in ["L0", "L1", "L2", "L3", "L4", "L5"]:
        print(f"  {lv}: {level_dist.get(lv, 0)}")
    
    if agents:
        print(f"\nAgent details:")
        for aid, data in agents.items():
            cap_count = data.get("skill_count", 0)
            last_seen = data.get("last_seen", "unknown")
            print(f"  {aid}: {cap_count} skills, last seen {last_seen[:19]}")


COMMANDS = {
    "sync": cmd_sync,
    "merge-skills": cmd_merge_skills,
    "consensus": cmd_consensus,
    "report": cmd_report,
}

if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in COMMANDS:
        print(f"Usage: {sys.argv[0]} <{'|'.join(COMMANDS.keys())}>")
        sys.exit(1)
    COMMANDS[sys.argv[1]]()
