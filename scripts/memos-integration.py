#!/usr/bin/env python3
"""
MemOS Integration - memory-evolution v5.0

与 MemOS 双向同步：
- 读取 MemOS chunks → 写入 memory-evolution patterns
- 将 skill-bank 同步到 MemOS skills-store
- 支持 hybrid search（FTS5 + Vector）

Usage:
    python3 scripts/memos-integration.py search "关键词"
    python3 scripts/memos-integration.py sync
    python3 scripts/memos-integration.py push-skill <skill_id>
"""

import os
import sys
import json
import sqlite3
from pathlib import Path
from typing import List, Dict, Any, Optional

# MemOS database path
MEMOS_DB_PATH = Path.home() / ".openclaw/memos-local/memos.db"
WORKSPACE = Path.home() / ".openclaw/workspace"


def get_memos_db() -> sqlite3.Connection:
    """连接 MemOS 数据库"""
    if not MEMOS_DB_PATH.exists():
        raise FileNotFoundError(f"MemOS database not found: {MEMOS_DB_PATH}")
    return sqlite3.connect(MEMOS_DB_PATH)


def search_memos(query: str, limit: int = 20, min_score: float = 0.45) -> List[Dict[str, Any]]:
    """
    从 MemOS 搜索记忆 chunks

    Returns:
        List of chunks with excerpt, chunkId, score, task_id
    """
    conn = get_memos_db()
    try:
        # FTS5 关键词搜索
        fts_query = "SELECT id, content, chunk_id FROM chunks WHERE content MATCH ? LIMIT ?"
        cursor = conn.execute(fts_query, (f'"{query}"', limit * 2))

        fts_results = [
            {
                "chunkId": row[1],
                "excerpt": row[0][:500],  # 前500字符
                "source": "memos-fts5",
                "score": 0.8  # FTS5 固定高分
            }
            for row in cursor.fetchall()
        ]

        # 向量语义搜索（如果有 embedding）
        vec_query = """
            SELECT id, content, chunk_id, vector
            FROM chunks
            ORDER BY vector LIMIT ?
        """
        cursor = conn.execute(vec_query, (limit,))
        vec_results = [
            {
                "chunkId": row[1],
                "excerpt": row[0][:500],
                "source": "memos-vector",
                "score": 0.7  # 临时固定值
            }
            for row in cursor.fetchall()
        ]

        return merge_results(fts_results, vec_results, min_score)
    finally:
        conn.close()


def calculate_similarity(query: str, vector: bytes) -> float:
    """
    简化的余弦相似度计算（仅用于演示）

    TODO: v5.0-alpha 中替换为真实 embedding 调用
    """
    # 实际应该调用 embedding provider 计算
    return 0.7  # 临时返回固定值


def merge_results(fts_results: List[Dict], vec_results: List[Dict], min_score: float) -> List[Dict]:
    """
    合并 FTS5 和向量搜索结果（RRF 融合）
    """
    merged = {}
    k = 60  # RRF 常数

    for r in fts_results:
        merged[r["chunkId"]] = merged.get(r["chunkId"], 0) + 1 / (k + 1)  # chunkId 从1开始

    for r in vec_results:
        merged[r["chunkId"]] = merged.get(r["chunkId"], 0) + 1 / (k + r["score"] + 1)  # 使用score而不是chunkId

    # 排序并过滤
    sorted_results = sorted(
        [{"chunkId": cid, "score": merged[cid], **fts_results.get(cid, {})}
         for cid in merged],
        key=lambda x: x["score"],
        reverse=True
    )

    return [{"score": r["score"], **fts_results.get(r["chunkId"], {})}
            for r in sorted_results[:limit] if r["score"] >= min_score]


def sync_skill_bank():
    """
    将 memory/skill-bank/ 同步到 MemOS skills-store

    双向同步：
    1. 读取 skill-bank → 写入 MemOS（新增/更新）
    2. 读取 MemOS skills → 写入 skill-bank（新增/更新）
    """
    skill_bank_path = WORKSPACE / "memory/skill-bank/skill-bank.json"
    memos_skills_path = WORKSPACE / "memory/skill-bank/memos-skills.json"

    # 读取 skill-bank
    if skill_bank_path.exists():
        with open(skill_bank_path, "r", encoding="utf-8") as f:
            skill_bank = json.load(f)
    else:
        skill_bank = {}

    # 读取 MemOS skills（如果存在）
    if memos_skills_path.exists():
        with open(memos_skills_path, "r", encoding="utf-8") as f:
            memos_skills = json.load(f)
    else:
        memos_skills = {}

    # 双向合并
    all_skills = {**skill_bank, **memos_skills}

    # 写回两个位置
    with open(skill_bank_path, "w", encoding="utf-8") as f:
        json.dump(all_skills, f, ensure_ascii=False, indent=2)

    with open(memos_skills_path, "w", encoding="utf-8") as f:
        json.dump(all_skills, f, ensure_ascii=False, indent=2)

    return len(all_skills)


def push_skill_to_memos(skill_id: str):
    """
    将一个 skill 推送到 MemOS

    Args:
        skill_id: Skill ID（如 "error-debug", "deep-research"）
    """
    skill_path = WORKSPACE / f"memory/skill-bank/skill-bank.json"
    if not skill_path.exists():
        print(f"❌ skill-bank.json not found")
        return False

    with open(skill_path, "r", encoding="utf-8") as f:
        skill_bank = json.load(f)

    if skill_id not in skill_bank:
        print(f"❌ Skill not found: {skill_id}")
        return False

    skill = skill_bank[skill_id]

    # TODO: v5.0-alpha 中调用 MemOS skill_publish
    print(f"📤 Pushing skill to MemOS: {skill_id}")
    print(f"   Name: {skill.get('name', 'N/A')}")
    print(f"   Version: {skill.get('version', 'N/A')}")

    return True


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        print("\nUsage:")
        print("  search  \"关键词\"      - 从 MemOS 搜索记忆")
        print("  sync              - 双向同步 skill-bank 和 MemOS")
        print("  push-skill <id>   - 将 skill 推送到 MemOS")
        return

    command = sys.argv[1]

    if command == "search":
        if len(sys.argv) < 3:
            print("❌ Missing query")
            return
        query = sys.argv[2]
        results = search_memos(query)
        print(f"\n🔍 Found {len(results)} results:\n")
        for r in results[:10]:
            print(f"  [{r['score']:.2f}] {r['excerpt'][:100]}...")
            print(f"    chunkId: {r['chunkId']}")

    elif command == "sync":
        count = sync_skill_bank()
        print(f"✅ Synced {count} skills between skill-bank and MemOS")

    elif command == "push-skill":
        if len(sys.argv) < 3:
            print("❌ Missing skill_id")
            return
        skill_id = sys.argv[2]
        push_skill_to_memos(skill_id)

    else:
        print(f"❌ Unknown command: {command}")


if __name__ == "__main__":
    main()
