#!/usr/bin/env python3
"""
RecallAssociation 集成补丁
演示如何修改 OpenClawMemoryEngine 以集成关联检索模块
"""

import os
import json
from typing import List, Dict, Any, Optional
from datetime import datetime

# 假设 recall_association 模块可用
try:
    from recall_association import RecallAssociation, RetrievalQuery, ConsolidatedMemory
    IMPORT_SUCCESS = True
except ImportError:
    IMPORT_SUCCESS = False
    print("[警告] recall_association 模块未找到，将使用模拟模式")
    # 提供模拟类以演示接口
    class RecallAssociation:
        def __init__(self, **kwargs):
            self.config = kwargs.get('config', {})
        def retrieve_hybrid(self, query):
            return []
        def detect_causal_relationships(self, memories):
            return []
        def cluster_by_theme(self, memories):
            return {}
        def update_cache(self, memories):
            pass
        def get_stats(self):
            return {}
    
    class RetrievalQuery:
        def __init__(self, **kwargs):
            pass
    
    class ConsolidatedMemory:
        def __init__(self, **kwargs):
            pass

def patch_openclaw_memory_engine(engine_class):
    """
    为 OpenClawMemoryEngine 类打补丁，添加关联检索功能
    
    用法:
        from openclaw_memory_engine_fixed import OpenClawMemoryEngine
        patch_openclaw_memory_engine(OpenClawMemoryEngine)
        engine = OpenClawMemoryEngine(...)
        engine.retrieve_enhanced(...)  # 新方法
    """
    
    original_init = engine_class.__init__
    original_retrieve = getattr(engine_class, 'retrieve', None)
    
    def new_init(self, *args, **kwargs):
        # 调用原始初始化
        original_init(self, *args, **kwargs)
        
        # 初始化关联检索引擎
        self.recall_config = {
            "time_decay_alpha": 0.01,
            "enable_caching": True,
            "enable_causal_detection": True,
            "enable_clustering": True,
            "clustering_threshold": 0.7,
            "default_weights": {
                "semantic": 0.4,
                "temporal": 0.3,
                "causal": 0.2,
                "emotional": 0.1
            }
        }
        
        # 合并用户配置
        if 'recall_config' in kwargs:
            self.recall_config.update(kwargs['recall_config'])
        
        # 创建关联检索引擎
        self.recall_engine = RecallAssociation(
            config=self.recall_config
        )
        
        # 标记是否已加载记忆
        self.recall_memories_loaded = False
        
        print("[关联检索] 关联检索引擎初始化完成")
    
    def load_memories_to_recall_engine(self):
        """将现有记忆加载到关联检索引擎"""
        if self.recall_memories_loaded:
            return True
        
        if not hasattr(self, 'recall_engine'):
            print("[警告] 关联检索引擎未初始化")
            return False
        
        try:
            # 转换现有记忆格式
            consolidated_memories = []
            for mem_dict in self.long_term_knowledge:
                # 确保记忆有向量
                vec = mem_dict.get('vec', [])
                if not vec:
                    # 如果没有向量，尝试生成伪向量
                    import numpy as np
                    import hashlib
                    text = mem_dict.get('fact', mem_dict.get('content', ''))
                    h = hashlib.sha256(text.encode()).hexdigest()
                    seed = int(h[:8], 16) % 10000
                    np.random.seed(seed)
                    vec = (np.random.rand(768) - 0.5).tolist()
                    mem_dict['vec'] = vec
                
                # 创建 ConsolidatedMemory 对象
                memory = ConsolidatedMemory(
                    id=mem_dict.get('id', str(id(mem_dict))),
                    content=mem_dict.get('fact', mem_dict.get('content', '')),
                    vec=vec,
                    importance=mem_dict.get('importance', 0.5),
                    memory_type=mem_dict.get('type', 'log'),
                    timestamp=mem_dict.get('timestamp', datetime.now().isoformat()),
                    confidence=mem_dict.get('confidence', 1.0),
                    emotional_weight=mem_dict.get('emotional_weight', 1.0)
                )
                consolidated_memories.append(memory)
            
            # 加载到关联检索引擎
            self.recall_engine.update_cache(consolidated_memories)
            self.recall_memories_loaded = True
            
            print(f"[关联检索] 加载了 {len(consolidated_memories)} 条记忆")
            return True
            
        except Exception as e:
            print(f"[关联检索] 加载记忆失败: {e}")
            return False
    
    def retrieve_enhanced(self, query_text, top_k=5, query_type=None, 
                         weights=None, time_decay_alpha=None):
        """
        增强检索方法（支持多维度检索）
        
        Args:
            query_text: 查询文本
            top_k: 返回结果数量
            query_type: 记忆类型过滤
            weights: 各维度权重配置
            time_decay_alpha: 时间衰减系数
            
        Returns:
            与原始 retrieve() 方法兼容的结果格式
        """
        # 确保记忆已加载
        self.load_memories_to_recall_engine()
        
        # 构建检索查询
        query = RetrievalQuery(
            query_text=query_text,
            query_type=query_type,
            max_results=top_k,
            weights=weights or self.recall_config['default_weights'],
            time_decay_alpha=time_decay_alpha or self.recall_config['time_decay_alpha']
        )
        
        # 执行增强检索
        try:
            results = self.recall_engine.retrieve_hybrid(query)
            
            # 转换为原始格式以保持兼容性
            legacy_results = []
            for result in results:
                legacy_results.append({
                    "fact": result.memory.content,
                    "score": result.total_score,
                    "similarity": result.score_components.get('semantic', 0),
                    "type": result.memory.memory_type,
                    "timestamp": result.memory.timestamp,
                    "confidence": result.memory.confidence,
                    "explanation": result.explanation
                })
            
            return legacy_results
            
        except Exception as e:
            print(f"[关联检索] 增强检索失败: {e}")
            # 降级到原始检索方法
            if original_retrieve:
                return original_retrieve(self, query_text, top_k, query_type)
            return []
    
    def detect_causal_links(self):
        """检测记忆之间的因果关系"""
        self.load_memories_to_recall_engine()
        
        # 获取所有记忆
        memories = []
        for mem_dict in self.long_term_knowledge:
            memory = ConsolidatedMemory(
                id=mem_dict.get('id', str(id(mem_dict))),
                content=mem_dict.get('fact', mem_dict.get('content', '')),
                vec=mem_dict.get('vec', []),
                memory_type=mem_dict.get('type', 'log')
            )
            memories.append(memory)
        
        # 检测因果关系
        causal_links = self.recall_engine.detect_causal_relationships(memories)
        
        print(f"[关联检索] 检测到 {len(causal_links)} 个因果链接")
        return causal_links
    
    def cluster_memories(self):
        """聚类记忆主题"""
        self.load_memories_to_recall_engine()
        
        # 获取所有记忆
        memories = []
        for mem_dict in self.long_term_knowledge:
            memory = ConsolidatedMemory(
                id=mem_dict.get('id', str(id(mem_dict))),
                content=mem_dict.get('fact', mem_dict.get('content', '')),
                vec=mem_dict.get('vec', []),
                memory_type=mem_dict.get('type', 'log')
            )
            memories.append(memory)
        
        # 主题聚类
        clusters = self.recall_engine.cluster_by_theme(memories)
        
        print(f"[关联检索] 创建了 {len(clusters)} 个主题聚类")
        
        # 将聚类信息存储到记忆元数据中
        for cluster_id, cluster in clusters.items():
            for mem_id in cluster.member_ids:
                # 查找对应记忆并更新元数据
                for mem_dict in self.long_term_knowledge:
                    if mem_dict.get('id', '') == mem_id:
                        if 'metadata' not in mem_dict:
                            mem_dict['metadata'] = {}
                        mem_dict['metadata']['theme_cluster'] = cluster_id
                        mem_dict['metadata']['theme_keywords'] = cluster.theme_keywords
                        break
        
        return clusters
    
    def get_recall_stats(self):
        """获取关联检索统计信息"""
        if hasattr(self, 'recall_engine'):
            return self.recall_engine.get_stats()
        return {}
    
    def clear_recall_cache(self):
        """清空关联检索缓存"""
        if hasattr(self, 'recall_engine'):
            self.recall_engine.clear_cache()
            print("[关联检索] 缓存已清空")
    
    # 替换原始方法（可选）
    if original_retrieve:
        def retrieve_with_fallback(self, query_text, top_k=5, query_type=None):
            """带降级的检索方法（自动选择增强或原始检索）"""
            if hasattr(self, 'recall_engine') and self.recall_memories_loaded:
                try:
                    return self.retrieve_enhanced(query_text, top_k, query_type)
                except Exception as e:
                    print(f"[关联检索] 降级到原始检索: {e}")
            
            # 使用原始检索
            return original_retrieve(self, query_text, top_k, query_type)
        
        engine_class.retrieve = retrieve_with_fallback
    
    # 添加新方法
    engine_class.__init__ = new_init
    engine_class.retrieve_enhanced = retrieve_enhanced
    engine_class.detect_causal_links = detect_causal_links
    engine_class.cluster_memories = cluster_memories
    engine_class.get_recall_stats = get_recall_stats
    engine_class.clear_recall_cache = clear_recall_cache
    engine_class.load_memories_to_recall_engine = load_memories_to_recall_engine
    
    return engine_class

def test_patched_engine():
    """测试打补丁后的引擎"""
    print("=" * 60)
    print("RecallAssociation 集成补丁测试")
    print("=" * 60)
    
    # 模拟一个简单的引擎类用于测试
    class TestMemoryEngine:
        def __init__(self, recall_config=None):
            self.long_term_knowledge = [
                {
                    "id": "test_mem_1",
                    "fact": "因为学习了量子计算，所以开始编写量子算法。",
                    "vec": [0.01 * i for i in range(768)],
                    "type": "knowledge",
                    "timestamp": "2026-03-28T10:00:00",
                    "importance": 0.8,
                    "confidence": 0.9
                },
                {
                    "id": "test_mem_2",
                    "fact": "量子算法在特定问题上具有指数级加速优势。",
                    "vec": [0.02 * i for i in range(768)],
                    "type": "knowledge",
                    "timestamp": "2026-03-28T11:00:00",
                    "importance": 0.7,
                    "confidence": 0.8
                },
                {
                    "id": "test_mem_3",
                    "fact": "今天完成了代码重构，提高了可维护性。",
                    "vec": [0.03 * i for i in range(768)],
                    "type": "code",
                    "timestamp": "2026-03-28T12:00:00",
                    "importance": 0.6,
                    "confidence": 0.7
                }
            ]
            
            # 原始检索方法
            def retrieve(self, query_text, top_k=5, query_type=None):
                print(f"[原始检索] 查询: {query_text}, 类型: {query_type}")
                return [{"fact": "测试结果", "score": 0.5}]
            
            self.retrieve = retrieve.__get__(self, TestMemoryEngine)
    
    # 应用补丁
    PatchedEngine = patch_openclaw_memory_engine(TestMemoryEngine)
    
    # 创建实例
    engine = PatchedEngine()
    
    # 测试增强检索
    print("\n[测试1] 增强检索...")
    results = engine.retrieve_enhanced("量子计算", query_type="knowledge", top_k=2)
    print(f"检索到 {len(results)} 条结果")
    for i, res in enumerate(results):
        print(f"  {i+1}. 分数: {res.get('score', 0):.3f}, 内容: {res['fact'][:50]}...")
    
    # 测试因果关系检测
    print("\n[测试2] 因果关系检测...")
    causal_links = engine.detect_causal_links()
    print(f"检测到 {len(causal_links)} 个因果链接")
    
    # 测试主题聚类
    print("\n[测试3] 主题聚类...")
    clusters = engine.cluster_memories()
    print(f"创建了 {len(clusters)} 个主题聚类")
    
    # 测试统计信息
    print("\n[测试4] 统计信息...")
    stats = engine.get_recall_stats()
    print(f"统计: {stats}")
    
    print("\n" + "=" * 60)
    print("补丁测试完成!")
    print("=" * 60)

if __name__ == "__main__":
    test_patched_engine()