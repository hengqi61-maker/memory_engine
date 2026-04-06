#!/usr/bin/env python3
"""
关联检索模块集成示例
将 RecallAssociation 模块集成到 OpenClawMemoryEngine 中
"""

import sys
import os
import time
import json
from datetime import datetime
from typing import List, Dict, Any

# 添加当前目录到路径以便导入
sys.path.insert(0, os.path.dirname(__file__))

def integrate_recall_association_example():
    """演示如何将 RecallAssociation 集成到现有系统中"""
    print("=" * 70)
    print("关联检索模块集成示例")
    print("=" * 70)
    
    # 1. 导入必要的模块
    print("\n[步骤1] 导入模块...")
    try:
        from recall_association import RecallAssociation, RetrievalQuery, ConsolidatedMemory
        print("[OK] RecallAssociation 模块导入成功")
    except ImportError as e:
        print(f"[ERROR] 导入失败: {e}")
        print("请确保 recall_association.py 在当前目录")
        return
    
    # 2. 创建模拟的现有记忆数据（兼容现有格式）
    print("\n[步骤2] 创建模拟记忆数据...")
    mock_memories = create_mock_memories()
    print(f"✓ 创建了 {len(mock_memories)} 条模拟记忆")
    
    # 3. 初始化现有引擎（模拟）
    print("\n[步骤3] 初始化现有 OpenClawMemoryEngine（模拟）...")
    
    class MockOpenClawMemoryEngine:
        """模拟现有记忆引擎用于演示"""
        def __init__(self):
            self.long_term_knowledge = mock_memories
            self.stats = {"memory_count": len(mock_memories)}
            
        def retrieve(self, query_text, top_k=5, query_type=None):
            """原有检索方法（简化版）"""
            # 模拟原有检索逻辑（基于简单向量相似度）
            results = []
            for mem in self.long_term_knowledge[:50]:  # 仅搜索前50条
                # 模拟评分（实际会有更多计算）
                score = 0.5
                if query_type and mem.get('type') == query_type:
                    score = 0.7
                results.append({
                    "fact": mem.get('fact', ''),
                    "score": score,
                    "type": mem.get('type', 'unknown'),
                    "timestamp": mem.get('timestamp', '')
                })
            results.sort(key=lambda x: x['score'], reverse=True)
            return results[:top_k]
    
    old_engine = MockOpenClawMemoryEngine()
    print(f"✓ 模拟引擎初始化完成，包含 {old_engine.stats['memory_count']} 条记忆")
    
    # 4. 初始化关联检索引擎
    print("\n[步骤4] 初始化 RecallAssociation 引擎...")
    recall_engine = RecallAssociation(config={
        "time_decay_alpha": 0.01,
        "enable_caching": True,
        "enable_causal_detection": True,
        "enable_clustering": True,
        "clustering_threshold": 0.7,
        "max_cache_size": 500
    })
    
    # 5. 转换记忆格式并加载到 RecallAssociation
    print("\n[步骤5] 加载记忆到关联检索引擎...")
    consolidated_memories = []
    for mem_dict in mock_memories:
        consolidated = ConsolidatedMemory(
            id=mem_dict.get("id", str(hash(json.dumps(mem_dict)))),
            content=mem_dict.get("fact", ""),
            vec=mem_dict.get("vec", []),
            importance=mem_dict.get("importance", 0.5),
            memory_type=mem_dict.get("type", "log"),
            timestamp=mem_dict.get("timestamp", ""),
            confidence=mem_dict.get("confidence", 1.0),
            emotional_weight=mem_dict.get("emotional_weight", 1.0)
        )
        consolidated_memories.append(consolidated)
    
    recall_engine.update_cache(consolidated_memories)
    print(f"✓ 加载了 {len(consolidated_memories)} 条记忆到关联检索引擎")
    
    # 6. 运行因果检测和主题聚类
    print("\n[步骤6] 运行因果检测和主题聚类...")
    causal_links = recall_engine.detect_causal_relationships(consolidated_memories)
    clusters = recall_engine.cluster_by_theme(consolidated_memories)
    print(f"✓ 检测到 {len(causal_links)} 个因果链接")
    print(f"✓ 创建了 {len(clusters)} 个主题聚类")
    
    # 7. 性能对比测试
    print("\n[步骤7] 性能对比测试...")
    
    test_queries = [
        ("量子计算", "knowledge"),
        ("学习", "knowledge"),
        ("项目", "task"),
        ("编程", "code")
    ]
    
    for query_text, query_type in test_queries:
        print(f"\n  查询: '{query_text}' (类型: {query_type})")
        
        # 旧引擎检索
        start_time = time.time()
        old_results = old_engine.retrieve(query_text, top_k=5, query_type=query_type)
        old_time = time.time() - start_time
        
        # 新引擎检索
        start_time = time.time()
        query = RetrievalQuery(
            query_text=query_text,
            query_type=query_type,
            max_results=5,
            weights={
                "semantic": 0.4,
                "temporal": 0.3,
                "causal": 0.2,
                "emotional": 0.1
            }
        )
        new_results = recall_engine.retrieve_hybrid(query)
        new_time = time.time() - start_time
        
        print(f"  旧引擎: {len(old_results)} 结果, {old_time:.3f} 秒")
        print(f"  新引擎: {len(new_results)} 结果, {new_time:.3f} 秒")
        
        # 显示新引擎的前2个结果
        if new_results:
            print(f"    最佳结果: {new_results[0].memory.content[:60]}...")
            print(f"      综合评分: {new_results[0].total_score:.3f}")
            print(f"      评分组件: {new_results[0].score_components}")
    
    # 8. 高级功能演示
    print("\n[步骤8] 高级功能演示...")
    
    # 8.1 时间邻近性检索
    print("\n  a) 时间邻近性检索:")
    ref_time = datetime.fromisoformat("2026-03-28T11:30:00")
    time_results = recall_engine.retrieve_by_time(ref_time, time_window_hours=6, top_k=3)
    for i, result in enumerate(time_results):
        print(f"    {i+1}. {result.memory.content[:50]}... (时间评分: {result.total_score:.3f})")
    
    # 8.2 因果关系检索
    print("\n  b) 因果关系检索:")
    if causal_links:
        source_id = causal_links[0].source_id
        causal_results = recall_engine.retrieve_by_causality(source_id, max_depth=2, top_k=3)
        for i, result in enumerate(causal_results):
            print(f"    {i+1}. {result.memory.content[:50]}... (因果评分: {result.total_score:.3f})")
    
    # 8.3 批量检索
    print("\n  c) 批量检索演示:")
    batch_queries = [
        RetrievalQuery(query_text="量子", query_type="knowledge", max_results=2),
        RetrievalQuery(query_text="学习", max_results=2),
        RetrievalQuery(query_text="代码", query_type="code", max_results=2)
    ]
    batch_results = recall_engine.batch_retrieve(batch_queries)
    print(f"    批次处理 {len(batch_queries)} 个查询, 共得到 {sum(len(r) for r in batch_results)} 个结果")
    
    # 9. 统计信息
    print("\n[步骤9] 统计信息...")
    stats = recall_engine.get_stats()
    for key, value in sorted(stats.items()):
        if isinstance(value, (int, float)):
            print(f"  {key}: {value}")
    
    # 10. 集成建议
    print("\n[步骤10] 集成建议:")
    print("""
  如何将 RecallAssociation 集成到现有 OpenClawMemoryEngine:
  
  1. 在 __init__ 方法中初始化 RecallAssociation:
     self.recall_engine = RecallAssociation(
         long_term_storage=self.storage,
         emotional_appraisal=self.emotional_appraisal,
         config={...}
     )
  
  2. 修改 retrieve 方法:
     def retrieve(self, query_text, top_k=5, query_type=None):
         query = RetrievalQuery(...)
         results = self.recall_engine.retrieve_hybrid(query)
         # 转换为原格式以保持兼容性
         return convert_to_legacy_format(results)
  
  3. 在睡眠周期中运行因果检测和聚类:
     def sleep_cycle(self):
         # 原有代码...
         self.recall_engine.detect_causal_relationships(memories)
         self.recall_engine.cluster_by_theme(memories)
  
  4. 渐进启用功能:
     - 阶段1: 仅替换检索方法，保持其他功能关闭
     - 阶段2: 启用因果检测
     - 阶段3: 启用主题聚类
     - 阶段4: 启用混合检索权重调整
  """)
    
    print("\n" + "=" * 70)
    print("集成示例完成!")
    print("建议: 在实际集成时，逐步测试每个功能，监控性能变化")
    print("=" * 70)

def create_mock_memories() -> List[Dict[str, Any]]:
    """创建模拟记忆数据（兼容现有格式）"""
    memories = []
    
    # 记忆1-5: 量子计算相关
    quantum_memories = [
        {
            "id": "mem_quantum_1",
            "fact": "因为学习了量子力学的基础概念，所以对量子计算产生了浓厚兴趣。",
            "vec": [0.1 * i for i in range(768)],  # 模拟向量
            "importance": 0.9,
            "type": "knowledge",
            "timestamp": "2026-03-28T09:00:00",
            "confidence": 0.9,
            "emotional_weight": 1.2
        },
        {
            "id": "mem_quantum_2",
            "fact": "量子计算利用量子比特的叠加和纠缠特性，实现指数级加速。",
            "vec": [0.05 * i for i in range(768)],
            "importance": 0.8,
            "type": "knowledge",
            "timestamp": "2026-03-28T10:30:00",
            "confidence": 0.8,
            "emotional_weight": 1.1
        },
        {
            "id": "mem_quantum_3",
            "fact": "今天安装了Qiskit量子计算框架，运行了第一个Hello World程序。",
            "vec": [0.08 * i for i in range(768)],
            "importance": 0.7,
            "type": "task",
            "timestamp": "2026-03-28T11:15:00",
            "confidence": 0.7,
            "emotional_weight": 1.0
        },
        {
            "id": "mem_quantum_4",
            "fact": "量子算法的优势在于解决某些特定问题，如因式分解和数据库搜索。",
            "vec": [0.12 * i for i in range(768)],
            "importance": 0.85,
            "type": "knowledge",
            "timestamp": "2026-03-28T12:00:00",
            "confidence": 0.85,
            "emotional_weight": 1.0
        },
        {
            "id": "mem_quantum_5",
            "fact": "由于量子硬件限制，目前的量子计算机只能运行小规模算法。",
            "vec": [0.09 * i for i in range(768)],
            "importance": 0.75,
            "type": "knowledge",
            "timestamp": "2026-03-28T13:00:00",
            "confidence": 0.75,
            "emotional_weight": 0.9
        }
    ]
    
    # 记忆6-10: 编程相关
    coding_memories = [
        {
            "id": "mem_code_1",
            "fact": "今天优化了Python代码的性能，使用了缓存和向量化操作。",
            "vec": [0.15 * i for i in range(768)],
            "importance": 0.8,
            "type": "code",
            "timestamp": "2026-03-28T14:00:00",
            "confidence": 0.8,
            "emotional_weight": 0.8
        },
        {
            "id": "mem_code_2",
            "fact": "因为内存泄漏问题，所以增加了内存监控和自动清理机制。",
            "vec": [0.13 * i for i in range(768)],
            "importance": 0.7,
            "type": "code",
            "timestamp": "2026-03-28T15:00:00",
            "confidence": 0.7,
            "emotional_weight": 0.9
        },
        {
            "id": "mem_code_3",
            "fact": "学习了新的设计模式，计划在下一个项目中应用工厂模式。",
            "vec": [0.11 * i for i in range(768)],
            "importance": 0.6,
            "type": "knowledge",
            "timestamp": "2026-03-28T16:00:00",
            "confidence": 0.6,
            "emotional_weight": 0.7
        },
        {
            "id": "mem_code_4",
            "fact": "代码重构导致测试失败，因此修复了相关测试用例。",
            "vec": [0.14 * i for i in range(768)],
            "importance": 0.65,
            "type": "code",
            "timestamp": "2026-03-28T17:00:00",
            "confidence": 0.65,
            "emotional_weight": 0.6
        },
        {
            "id": "mem_code_5",
            "fact": "项目部署到生产环境，检查了所有依赖和配置。",
            "vec": [0.16 * i for i in range(768)],
            "importance": 0.9,
            "type": "task",
            "timestamp": "2026-03-28T18:00:00",
            "confidence": 0.9,
            "emotional_weight": 1.2
        }
    ]
    
    # 记忆11-15: 学习相关
    learning_memories = [
        {
            "id": "mem_learn_1",
            "fact": "复习了线性代数的核心概念，包括特征值和特征向量。",
            "vec": [0.07 * i for i in range(768)],
            "importance": 0.7,
            "type": "knowledge",
            "timestamp": "2026-03-28T19:00:00",
            "confidence": 0.7,
            "emotional_weight": 0.8
        },
        {
            "id": "mem_learn_2",
            "fact": "由于理解了概率论，所以能够更好地分析随机算法。",
            "vec": [0.09 * i for i in range(768)],
            "importance": 0.8,
            "type": "knowledge",
            "timestamp": "2026-03-28T20:00:00",
            "confidence": 0.8,
            "emotional_weight": 0.9
        },
        {
            "id": "mem_learn_3",
            "fact": "学习计划：每天花费2小时学习量子计算相关课程。",
            "vec": [0.12 * i for i in range(768)],
            "importance": 0.9,
            "type": "task",
            "timestamp": "2026-03-28T21:00:00",
            "confidence": 0.9,
            "emotional_weight": 1.1
        },
        {
            "id": "mem_learn_4",
            "fact": "参加了线上研讨会，了解了最新的研究进展。",
            "vec": [0.08 * i for i in range(768)],
            "importance": 0.6,
            "type": "knowledge",
            "timestamp": "2026-03-28T22:00:00",
            "confidence": 0.6,
            "emotional_weight": 0.7
        },
        {
            "id": "mem_learn_5",
            "fact": "因为知识缺乏，所以制定了新的学习路线图。",
            "vec": [0.11 * i for i in range(768)],
            "importance": 0.75,
            "type": "task",
            "timestamp": "2026-03-28T23:00:00",
            "confidence": 0.75,
            "emotional_weight": 1.0
        }
    ]
    
    # 组合所有记忆
    memories.extend(quantum_memories)
    memories.extend(coding_memories)
    memories.extend(learning_memories)
    
    # 添加一些随机向量（更真实）
    import random
    random.seed(42)
    for mem in memories:
        # 如果向量是线性递增的，添加一些随机性
        if "vec" in mem and len(mem["vec"]) == 768:
            mem["vec"] = [x + random.uniform(-0.05, 0.05) for x in mem["vec"]]
    
    return memories

if __name__ == "__main__":
    integrate_recall_association_example()