#!/usr/bin/env python3
"""
阶段1集成测试 - 使用引擎的ingest API
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from biological_memory_engine import BiologicalMemoryEngine

def main():
    print("阶段1集成测试 - 使用 ingest API")
    
    # 配置引擎
    config = {
        "system_name": "TestMemoryEngine",
        "version": "1.0.0",
        "module_configs": {
            "working_memory": {
                "capacity": 10,
                "embedding_backend": "fake"  # 使用简化嵌入
            },
            "long_term_storage": {
                "storage_path": "./test_storage",
                "storage_backend": "json"
            },
            "emotional_appraisal": {
                "enabled": True,
                "analyzer_mode": "hybrid"
            },
            "consolidation_pruning": {
                "enabled": False  # 简化测试
            }
        },
        "pipeline": [
            "sensory_registration",
            "working_memory", 
            "emotional_appraisal",
            "long_term_storage"
        ]
    }
    
    # 初始化引擎
    engine = BiologicalMemoryEngine(config)
    print("引擎初始化完成")
    
    # 测试记忆
    test_content = "量子计算项目取得重大突破！我们成功实现了量子比特的稳定控制，这是一个令人兴奋的进展。"
    
    # 摄入记忆
    result = engine.ingest(
        content=test_content,
        content_type="text",
        source="test"
    )
    
    if result.success:
        memory_item = result.data
        print("[OK] 记忆摄入成功")
        print(f"   记忆ID: {memory_item.id}")
        print(f"   状态: {memory_item.status.value}")
        print(f"   记忆类型: {memory_item.memory_type.value}")
        print(f"   重要性: {memory_item.importance:.3f}")
        
        # 检查情绪分数
        if memory_item.emotional_scores:
            scores = memory_item.emotional_scores
            print(f"   情绪分数:")
            for key, value in scores.items():
                if isinstance(value, (int, float)):
                    print(f"     {key}: {value:.3f}")
                else:
                    print(f"     {key}: {value}")
        else:
            print("   情绪分数: 无")
            
        # 检查工作记忆处理
        if memory_item.working_metadata:
            print(f"   工作记忆元数据: {len(memory_item.working_metadata)} 项")
            
        # 检查存储位置
        if memory_item.storage_location:
            print(f"   存储位置: {memory_item.storage_location}")
            
    else:
        print(f"[ERROR] 记忆摄入失败: {result.message}")
    
    # 测试检索
    print("\n测试检索...")
    query = "量子计算"
    result = engine.retrieve(query, top_k=2)
    
    if result.success:
        memories = result.data if isinstance(result.data, list) else [result.data]
        print(f"检索到 {len(memories)} 条相关记忆:")
        for i, mem in enumerate(memories):
            print(f"  {i+1}. {mem.content[:60]}...")
            if mem.emotional_scores:
                valence = mem.emotional_scores.get('valence', 0)
                arousal = mem.emotional_scores.get('arousal', 0)
                print(f"     愉悦度: {valence:.3f}, 唤醒度: {arousal:.3f}")
    else:
        print(f"检索失败: {result.message}")
    
    # 清理
    if os.path.exists("./test_storage"):
        import shutil
        shutil.rmtree("./test_storage")
        print("\n清理测试存储目录")

if __name__ == "__main__":
    main()