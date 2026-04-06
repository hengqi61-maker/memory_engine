#!/usr/bin/env python3
"""
阶段1简易集成测试 - 测试情绪评估、工作记忆、长期存储
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from biological_memory_engine import BiologicalMemoryEngine, MemoryItem, MemoryContext

def main():
    print("阶段1简易集成测试")
    
    # 配置，只启用核心三个模块
    config = {
        "mode": "balanced",
        "modules": {
            "sensory_registration": {"enabled": True},
            "working_memory": {"enabled": True},
            "emotional_appraisal": {"enabled": True},
            "consolidation_pruning": {"enabled": False},
            "long_term_storage": {"enabled": True},
            "recall_association": {"enabled": False},
        },
        "storage_path": os.path.join(os.path.dirname(__file__), "test_memory.json"),
    }
    
    # 初始化引擎
    engine = BiologicalMemoryEngine(config)
    print("引擎初始化完成")
    
    # 创建测试记忆
    test_memory = MemoryItem(
        content="量子计算项目取得重大突破！我们成功实现了量子比特的稳定控制，这是一个令人兴奋的进展。",
        source="test"
    )
    
    # 创建上下文
    context = MemoryContext(user_id="test_user", session_id="test_session")
    
    # 处理记忆
    result = engine.process_memory(test_memory, context)
    
    if result.success:
        memory = result.data
        print("[OK] 记忆处理成功")
        print(f"   状态: {memory.status.value}")
        print(f"   情绪分数: {memory.emotional_scores}")
        print(f"   重要性: {memory.importance}")
        print(f"   记忆类型: {memory.memory_type.value}")
        print(f"   特征数量: {len(memory.features)}")
        print(f"   嵌入向量长度: {len(memory.embedding) if memory.embedding else '无'}")
        
        # 验证情绪分数是否包含所需字段
        required_fields = ['valence', 'arousal', 'dominance', 'intensity']
        if all(field in memory.emotional_scores for field in required_fields):
            print("[OK] 情绪评分完整")
        else:
            print("[WARNING]️ 情绪评分不完整")
            
        # 验证重要性是否合理
        if 0 <= memory.importance <= 1:
            print(f"[OK] 重要性分数有效: {memory.importance}")
        else:
            print(f"[ERROR] 重要性分数无效: {memory.importance}")
            
    else:
        print(f"[ERROR] 记忆处理失败: {result.message}")
    
    # 清理
    if os.path.exists(config["storage_path"]):
        os.remove(config["storage_path"])
        print("清理测试文件")

if __name__ == "__main__":
    main()