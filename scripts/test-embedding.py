#!/usr/bin/env python3
"""Test MemOS embedding integration"""

import sys
import os

# 添加脚本目录到路径
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, script_dir)

# 直接导入模块文件
import importlib.util
spec = importlib.util.spec_from_file_location("memos_integration", os.path.join(script_dir, "memos-integration.py"))
memos_integration = importlib.util.module_from_spec(spec)
spec.loader.exec_module(memos_integration)

get_embedding = memos_integration.get_embedding
search_memos = memos_integration.search_memos

# 测试1: embedding API
print("🧪 Testing embedding API...")
test_text = "记忆进化"
embedding = get_embedding(test_text)

if embedding:
    print(f"✅ Embedding success: {len(embedding)} dimensions")
    print(f"   First 5 values: {embedding[:5]}")
else:
    print("❌ Embedding failed")
    sys.exit(1)

# 测试2: hybrid search
print("\n🔍 Testing hybrid search...")

# 调试：先单独测试 FTS5
print("\n📄 Testing FTS5 only...")
try:
    results_fts = search_memos("记忆进化", limit=5)
    print(f"✅ FTS5 found {len(results_fts)} results")
except Exception as e:
    print(f"❌ FTS5 error: {e}")

results = search_memos("记忆进化", limit=5)
print(f"\n✅ Hybrid search found {len(results)} results:")
for i, r in enumerate(results, 1):
    source_emoji = {"memos-fts5": "📄", "memos-vector": "🧠"}[r["source"]]
    print(f"{i}. {source_emoji} [{r['score']:.2f}] {r['excerpt'][:80]}...")
