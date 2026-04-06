#!/usr/bin/env python3
"""
阶段1集成测试：验证情绪评估、工作记忆、长期存储三个核心模块的集成
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from biological_memory_engine import BiologicalMemoryEngine, MemoryItem, MemoryContext
import time

def test_basic_integration():
    """测试基本集成"""
    print("=" * 70)
    print("阶段1集成测试：情绪评估 + 工作记忆 + 长期存储")
    print("=" * 70)
    
    # 创建配置
    config = {
        "mode": "balanced",  # 平衡模式
        "modules": {
            "sensory_registration": {"enabled": True},
            "working_memory": {"enabled": True, "capacity": 10},
            "emotional_appraisal": {"enabled": True},
            "consolidation_pruning": {"enabled": False},  # 禁用，简化测试
            "long_term_storage": {"enabled": True},
            "recall_association": {"enabled": False},  # 禁用，简化测试
        },
        "storage_path": os.path.join(os.path.dirname(__file__), "test_memory_store.json"),
    }
    
    # 初始化引擎
    print("1. 初始化生物学记忆引擎...")
    engine = BiologicalMemoryEngine(config)
    
    print(f"   已加载模块: {list(engine.modules.keys())}")
    print(f"   情绪分析器状态: {engine.modules['emotional_appraisal'].has_analyzer}")
    
    # 创建测试记忆
    test_memory = MemoryItem(
        content="量子计算项目取得重大突破！我们成功实现了量子比特的稳定控制。",
        source="test",
        metadata={"user": "齐恒", "project": "量子计算"}
    )
    
    print("2. 处理记忆项...")
    
    # 处理记忆
    context = MemoryContext(
        user_id="test_user",
        session_id="test_session"
    )
    
    result = engine.process_memory(test_memory, context)
    
    if result.success:
        print(f"   [OK] 记忆处理成功")
        print(f"   状态: {result.data.status.value}")
        print(f"   情绪分数: {result.data.emotional_scores}")
        print(f"   重要性: {result.data.importance}")
        print(f"   记忆类型: {result.data.memory_type.value}")
        
        # 检查是否存储到长期存储
        if "long_term_storage" in engine.modules:
            storage_result = engine.modules["long_term_storage"].get_stats()
            print(f"   存储统计: {storage_result.metadata}")
    else:
        print(f"   [ERROR] 记忆处理失败: {result.message}")
    
    # 测试批量记忆
    print("\n3. 测试批量记忆处理...")
    memories = [
        MemoryItem(content="今天天气很好，心情愉快。", source="test"),
        MemoryItem(content="系统出现了一个错误需要修复。", source="test"),
        MemoryItem(content="量子算法设计完成，准备测试。", source="test"),
    ]
    
    success_count = 0
    for mem in memories:
        result = engine.process_memory(mem, context)
        if result.success:
            success_count += 1
    
    print(f"   成功处理 {success_count}/{len(memories)} 个记忆")
    
    # 工作记忆状态
    if "working_memory" in engine.modules:
        wm_result = engine.modules["working_memory"].get_status()
        print(f"   工作记忆状态: {wm_result.metadata}")
    
    # 长期存储统计
    if "long_term_storage" in engine.modules:
        storage_result = engine.modules["long_term_storage"].get_stats()
        print(f"   长期存储统计: {storage_result.metadata}")
    
    print("\n4. 测试记忆检索...")
    
    # 简单检索测试
    query_context = MemoryContext(
        user_id="test_user",
        query="量子计算"
    )
    
    if "recall_association" in engine.modules:
        recall_result = engine.modules["recall_association"].recall(query_context)
        if recall_result.success:
            recalled = recall_result.data
            print(f"   检索到 {len(recalled)} 条相关记忆")
            for i, mem in enumerate(recalled[:3]):
                print(f"     {i+1}. {mem.content[:50]}...")
        else:
            print(f"   检索失败: {recall_result.message}")
    
    print("\n" + "=" * 70)
    print("阶段1集成测试完成")
    print("=" * 70)
    
    # 清理测试文件
    if os.path.exists(config["storage_path"]):
        os.remove(config["storage_path"])
        print(f"清理测试文件: {config['storage_path']}")

if __name__ == "__main__":
    test_basic_integration()