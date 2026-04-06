#!/usr/bin/env python3
"""
测试长期存储系统的基本功能
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import numpy as np
from datetime import datetime, timedelta

# 测试 StoreSchema
print("=== 测试 StoreSchema ===")
from long_term_storage import StoreSchema

store_data = StoreSchema.create_empty_store(embedding_dim=768)
valid, msg = StoreSchema.validate_store(store_data)
print(f"创建空存储验证: {valid} - {msg}")
print(f"版本: {store_data['version']}")
print(f"配置: {store_data['config']}")

# 测试 VectorIndexManager（使用numpy模式）
print("\n=== 测试 VectorIndexManager ===")
from long_term_storage import VectorIndexManager

# 临时目录
import tempfile
temp_dir = tempfile.mkdtemp()
print(f"临时目录: {temp_dir}")

# 初始化管理器（强制使用numpy模式）
manager = VectorIndexManager(dimension=768, index_type="numpy", storage_dir=temp_dir)

# 添加向量
test_vector = np.random.rand(768).astype(np.float32)
storage_id = "test_memory_001"
position = manager.add_vector(test_vector, storage_id)
print(f"添加向量位置: {position}")

# 搜索相似
query_vector = np.random.rand(768).astype(np.float32)
results = manager.search_similar(query_vector, top_k=3)
print(f"相似搜索找到 {len(results)} 个结果")
for rid, score in results:
    print(f"  ID: {rid}, 相似度: {score:.3f}")

# 测试 LongTermStorage
print("\n=== 测试 LongTermStorage ===")
from long_term_storage import LongTermStorage

# 创建测试存储
test_storage_dir = os.path.join(temp_dir, "test_storage")
storage = LongTermStorage(
    storage_dir=test_storage_dir,
    embedding_dim=768,
    enable_archive=False  # 简化测试，禁用归档
)

# 创建测试记忆
test_memory = {
    "id": "test_001",
    "fact": "这是一个测试记忆",
    "content": "这是一个测试记忆的内容，用于验证长期存储功能",
    "vec": np.random.rand(768).tolist(),
    "importance": 0.8,
    "type": "knowledge",
    "timestamp": datetime.now().isoformat(),
    "confidence": 0.9,
    "metadata": {
        "emotion": "neutral",
        "keywords": ["测试", "验证"]
    }
}

# 存储记忆
storage_id = storage.store(test_memory)
print(f"存储记忆ID: {storage_id}")

# 加载记忆
loaded = storage.load(storage_id)
print(f"加载记忆: {loaded['id']} - {loaded['fact'][:20]}...")

# 时间范围查询
start_time = datetime.now() - timedelta(days=1)
end_time = datetime.now() + timedelta(days=1)
time_results = storage.load_by_time_range(start_time, end_time)
print(f"时间范围查询结果: {len(time_results)} 条记忆")

# 相似性检索
query_vec = np.random.rand(768)
similar_results = storage.retrieve(query_vec, top_k=2)
print(f"相似性检索结果: {len(similar_results)} 条记忆")
for mem, score in similar_results:
    print(f"  相似度 {score:.3f}: {mem['fact'][:30]}...")

# 获取统计信息
stats = storage.get_stats()
print(f"\n存储统计:")
print(f"  总记忆数: {stats['total_memories']}")
print(f"  活跃记忆: {stats['active_memories']}")
print(f"  归档记忆: {stats['archived_memories']}")
print(f"  内存类型分布: {stats['memory_types']}")

# 保存存储
storage.save()
print(f"\n存储已保存到: {test_storage_dir}")

# 测试适配器
print("\n=== 测试适配器 ===")
from long_term_adapter import LongTermStorageAdapter

# 创建适配器
adapter_dir = os.path.join(temp_dir, "adapter_test")
adapter_base = os.path.join(adapter_dir, "memory_store")
adapter = LongTermStorageAdapter(base_path=adapter_base)

# 测试保存和加载
test_memories = [
    {
        "id": "adapter_test_001",
        "content": "适配器测试记忆1",
        "fact": "适配器测试记忆1",
        "vec": np.random.rand(768).tolist(),
        "importance": 0.7,
        "type": "task",
        "timestamp": datetime.now().isoformat(),
        "confidence": 0.8
    }
]

summary = "# 测试摘要\n这是测试摘要内容"
adapter.save_atomic(test_memories, summary)

loaded_memories = adapter.load()
print(f"适配器加载记忆数: {len(loaded_memories)}")

# 清理
import shutil
try:
    shutil.rmtree(temp_dir)
    print(f"\n清理临时目录: {temp_dir}")
except Exception as e:
    print(f"清理失败: {e}")

print("\n=== 测试完成 ===")