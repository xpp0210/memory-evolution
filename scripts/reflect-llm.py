#!/usr/bin/env python3
"""
reflect-llm.py - LLM 驱动的智能反思引擎 (v5.0)

替代 reflect.sh 的固定规则引擎，用 LLM 判断：
- 任务类型分类（新任务/重复/失败/成功）
- 智能归因分析（root cause）
- 进化策略推荐（CAPTURED/FIX/DERIVED/经验模式）

Usage:
    python3 scripts/reflect-llm.py reflect --task "任务描述" --status success --skill "skill_id"
    python3 scripts/reflect-llm.py attribute --task "任务描述" --error "错误信息"
    python3 scripts/reflect-llm.py classify --task "任务描述"
    python3 scripts/reflect-llm.py decay  # Ebbinghaus衰减检查
"""

import sys
import os
import json
import argparse
from pathlib import Path
from datetime import datetime, timedelta

# 添加当前目录到 path
sys.path.insert(0, str(Path(__file__).parent))

from llm_utils import call_llm_json, call_llm

WORKSPACE = Path.home() / ".openclaw/workspace"
MEMORY_DIR = WORKSPACE / "memory"
SKILL_BANK = MEMORY_DIR / "skill-bank"
CAPABILITY_MAP = MEMORY_DIR / "capability-map.json"
ITERATION_RULES = MEMORY_DIR / "iteration-rules.md"


def classify_task(task_desc: str) -> dict:
    """LLM 判断任务类型"""
    prompt = f"""分析以下任务描述，判断任务类型。

任务: {task_desc}

返回JSON:
{{
  "type": "new|repeated|failed|success",
  "category": "error-debug|deep-research|tool-install|doc-creation|code-dev|daily-ops|learning-extract|self-evolve",
  "confidence": 0.0-1.0,
  "reasoning": "简短说明"
}}"""
    return call_llm_json(prompt, system="你是任务分类器。只返回JSON。")


def attribute_failure(task_desc: str, error_info: str) -> dict:
    """LLM 归因分析（失败任务的 root cause）"""
    # 加载能力图谱中的历史失败
    history = ""
    if CAPABILITY_MAP.exists():
        try:
            with open(CAPABILITY_MAP) as f:
                cap = json.load(f)
            failures = [s for s in cap.get("skills", []) if s.get("fail_count", 0) > 0]
            if failures:
                history = f"\n历史失败模式:\n{json.dumps(failures[:5], ensure_ascii=False, indent=2)}"
        except Exception:
            pass

    # 加载迭代规则
    rules = ""
    if ITERATION_RULES.exists():
        try:
            rules = ITERATION_RULES.read_text()[:1000]
        except Exception:
            pass

    prompt = f"""分析以下任务失败的根本原因。

任务: {task_desc}
错误信息: {error_info}
{history}

已有迭代规则:
{rules}

返回JSON:
{{
  "root_cause": "根本原因",
  "error_type": "config|network|permission|logic|resource|timeout|unknown",
  "fix_suggestion": "具体修复建议",
  "rule_candidate": "如果发现新规律，写出一条迭代规则（否则null）",
  "related_skill": "相关的skill_id（如果适用）",
  "severity": "low|medium|high|critical"
}}"""
    return call_llm_json(prompt, system="你是根因分析专家。只返回JSON。")


def reflect_task(task_desc: str, status: str, skill_id: str = "") -> dict:
    """LLM 反思：评估任务并推荐进化策略"""
    # 读取相关 skill 信息
    skill_info = ""
    if skill_id:
        skill_file = SKILL_BANK / f"{skill_id}.json"
        if skill_file.exists():
            try:
                skill_info = skill_file.read_text()[:500]
            except Exception:
                pass

    prompt = f"""反思以下任务执行情况，推荐进化策略。

任务: {task_desc}
执行状态: {status}
Skill: {skill_id or '未指定'}
{f'Skill信息: {skill_info}' if skill_info else ''}

返回JSON:
{{
  "assessment": "简短评估（1-2句）",
  "strategy": "CAPTURED|FIX|DERIVED|EXPERIENCE|SKIP",
  "strategy_reason": "选择该策略的原因",
  "skill_action": "create|update|skip",
  "skill_id": "推荐的目标skill_id",
  "learnings": ["关键学习点1", "关键学习点2"],
  "confidence": 0.0-1.0,
  "next_step": "下一步建议"
}}

策略说明:
- CAPTURED: 新能力捕获，需要创建新 skill
- FIX: 修复失败，需要更新现有 skill
- DERIVED: 从已有技能衍生新变体
- EXPERIENCE: 提取经验模式
- SKIP: 无需进化"""
    return call_llm_json(prompt, system="你是反思引擎。只返回JSON。")


def check_decay() -> dict:
    """Ebbinghaus 衰减检查（兼容 v4.0 reflect.sh decay）"""
    now = datetime.now()
    results = {"checked": 0, "decayed": 0, "rules_pruned": 0, "details": []}

    # 检查 skill-bank 中的衰减
    if SKILL_BANK.exists():
        for f in SKILL_BANK.glob("*.json"):
            try:
                data = json.loads(f.read_text())
                last_used = data.get("last_used", "")
                if last_used:
                    last_dt = datetime.fromisoformat(last_used)
                    days_since = (now - last_dt).days
                    # Ebbinghaus: 半衰期14天
                    retention = pow(2, -days_since / 14)
                    data["retention"] = round(retention, 3)
                    if retention < 0.3:
                        results["decayed"] += 1
                        results["details"].append(f"{f.stem}: {days_since}天未用, 保留率{retention:.1%}")
                    # 写回
                    f.write_text(json.dumps(data, ensure_ascii=False, indent=2))
                results["checked"] += 1
            except Exception:
                pass

    return results


def main():
    parser = argparse.ArgumentParser(description="LLM 驱动的智能反思引擎")
    sub = parser.add_subparsers(dest="command")

    # reflect
    p_reflect = sub.add_parser("reflect", help="反思任务")
    p_reflect.add_argument("--task", required=True, help="任务描述")
    p_reflect.add_argument("--status", default="success", help="任务状态")
    p_reflect.add_argument("--skill", default="", help="skill_id")

    # attribute
    p_attr = sub.add_parser("attribute", help="归因分析")
    p_attr.add_argument("--task", required=True, help="任务描述")
    p_attr.add_argument("--error", required=True, help="错误信息")

    # classify
    p_class = sub.add_parser("classify", help="任务分类")
    p_class.add_argument("--task", required=True, help="任务描述")

    # decay
    sub.add_parser("decay", help="Ebbinghaus衰减检查")

    args = parser.parse_args()

    if args.command == "reflect":
        result = reflect_task(args.task, args.status, args.skill)
    elif args.command == "attribute":
        result = attribute_failure(args.task, args.error)
    elif args.command == "classify":
        result = classify_task(args.task)
    elif args.command == "decay":
        result = check_decay()
    else:
        parser.print_help()
        return

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
