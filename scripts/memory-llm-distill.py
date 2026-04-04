#!/usr/bin/env python3
"""
memory-llm-distill.py - LLM 驱动的知识蒸馏引擎 (v5.0)

升级 night-consolidate.py，用 LLM 做知识蒸馏：
- 从日常日志中提取核心知识
- 去重和语义合并
- 生成结构化知识条目
- 写入 knowledge/ 目录

Usage:
    python3 scripts/memory-llm-distill.py distill --source memory/2026-04-04.md
    python3 scripts/memory-llm-distill.py distill-all  # 蒸馏所有未处理日志
    python3 scripts/memory-llm-distill.py consolidate  # 整合到 MEMORY.md
    python3 scripts/memory-llm-distill.py status       # 查看蒸馏状态
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
KNOWLEDGE_DIR = MEMORY_DIR / "knowledge"
DISTILL_LOG = MEMORY_DIR / "distill-log.json"


def _load_distill_log() -> dict:
    """加载蒸馏日志"""
    if DISTILL_LOG.exists():
        try:
            return json.loads(DISTILL_LOG.read_text())
        except Exception:
            pass
    return {"processed": [], "distilled": 0, "last_run": ""}


def _save_distill_log(log: dict):
    """保存蒸馏日志"""
    DISTILL_LOG.parent.mkdir(parents=True, exist_ok=True)
    log["last_run"] = datetime.now().isoformat()
    DISTILL_LOG.write_text(json.dumps(log, ensure_ascii=False, indent=2))


def distill_file(source_path: str) -> dict:
    """LLM 蒸馏单个日志文件"""
    source = Path(source_path)
    if not source.exists():
        return {"error": f"文件不存在: {source_path}"}

    content = source.read_text()
    if not content.strip():
        return {"error": "文件为空"}

    # 检查是否已处理
    log = _load_distill_log()
    if source.name in log["processed"]:
        return {"status": "already_processed", "file": source.name}

    prompt = f"""从以下日志中蒸馏核心知识。

日志内容（{len(content)} 字符）:
{content[:8000]}

提取以下类型的知识：
1. 决策及理由（做了什么选择，为什么）
2. 技术事实（数据、配置、命令、路径）
3. 经验教训（什么有效、什么失败）
4. 待办事项（未完成的任务）
5. 工作流偏好（工具使用模式、格式偏好）

返回JSON:
{{
  "decisions": [
    {{"decision": "决定内容", "reason": "原因", "impact": "影响"}}
  ],
  "tech_facts": [
    {{"fact": "事实", "category": "config|tool|api|path|command", "detail": "详细说明"}}
  ],
  "lessons": [
    {{"lesson": "经验", "type": "success|failure|insight", "context": "上下文"}}
  ],
  "todos": [
    {{"task": "待办内容", "priority": "high|medium|low", "blocked_by": "阻塞项"}}
  ],
  "preferences": [
    {{"preference": "偏好", "category": "tool|format|workflow|communication"}}
  ],
  "summary": "一句话总结这天的主要内容",
  "key_metrics": {{"lines": 0, "decisions": 0, "facts": 0, "lessons": 0}}
}}"""
    result = call_llm_json(
        prompt,
        system="你是知识蒸馏引擎。从日志中提取结构化知识。只返回JSON。",
        max_tokens=3000
    )

    if result:
        # 写入 knowledge/ 目录
        KNOWLEDGE_DIR.mkdir(parents=True, exist_ok=True)
        date_stem = source.stem  # e.g., 2026-04-04
        output_path = KNOWLEDGE_DIR / f"{date_stem}-distilled.json"
        output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2))

        # 更新蒸馏日志
        log["processed"].append(source.name)
        log["distilled"] = log.get("distilled", 0) + 1
        _save_distill_log(log)

        result["_output"] = str(output_path)

    return result or {"error": "LLM 蒸馏失败"}


def distill_all() -> dict:
    """蒸馏所有未处理的日志"""
    log = _load_distill_log()
    processed = set(log.get("processed", []))

    # 扫描所有日志文件
    candidates = []
    for pattern in ["2026-*.md"]:
        for f in MEMORY_DIR.glob(pattern):
            if f.name not in processed and not f.name.startswith("."):
                candidates.append(f)

    if not candidates:
        return {"status": "no_new_files", "total_processed": log.get("distilled", 0)}

    results = {"processed": 0, "failed": 0, "files": []}
    for f in sorted(candidates):
        r = distill_file(str(f))
        if "error" not in r:
            results["processed"] += 1
        else:
            results["failed"] += 1
        results["files"].append({"file": f.name, "status": "ok" if "error" not in r else r["error"]})

    return results


def consolidate() -> dict:
    """LLM 整合蒸馏结果到 MEMORY.md"""
    memory_file = WORKSPACE / "MEMORY.md"
    if not memory_file.exists():
        return {"error": "MEMORY.md 不存在"}

    memory_content = memory_file.read_text()

    # 收集所有蒸馏结果
    distilled = []
    if KNOWLEDGE_DIR.exists():
        for f in KNOWLEDGE_DIR.glob("*-distilled.json"):
            try:
                d = json.loads(f.read_text())
                d["_source"] = f.stem
                distilled.append(d)
            except Exception:
                pass

    if not distilled:
        return {"status": "no_distilled_data"}

    # 提取关键决策和事实
    decisions = []
    facts = []
    lessons = []
    for d in distilled:
        decisions.extend(d.get("decisions", []))
        facts.extend(d.get("tech_facts", []))
        lessons.extend(d.get("lessons", []))

    prompt = f"""基于以下蒸馏结果，生成 MEMORY.md 需要更新的内容。

当前 MEMORY.md（前2000字符）:
{memory_content[:2000]}

新蒸馏的关键决策 ({len(decisions)} 条):
{json.dumps(decisions[:10], ensure_ascii=False)}

新技术事实 ({len(facts)} 条):
{json.dumps(facts[:10], ensure_ascii=False)}

新经验教训 ({len(lessons)} 条):
{json.dumps(lessons[:10], ensure_ascii=False)}

返回JSON:
{{
  "updates": [
    {{
      "section": "MEMORY.md中的章节名",
      "action": "add|update|replace",
      "content": "要添加/更新的内容（markdown格式）"
    }}
  ],
  "archive_candidates": ["建议归档的旧内容"],
  "new_sections": ["建议新增的章节"],
  "total_lines_change": 0
}}"""
    result = call_llm_json(
        prompt,
        system="你是记忆管理器。生成MEMORY.md的增量更新。只返回JSON。",
        max_tokens=3000
    )

    return result or {"error": "LLM 整合失败"}


def show_status() -> dict:
    """显示蒸馏状态"""
    log = _load_distill_log()

    # 统计
    total_logs = len(list(MEMORY_DIR.glob("2026-*.md")))
    total_distilled = len(list(KNOWLEDGE_DIR.glob("*-distilled.json"))) if KNOWLEDGE_DIR.exists() else 0

    return {
        "total_logs": total_logs,
        "processed": len(log.get("processed", [])),
        "distilled": log.get("distilled", 0),
        "last_run": log.get("last_run", "never"),
        "knowledge_files": total_distilled,
        "pending": total_logs - len(log.get("processed", []))
    }


def main():
    parser = argparse.ArgumentParser(description="LLM 驱动的知识蒸馏引擎")
    sub = parser.add_subparsers(dest="command")

    # distill
    p_distill = sub.add_parser("distill", help="蒸馏单个文件")
    p_distill.add_argument("--source", required=True)

    # distill-all
    sub.add_parser("distill-all", help="蒸馏所有未处理日志")

    # consolidate
    sub.add_parser("consolidate", help="整合到MEMORY.md")

    # status
    sub.add_parser("status", help="查看蒸馏状态")

    args = parser.parse_args()

    if args.command == "distill":
        result = distill_file(args.source)
    elif args.command == "distill-all":
        result = distill_all()
    elif args.command == "consolidate":
        result = consolidate()
    elif args.command == "status":
        result = show_status()
    else:
        parser.print_help()
        return

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
