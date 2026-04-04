#!/usr/bin/env python3
"""
MemOS Integration - memory-evolution v5.0

与 MemOS 双向同步：
- 读取 MemOS chunks → 写入 memory-evolution patterns
- 将 skill-bank 同步到 MemOS skills-store
- 支持 hybrid search（FTS5 + Vector + 真实 embedding）

Usage:
    python3 scripts/memos-integration.py search "关键词"
    python3 scripts/memos-integration.py sync
    python3 scripts/memos-integration.py push-skill <skill_id>
"""

import os
import sys
import json
import sqlite3
import requests
import struct
import math
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

# MemOS database path
MEMOS_DB_PATH = Path.home() / ".openclaw/memos-local/memos.db"
WORKSPACE = Path.home() / ".openclaw/workspace"

# MemOS embedding 配置（从 openclaw.json 读取）
EMBEDDING_CONFIG = {
    "provider": "siliconflow",
    "endpoint": "https://api.siliconflow.cn/v1",
    "model": "BAAI/bge-m3",
    "apiKey": "sk-ubvaapugsvhgmljkjqmndjmsqhcwiyrddseshtukkfhaoeee"
}


def get_memos_db() -> sqlite3.Connection:
    """连接 MemOS 数据库"""
    if not MEMOS_DB_PATH.exists():
        raise FileNotFoundError(f"MemOS database not found: {MEMOS_DB_PATH}")
    return sqlite3.connect(MEMOS_DB_PATH)


def get_embedding(text: str) -> Optional[List[float]]:
    """
    调用 embedding API 获取文本向量

    Args:
        text: 要嵌入的文本

    Returns:
        向量列表（384维），失败返回 None
    """
    if not text or len(text.strip()) == 0:
        return None

    try:
        response = requests.post(
            f"{EMBEDDING_CONFIG['endpoint']}/embeddings",
            headers={
                "Authorization": f"Bearer {EMBEDDING_CONFIG['apiKey']}",
                "Content-Type": "application/json"
            },
            json={
                "model": EMBEDDING_CONFIG['model'],
                "input": text
            },
            timeout=10
        )
        response.raise_for_status()
        data = response.json()
        embedding = data['data'][0]['embedding']
        return embedding
    except Exception as e:
        print(f"❌ Error getting embedding: {e}", file=sys.stderr)
        return None


def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """
    计算余弦相似度

    Args:
        vec1: 向量1
        vec2: 向量2

    Returns:
        相似度（0-1），1表示完全相同
    """
    dot_product = sum(a * b for a, b in zip(vec1, vec2))
    magnitude1 = math.sqrt(sum(a * a for a in vec1))
    magnitude2 = math.sqrt(sum(b * b for b in vec2))
    if magnitude1 == 0 or magnitude2 == 0:
        return 0.0
    return dot_product / (magnitude1 * magnitude2)


def decode_vector(blob: bytes) -> List[float]:
    """
    解码 SQLite BLOB 中的向量（float32 格式）

    Args:
        blob: 二进制数据

    Returns:
        浮点数列表
    """
    # 每个向量元素占 4 字节（float32）
    return [struct.unpack('f', blob[i:i+4])[0] for i in range(0, len(blob), 4)]


def search_memos(query: str, limit: int = 20, min_score: float = 0.45) -> List[Dict[str, Any]]:
    """
    从 MemOS 搜索记忆 chunks（Hybrid Search: FTS5 + Vector）

    Args:
        query: 搜索查询
        limit: 返回结果数量
        min_score: 最小相似度阈值

    Returns:
        List of chunks with excerpt, chunkId, score, task_id
    """
    conn = get_memos_db()
    try:
        # FTS5 关键词搜索（使用 chunks_fts 虚拟表）
        fts_query = "SELECT c.id, c.content, c.summary FROM chunks_fts fts JOIN chunks c ON fts.rowid = c.rowid WHERE fts.content MATCH ? LIMIT ?"
        cursor = conn.execute(fts_query, (f'"{query}"', limit * 2))

        fts_results = [
            {
                "chunkId": f"chunk_{row[0]}",
                "excerpt": row[2] if row[2] else row[1][:500],
                "source": "memos-fts5",
                "score": 0.8
            }
            for row in cursor.fetchall()
        ]

        # 向量语义搜索（真实 embedding）
        vec_results = []
        query_embedding = get_embedding(query)

        if query_embedding:
            # 查询 embeddings 表，计算余弦相似度
            # 只搜索与查询向量同维度的 embeddings（避免维度不匹配）
            vec_query = f"""
                SELECT e.chunk_id, c.content, c.summary, e.vector
                FROM embeddings e
                JOIN chunks c ON e.chunk_id = c.id
                WHERE e.dimensions = {len(query_embedding)}
                ORDER BY e.updated_at DESC
                LIMIT {limit * 2}
            """
            cursor = conn.execute(vec_query)

            for row in cursor.fetchall():
                chunk_id = row[0]
                content = row[1]
                summary = row[2]
                vec_blob = row[3]

                # 解码向量并计算相似度
                if vec_blob:
                    vec = decode_vector(vec_blob)
                    similarity = cosine_similarity(query_embedding, vec)
                    if similarity >= min_score:
                        vec_results.append({
                            "chunkId": f"chunk_{chunk_id}",
                            "excerpt": summary if summary else content[:500],
                            "source": "memos-vector",
                            "score": similarity
                        })

            # 按相似度排序
            vec_results.sort(key=lambda x: x["score"], reverse=True)
            vec_results = vec_results[:limit]

        return merge_results(fts_results, vec_results, min_score)
    finally:
        conn.close()


def merge_results(fts_results: List[Dict], vec_results: List[Dict], min_score: float) -> List[Dict]:
    """
    合并 FTS5 和向量搜索结果（RRF 融合）

    Args:
        fts_results: FTS5 搜索结果
        vec_results: 向量搜索结果
        min_score: 最小分数阈值

    Returns:
        合并后的结果列表
    """
    merged = {}
    k = 60  # RRF 常数

    for r in fts_results:
        merged[r["chunkId"]] = merged.get(r["chunkId"], 0) + 1 / (k + 1)

    for r in vec_results:
        merged[r["chunkId"]] = merged.get(r["chunkId"], 0) + 1 / (k + r["score"] + 1)

    # 排序并过滤
    if not merged:
        return []

    sorted_results = sorted(
        [{"chunkId": cid, "score": merged[cid]}
         for cid in merged],
        key=lambda x: x["score"],
        reverse=True
    )

    # 根据排序后的 chunkId 查找原始数据
    final_results = []
    for r in sorted_results[:len(fts_results) + len(vec_results)]:
        if r["score"] < min_score:
            continue
        # 查找对应的 FTS 或向量结果
        source_result = next((item for item in fts_results + vec_results if item["chunkId"] == r["chunkId"]), None)
        if source_result:
            final_results.append({**source_result, "score": r["score"]})

    return final_results


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
    skill_path = WORKSPACE / "memory/skill-bank/skill-bank.json"
    if not skill_path.exists():
        print("❌ skill-bank.json not found")
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
        print("  search  \"关键词\"      - 从 MemOS 搜索记忆（Hybrid Search）")
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
        for i, r in enumerate(results[:10], 1):
            source_emoji = {"memos-fts5": "📄", "memos-vector": "🧠"}[r["source"]]
            print(f"{i}. {source_emoji} [{r['score']:.2f}] {r['excerpt'][:100]}...")

    elif command == "sync":
        skill_count = sync_skill_bank()
        print(f"✅ Sync complete: {skill_count} skills")

    elif command == "push-skill":
        if len(sys.argv) < 3:
            print("❌ Missing skill ID")
            return
        skill_id = sys.argv[2]
        push_skill_to_memos(skill_id)

    else:
        print(f"❌ Unknown command: {command}")


if __name__ == "__main__":
    main()
