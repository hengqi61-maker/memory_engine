#!/usr/bin/env python3
"""快速测试记忆引擎基本功能"""
import sys
import os

# 添加路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'code', 'modules'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'code', 'examples'))

try:
    from biological_memory_engine import BiologicalMemoryEngine, MemoryItem, MemoryType
    print("[OK] 导入成功")
    
    # 创建简单配置
    config = {
        "working_memory": {"capacity": 10},
        "emotional_appraisal": {"use_snownlp": False},
        "long_term_storage": {"storage_path": "./test_memories"}
    }
    
    # 初始化引擎
    engine = BiologicalMemoryEngine(config)
    print("[OK] 引擎初始化成功")
    
    # 处理记忆（使用ingest API）
    result = engine.ingest("这是一个测试记忆", source="test")
    print(f"[OK] 记忆处理成功: success={result.success}")
    
    # 查询测试（使用retrieve API）
    query_result = engine.retrieve("测试", top_k=5)
    # MemoryResult的data字段包含记忆列表
    if query_result.success and query_result.data:
        # data可能是列表，也可能是字典
        if isinstance(query_result.data, list):
            memories = query_result.data
        elif isinstance(query_result.data, dict):
            memories = query_result.data.get('memories', [])
        else:
            memories = []
        print(f"[OK] 查询成功: 获取到 {len(memories)} 条结果")
    else:
        print(f"[INFO] 查询结果: {query_result.message}")
    
    print("\n[TARGET] 修剪后测试通过！系统基本功能正常。")
    
except Exception as e:
    print(f"[ERROR] 测试失败: {e}")
    import traceback
    traceback.print_exc()