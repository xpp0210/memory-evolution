#!/usr/bin/env python3
"""
skill-llm-evolve.py - LLM 驱动的技能进化引擎 (v5.0)

升级 skill-evolve.py，用 LLM 生成技能变异：
- 分析现有 skill 的优缺点
- 生成改进方案
- 合并相似 skill
- 发现能力缺口

Usage:
    python3 scripts/skill-llm-evolve.py analyze --skill error-debug
    python3 scripts/skill-llm-evolve.py improve --skill error-debug --feedback "经常在代理冲突时失败"
    python3 scripts/skill-llm-evolve.py merge --skills "error-debug,network-debug"
    python3 scripts/skill-llm-evolve.py discover --context "最近的任务历史"
    python3 scripts/skill-llm-evolve.py evolve --skill error-debug --mutation "增加代理环境检测"
"""

import sys
import os
import json
import argparse
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

from llm_utils import call_llm_json, call_llm

WORKSPACE = Path.home() / ".openclaw/workspace"
MEMORY_DIR = WORKSPACE / "memory"
SKILL_BANK = MEMORY_DIR / "skill-bank"
CAPABILITY_MAP = MEMORY_DIR / "capability-map.json"


def _load_skill(skill_id: str) -> dict:
    """加载 skill JSON"""
    skill_file = SKILL_BANK / f"{skill_id}.json"
    if not skill_file.exists():
        return {}
    try:
        return json.loads(skill_file.read_text())
    except Exception:
        return {}


def _save_skill(skill_id: str, data: dict):
    """保存 skill JSON"""
    SKILL_BANK.mkdir(parents=True, exist_ok=True)
    data["updated_at"] = datetime.now().isoformat()
    (SKILL_BANK / f"{skill_id}.json").write_text(
        json.dumps(data, ensure_ascii=False, indent=2)
    )


def analyze_skill(skill_id: str) -> dict:
    """LLM 分析现有 skill 的优缺点"""
    skill = _load_skill(skill_id)
    if not skill:
        return {"error": f"Skill {skill_id} 不存在"}

    prompt = f"""分析以下 skill 的质量和改进空间。

Skill ID: {skill_id}
内容: {json.dumps(skill, ensure_ascii=False)[:2000]}

返回JSON:
{{
  "quality_score": 1-10,
  "strengths": ["优点1", "优点2"],
  "weaknesses": ["弱点1", "弱点2"],
  "suggested_improvements": ["改进1", "改进2"],
  "coverage_gaps": ["覆盖缺口1"],
  "complexity": "low|medium|high",
  "maintainability": "low|medium|high"
}}"""
    return call_llm_json(prompt, system="你是技能质量分析师。只返回JSON。")


def improve_skill(skill_id: str, feedback: str) -> dict:
    """LLM 基于 feedback 生成改进方案"""
    skill = _load_skill(skill_id)
    if not skill:
        return {"error": f"Skill {skill_id} 不存在"}

    prompt = f"""基于反馈改进以下 skill。

Skill ID: {skill_id}
当前内容: {json.dumps(skill, ensure_ascii=False)[:1500]}
用户反馈: {feedback}

返回JSON:
{{
  "improved_steps": ["改进后的步骤1", "步骤2", "步骤3"],
  "changes": ["变更1: 说明", "变更2: 说明"],
  "new_rules": ["新规则1"],
  "risk_assessment": "改进可能带来的风险",
  "version": "建议的新版本号"
}}"""
    return call_llm_json(prompt, system="你是技能改进专家。只返回JSON。")


def merge_skills(skill_ids: list) -> dict:
    """LLM 合并多个相似 skill"""
    skills = {}
    for sid in skill_ids:
        s = _load_skill(sid)
        if s:
            skills[sid] = s

    if len(skills) < 2:
        return {"error": "至少需要2个有效skill才能合并"}

    prompt = f"""合并以下相似 skill 为一个统一的 skill。

Skills: {json.dumps(skills, ensure_ascii=False)[:3000]}

返回JSON:
{{
  "merged_id": "合并后的skill_id",
  "merged_name": "合并后的名称",
  "merged_steps": ["步骤1", "步骤2", "步骤3"],
  "merged_rules": ["规则1", "规则2"],
  "source_skills": {skill_ids},
  "conflicts_resolved": ["解决的冲突1"],
  "merge_rationale": "合并理由"
}}"""
    return call_llm_json(prompt, system="你是技能整合专家。只返回JSON。")


def discover_gaps(context: str = "") -> dict:
    """LLM 发现能力缺口"""
    # 加载当前能力图谱
    existing_skills = []
    if SKILL_BANK.exists():
        existing_skills = [f.stem for f in SKILL_BANK.glob("*.json")]

    capability = ""
    if CAPABILITY_MAP.exists():
        try:
            capability = CAPABILITY_MAP.read_text()[:1000]
        except Exception:
            pass

    prompt = f"""分析当前能力图谱，发现能力缺口。

已有技能: {json.dumps(existing_skills)}
能力图谱: {capability or '无'}
上下文: {context or '基于最近任务历史'}

返回JSON:
{{
  "gaps": [
    {{
      "missing_skill": "缺少的技能",
      "reason": "为什么需要",
      "suggested_id": "建议的skill_id",
      "priority": "high|medium|low",
      "source": "如何获取（搜索GitHub/文档/社区）"
    }}
  ],
  "overlapping": ["可能重叠的skill组"],
  "recommendation": "总体建议"
}}"""
    return call_llm_json(prompt, system="你是能力缺口分析师。只返回JSON。")


def evolve_skill(skill_id: str, mutation: str) -> dict:
    """LLM 对 skill 执行变异进化"""
    skill = _load_skill(skill_id)
    if not skill:
        return {"error": f"Skill {skill_id} 不存在"}

    prompt = f"""对以下 skill 执行变异进化。

Skill ID: {skill_id}
当前内容: {json.dumps(skill, ensure_ascii=False)[:1500]}
变异方向: {mutation}

返回JSON:
{{
  "evolved_steps": ["进化后的步骤1", "步骤2", "步骤3"],
  "mutations_applied": ["变异1: 说明"],
  "backward_compatible": true/false,
  "test_scenarios": ["测试场景1", "测试场景2"],
  "rollback_plan": "回滚方案"
}}"""
    return call_llm_json(prompt, system="你是技能进化引擎。只返回JSON。")


def main():
    parser = argparse.ArgumentParser(description="LLM 驱动的技能进化引擎")
    sub = parser.add_subparsers(dest="command")

    # analyze
    p_analyze = sub.add_parser("analyze", help="分析skill质量")
    p_analyze.add_argument("--skill", required=True)

    # improve
    p_improve = sub.add_parser("improve", help="改进skill")
    p_improve.add_argument("--skill", required=True)
    p_improve.add_argument("--feedback", required=True)

    # merge
    p_merge = sub.add_parser("merge", help="合并skill")
    p_merge.add_argument("--skills", required=True, help="逗号分隔的skill_id")

    # discover
    p_discover = sub.add_parser("discover", help="发现能力缺口")
    p_discover.add_argument("--context", default="")

    # evolve
    p_evolve = sub.add_parser("evolve", help="变异进化")
    p_evolve.add_argument("--skill", required=True)
    p_evolve.add_argument("--mutation", required=True)

    args = parser.parse_args()

    if args.command == "analyze":
        result = analyze_skill(args.skill)
    elif args.command == "improve":
        result = improve_skill(args.skill, args.feedback)
    elif args.command == "merge":
        result = merge_skills(args.skills.split(","))
    elif args.command == "discover":
        result = discover_gaps(args.context)
    elif args.command == "evolve":
        result = evolve_skill(args.skill, args.mutation)
    else:
        parser.print_help()
        return

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
