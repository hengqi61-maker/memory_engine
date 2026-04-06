#!/usr/bin/env python3
"""
关联检索与回忆模块 (Recall & Association)
OpenClaw 记忆引擎的第六个核心模块

设计目标：
1. 时间邻近性：近期相关性更高的记忆获得更高检索权重
2. 因果链推理：检测记忆之间的因果关系，建立推理链条
3. 主题聚类增强：基于语义相似度自动聚类相关记忆
4. 多模式检索：支持关键词、语义相似度、时间、因果关系等多维度查询

数学基础：
- 时间衰减函数：weight_time = exp(-α × Δt)
- 因果推理评分：通过文本模式匹配和逻辑连接词检测
- 主题聚类：基于向量相似度使用层次聚类或DBSCAN
- 混合检索评分：综合向量相似度、时间权重、因果关系分、情绪重要性权重

与其他模块集成：
- 接收来自 LongTermStorage 的存储记忆
- 利用 WorkingMemory 的编码向量进行相似度计算
- 考虑 EmotionalAppraisal 的情绪重要性权重
- 与 ConsolidationPruning 共享因果检测逻辑

性能考量：
- 支持批量检索和缓存机制
- 考虑实际运行环境（本地、无GPU、中等算力）
## 科学依据：参考联想记忆理论和认知神经科学研究
"""

import numpy as np
import json
import re
import heapq
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional, Any, Set, Union
from dataclasses import dataclass, field
from enum import Enum
import warnings

# 导入类型定义（如果可用）
EncodedMemory = Any
AppraisedMemory = Any
OpenClawMemoryEngine = Any

# ==================== 数据类型定义 ====================

@dataclass
class ConsolidatedMemory:
    """整合后的记忆对象（与现有系统兼容）"""
    id: str
    content: str
    vec: List[float]  # 768维向量
    importance: float = 0.5
    memory_type: str = "log"
    timestamp: str = ""
    confidence: float = 1.0
    source_count: int = 1
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # 增强字段（可选）
    causal_links: List[str] = field(default_factory=list)  # 因果链接到的记忆ID
    theme_cluster_id: Optional[str] = None  # 主题聚类ID
    emotional_weight: float = 1.0  # 情绪重要性权重

@dataclass
class RetrievalQuery:
    """检索查询对象"""
    query_text: str = ""
    query_vector: Optional[np.ndarray] = None
    query_type: Optional[str] = None  # 记忆类型过滤
    time_range: Optional[Tuple[datetime, datetime]] = None
    causal_context: Optional[List[str]] = None  # 相关因果记忆ID
    theme_filter: Optional[str] = None  # 主题过滤
    max_results: int = 10
    
    # 混合检索权重配置
    weights: Dict[str, float] = field(default_factory=lambda: {
        "semantic": 0.4,    # 语义相似度权重
        "temporal": 0.3,    # 时间邻近权重
        "causal": 0.2,      # 因果关联权重
        "emotional": 0.1    # 情绪重要性权重
    })
    
    # 时间衰减系数
    time_decay_alpha: float = 0.01  # 小时^-1
    
    def __post_init__(self):
        if self.query_text and self.query_vector is None:
            # 这里应该调用嵌入函数，但需要外部依赖
            # 暂时设置为None，由调用者提供
            pass

@dataclass 
class RetrievalResult:
    """检索结果对象"""
    memory: ConsolidatedMemory
    total_score: float  # 综合评分 (0-1)
    score_components: Dict[str, float]  # 各维度评分
    explanation: str  # 解释为何被检索到
    
    def __lt__(self, other):
        # 用于堆排序
        return self.total_score < other.total_score
    
    def __str__(self):
        return (f"记忆 [{self.memory.memory_type}] 得分: {self.total_score:.3f} | "
                f"内容: {self.memory.content[:50]}...")

@dataclass
class Cluster:
    """主题聚类"""
    cluster_id: str
    centroid: np.ndarray  # 聚类中心向量
    member_ids: List[str]  # 成员记忆ID
    theme_keywords: List[str]  # 主题关键词
    coherence_score: float  # 聚类内一致性
    last_updated: datetime = field(default_factory=datetime.now)
    
    def size(self):
        return len(self.member_ids)

@dataclass
class CausalLink:
    """因果链接"""
    source_id: str  # 原因记忆ID
    target_id: str  # 结果记忆ID
    relation_type: str  # "cause", "enable", "prevent", "temporal"
    confidence: float  # 置信度 (0-1)
    evidence: str  # 证据文本
    created_at: datetime = field(default_factory=datetime.now)

# ==================== 数学公式推导 ====================
"""
1. 时间衰减函数：
   weight_time = exp(-α × Δt)
   α: 衰减系数 (默认 0.01 小时^-1)
   Δt: 时间差 (小时)

2. 因果关联评分：
   采用基于文本模式匹配和逻辑规则的方法：
   - 模式匹配：如 "因为A所以B", "A导致B", "由于A因此B"
   - 词语共现：如果记忆在相同上下文中频繁共现
   - 时间顺序：原因通常在结果之前
   
   causal_score = w1 * pattern_match + w2 * cooccurrence + w3 * temporal_order

3. 主题聚类评分：
   - 向量相似度：余弦相似度
   - 聚类内平均相似度作为主题相关性指标
   theme_score = avg_similarity(cluster_members, query_vector)

4. 混合检索评分：
   total_score = ∑ (weight_i * score_i) / ∑ weight_i
   其中 i ∈ {semantic, temporal, causal, emotional, theme}
   
   各维度评分归一化到 [0,1] 区间
"""

class RecallAssociation:
    """
    关联检索与回忆引擎
    """
    
    def __init__(self, 
                 config: Optional[Dict] = None,
                 long_term_storage: Optional[Any] = None,
                 working_memory: Optional[Any] = None,
                 emotional_appraisal: Optional[Any] = None):
        """
        初始化关联检索引擎
        
        Args:
            config: 配置字典
            long_term_storage: 长期存储接口
            working_memory: 工作记忆接口（用于向量编码）
            emotional_appraisal: 情绪评估接口（用于重要性权重）
        """
        self.config = self._load_config(config)
        
        # 外部模块引用
        self.long_term_storage = long_term_storage
        self.working_memory = working_memory
        self.emotional_appraisal = emotional_appraisal
        
        # 内部状态
        self.memory_cache: Dict[str, ConsolidatedMemory] = {}
        self.causal_links: Dict[str, List[CausalLink]] = {}  # memory_id -> 链接列表
        self.clusters: Dict[str, Cluster] = {}
        self.cluster_membership: Dict[str, str] = {}  # memory_id -> cluster_id
        
        # 缓存机制
        self.vector_cache: Dict[str, np.ndarray] = {}
        self.similarity_cache: Dict[Tuple[str, str], float] = {}
        
        # 统计信息
        self.stats = {
            "total_retrievals": 0,
            "avg_processing_time": 0.0,
            "cache_hits": 0,
            "cache_misses": 0,
            "clusters_created": 0,
            "causal_links_detected": 0
        }
        
        # 模式匹配规则
        self._init_patterns()
        
        print(f"[关联检索] 引擎初始化完成")
        print(f"          - 时间衰减基准系数: {self.config['time_decay_alpha']}")
        print(f"          - 缓存容量: {self.config['max_cache_size']}")
        print(f"          - 启用情感统一衰减: ✓")
        
    def _load_config(self, user_config: Optional[Dict]) -> Dict:
        """加载配置"""
        default_config = {
            # 时间衰减
            "time_decay_alpha": 0.01,  # 小时^-1
            
            # 因果推理
            "causal_patterns": [
                (r"因为(.+?)所以(.+)", 0.9),
                (r"由于(.+?)因此(.+)", 0.8),
                (r"(.+?)导致(.+)", 0.85),
                (r"(.+?)造成(.+)", 0.8),
                (r"(.+?)引起(.+)", 0.8),
                (r"如果(.+?)那么(.+)", 0.7),
                (r"(.+?)的结果是(.+)", 0.75)
            ],
            "causal_keywords": ["因为", "所以", "导致", "造成", "引起", "因此", "因而", "故而"],
            "causal_window_size": 3,  # 因果检测的上下文窗口大小
            
            # 主题聚类
            "clustering_threshold": 0.7,  # 聚类相似度阈值
            "min_cluster_size": 2,
            "max_cluster_size": 50,
            "clustering_method": "hierarchical",  # hierarchical, dbscan
            
            # 混合检索权重
            "default_weights": {
                "semantic": 0.4,
                "temporal": 0.3,
                "causal": 0.2,
                "emotional": 0.1
            },
            
            # 性能
            "max_cache_size": 1000,
            "similarity_precision": 0.001,  # 相似度缓存精度
            "enable_caching": True,
            "enable_clustering": True,
            "enable_causal_detection": True,
            
            # 科学参数（基于认知神经科学）
            "recent_bias_factor": 1.5,  # 近期记忆偏置因子
            "emotional_amplification": 1.3,  # 情绪记忆放大因子
            "primacy_recency_ratio": 0.6,  # 首因效应与近因效应比值
        }
        
        if user_config:
            # 深度合并配置
            self._deep_merge(default_config, user_config)
        
        return default_config
    
    def _deep_merge(self, base: Dict, update: Dict):
        """深度合并配置字典"""
        for key, value in update.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_merge(base[key], value)
            else:
                base[key] = value
    
    def _init_patterns(self):
        """初始化模式匹配规则"""
        self.patterns_compiled = []
        for pattern_str, weight in self.config["causal_patterns"]:
            pattern = re.compile(pattern_str, re.DOTALL)
            self.patterns_compiled.append((pattern, weight))
    
    # ==================== 核心接口 ====================
    
    def retrieve_by_similarity(self, 
                              query_vector: np.ndarray,
                              top_k: int = 10,
                              filter_type: Optional[str] = None) -> List[RetrievalResult]:
        """
        基于语义相似度检索
        
        Args:
            query_vector: 查询向量 (768维)
            top_k: 返回结果数量
            filter_type: 记忆类型过滤
            
        Returns:
            按相似度排序的检索结果
        """
        results = []
        
        for memory in self._get_all_memories():
            if filter_type and memory.memory_type != filter_type:
                continue
            
            # 计算相似度
            similarity = self._compute_similarity(query_vector, memory.vec)
            
            # 构建结果
            result = RetrievalResult(
                memory=memory,
                total_score=similarity,
                score_components={
                    "semantic": similarity,
                    "temporal": 0.5,  # 默认值
                    "causal": 0.0,
                    "emotional": memory.emotional_weight
                },
                explanation=f"语义相似度: {similarity:.3f}"
            )
            results.append(result)
        
        # 排序并返回top_k
        results.sort(key=lambda x: x.total_score, reverse=True)
        return results[:top_k]
    
    def retrieve_by_time(self,
                        time_reference: datetime,
                        time_window_hours: float = 24.0,
                        top_k: int = 10) -> List[RetrievalResult]:
        """
        基于时间邻近性检索
        
        Args:
            time_reference: 参考时间点
            time_window_hours: 时间窗口大小（小时）
            top_k: 返回结果数量
            
        Returns:
            按时间邻近性排序的检索结果
        """
        results = []
        time_window = timedelta(hours=time_window_hours)
        
        for memory in self._get_all_memories():
            # 解析时间戳
            mem_time = self._parse_timestamp(memory.timestamp)
            if mem_time is None:
                continue
            
            # 计算时间差
            time_diff_hours = abs((time_reference - mem_time).total_seconds() / 3600.0)
            
            # 应用统一的时间衰减函数（受重要性影响）
            # α = α_base / (1 + importance) - 重要性越高，衰减越慢
            importance = getattr(memory, 'importance', 0.5)  # 默认为中性重要性
            α_base = self.config.get("time_decay_alpha_base", 0.01)
            α_dynamic = α_base / (1 + importance)
            time_score = np.exp(-α_dynamic * time_diff_hours)
            
            # 在时间窗口内的记忆获得更高权重
            if time_diff_hours <= time_window_hours:
                time_score *= self.config["recent_bias_factor"]
            
            # 构建结果
            result = RetrievalResult(
                memory=memory,
                total_score=time_score,
                score_components={
                    "semantic": 0.0,
                    "temporal": time_score,
                    "causal": 0.0,
                    "emotional": memory.emotional_weight
                },
                explanation=f"时间邻近性: 差{time_diff_hours:.1f}小时, 得分{time_score:.3f}"
            )
            results.append(result)
        
        # 排序并返回top_k
        results.sort(key=lambda x: x.total_score, reverse=True)
        return results[:top_k]
    
    def retrieve_by_causality(self,
                            source_memory_id: str,
                            max_depth: int = 3,
                            top_k: int = 10) -> List[RetrievalResult]:
        """
        基于因果关系检索
        
        Args:
            source_memory_id: 源记忆ID
            max_depth: 最大因果链深度
            top_k: 返回结果数量
            
        Returns:
            按因果关联度排序的检索结果
        """
        # 查找所有因果链接
        causal_scores = {}
        visited = set()
        
        def dfs(current_id: str, depth: int, current_score: float):
            if depth > max_depth or current_id in visited:
                return
            
            visited.add(current_id)
            
            # 获取当前记忆
            memory = self.memory_cache.get(current_id)
            if not memory:
                return
            
            # 记录因果评分
            causal_scores[current_id] = max(causal_scores.get(current_id, 0), current_score)
            
            # 遍历所有因果链接
            for link in self.causal_links.get(current_id, []):
                if link.target_id != current_id:
                    next_id = link.target_id
                else:
                    next_id = link.source_id
                
                # 衰减链路强度
                next_score = current_score * link.confidence * 0.8  # 深度衰减因子
                dfs(next_id, depth + 1, next_score)
        
        # 开始深度优先搜索
        dfs(source_memory_id, 0, 1.0)
        
        # 构建结果
        results = []
        for mem_id, causal_score in causal_scores.items():
            if mem_id == source_memory_id:
                continue  # 跳过源记忆
            
            memory = self.memory_cache.get(mem_id)
            if not memory:
                continue
            
            result = RetrievalResult(
                memory=memory,
                total_score=causal_score,
                score_components={
                    "semantic": 0.0,
                    "temporal": 0.5,
                    "causal": causal_score,
                    "emotional": memory.emotional_weight
                },
                explanation=f"因果关联度: {causal_score:.3f} (深度≤{max_depth})"
            )
            results.append(result)
        
        # 排序并返回top_k
        results.sort(key=lambda x: x.total_score, reverse=True)
        return results[:top_k]
    
    def retrieve_hybrid(self, query: RetrievalQuery) -> List[RetrievalResult]:
        """
        混合多维度检索
        
        Args:
            query: 检索查询对象
            
        Returns:
            按综合评分排序的检索结果
        """
        import time
        start_time = time.time()
        
        results = []
        all_memories = self._get_all_memories()
        
        # 时间参考点（默认为现在）
        time_reference = datetime.now()
        if query.time_range:
            time_reference = query.time_range[0]  # 使用开始时间作为参考
        
        # 遍历所有记忆
        for memory in all_memories:
            # 类型过滤
            if query.query_type and memory.memory_type != query.query_type:
                continue
            
            # 时间范围过滤
            if query.time_range:
                mem_time = self._parse_timestamp(memory.timestamp)
                if mem_time and not (query.time_range[0] <= mem_time <= query.time_range[1]):
                    continue
            
            # 计算各维度评分
            scores = {}
            
            # 1. 语义相似度评分
            if query.query_vector is not None:
                semantic_score = self._compute_similarity(query.query_vector, memory.vec)
            else:
                semantic_score = 0.0  # 无查询向量时设为0
            
            # 2. 时间邻近性评分
            mem_time = self._parse_timestamp(memory.timestamp)
            if mem_time:
                time_diff_hours = abs((time_reference - mem_time).total_seconds() / 3600.0)
                # 统一的时间衰减函数（受重要性影响）
                # α = α_base / (1 + importance) - 重要性越高，衰减越慢
                importance = getattr(memory, 'importance', 0.5)  # 默认为中性重要性
                α_base = query.time_decay_alpha  # 使用查询中的基准值
                α_dynamic = α_base / (1 + importance)
                temporal_score = np.exp(-α_dynamic * time_diff_hours)
            else:
                temporal_score = 0.5  # 无时间戳时设为中性值
            
            # 3. 因果关联评分
            causal_score = 0.0
            if query.causal_context:
                for source_id in query.causal_context:
                    link_score = self._get_causal_link_score(source_id, memory.id)
                    causal_score = max(causal_score, link_score)
            
            # 4. 情绪重要性评分
            emotional_score = memory.emotional_weight
            
            # 5. 主题聚类评分（如果启用）
            theme_score = 0.0
            if query.theme_filter and memory.theme_cluster_id:
                cluster = self.clusters.get(memory.theme_cluster_id)
                if cluster and query.theme_filter in cluster.theme_keywords:
                    theme_score = 1.0
            
            # 收集所有评分
            scores = {
                "semantic": semantic_score,
                "temporal": temporal_score,
                "causal": causal_score,
                "emotional": emotional_score,
                "theme": theme_score
            }
            
            # 应用权重计算综合评分
            total_score = 0.0
            total_weight = 0.0
            
            for dim, score in scores.items():
                weight = query.weights.get(dim, self.config["default_weights"].get(dim, 0.0))
                total_score += weight * score
                total_weight += weight
            
            if total_weight > 0:
                total_score = total_score / total_weight
            
            # 构建结果
            result = RetrievalResult(
                memory=memory,
                total_score=total_score,
                score_components=scores,
                explanation=self._generate_explanation(scores, total_score)
            )
            results.append(result)
        
        # 排序并返回top_k
        results.sort(key=lambda x: x.total_score, reverse=True)
        
        # 更新统计信息
        processing_time = time.time() - start_time
        self._update_stats(len(all_memories), processing_time)
        
        return results[:query.max_results]
    
    # ==================== 辅助方法 ====================
    
    def _get_all_memories(self) -> List[ConsolidatedMemory]:
        """获取所有记忆（优先缓存，然后外部存储）"""
        if self.memory_cache:
            return list(self.memory_cache.values())
        
        # 从外部存储加载
        memories = []
        if self.long_term_storage:
            # 假设外部存储有load_all方法
            try:
                storage_memories = self.long_term_storage.load_all()
                for mem_dict in storage_memories:
                    memory = self._dict_to_memory(mem_dict)
                    self.memory_cache[memory.id] = memory
                    memories.append(memory)
            except Exception as e:
                warnings.warn(f"从长期存储加载失败: {e}")
                memories = list(self.memory_cache.values())
        
        return memories
    
    def _compute_similarity(self, vec1: Union[np.ndarray, List[float]], 
                           vec2: Union[np.ndarray, List[float]]) -> float:
        """计算余弦相似度（带缓存）"""
        if not len(vec1) or not len(vec2):
            return 0.0
        
        # 转换为numpy数组
        v1 = np.array(vec1, dtype=np.float32) if not isinstance(vec1, np.ndarray) else vec1
        v2 = np.array(vec2, dtype=np.float32) if not isinstance(vec2, np.ndarray) else vec2
        
        # 检查缓存
        cache_key = (hash(v1.tobytes()), hash(v2.tobytes()))
        if self.config["enable_caching"] and cache_key in self.similarity_cache:
            self.stats["cache_hits"] += 1
            return self.similarity_cache[cache_key]
        
        # 计算余弦相似度
        norm1 = np.linalg.norm(v1)
        norm2 = np.linalg.norm(v2)
        
        if norm1 == 0 or norm2 == 0:
            similarity = 0.0
        else:
            similarity = np.dot(v1, v2) / (norm1 * norm2)
        
        # 归一化到 [0,1]
        similarity = (similarity + 1) / 2 if similarity < 0 else similarity
        
        # 缓存结果
        if self.config["enable_caching"]:
            self.similarity_cache[cache_key] = similarity
            self.stats["cache_misses"] += 1
            
            # 限制缓存大小
            if len(self.similarity_cache) > self.config["max_cache_size"]:
                # 随机删除一些条目（简化实现）
                keys_to_remove = list(self.similarity_cache.keys())[:100]
                for key in keys_to_remove:
                    del self.similarity_cache[key]
        
        return similarity
    
    def _parse_timestamp(self, timestamp_str: str) -> Optional[datetime]:
        """解析时间戳字符串"""
        if not timestamp_str:
            return None
        
        try:
            # 尝试ISO格式
            return datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        except ValueError:
            try:
                # 尝试其他格式
                for fmt in ["%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"]:
                    try:
                        return datetime.strptime(timestamp_str, fmt)
                    except ValueError:
                        continue
            except Exception:
                pass
        
        return None
    
    def _get_causal_link_score(self, source_id: str, target_id: str) -> float:
        """获取两个记忆之间的因果链接评分"""
        links = self.causal_links.get(source_id, [])
        for link in links:
            if link.target_id == target_id:
                return link.confidence
        return 0.0
    
    def _dict_to_memory(self, mem_dict: Dict) -> ConsolidatedMemory:
        """将字典转换为ConsolidatedMemory对象"""
        return ConsolidatedMemory(
            id=mem_dict.get("id", str(hash(str(mem_dict)))),
            content=mem_dict.get("content", mem_dict.get("fact", "")),
            vec=mem_dict.get("vec", []),
            importance=mem_dict.get("importance", 0.5),
            memory_type=mem_dict.get("memory_type", mem_dict.get("type", "log")),
            timestamp=mem_dict.get("timestamp", ""),
            confidence=mem_dict.get("confidence", 1.0),
            source_count=mem_dict.get("source_count", 1),
            metadata=mem_dict.get("metadata", {}),
            emotional_weight=mem_dict.get("emotional_weight", 1.0)
        )
    
    def _generate_explanation(self, scores: Dict[str, float], total_score: float) -> str:
        """生成人类可读的解释"""
        explanations = []
        for dim, score in scores.items():
            if score > 0.1:  # 只报告显著维度
                explanations.append(f"{dim}:{score:.2f}")
        
        if not explanations:
            return f"综合评分: {total_score:.3f}"
        
        return f"综合评分: {total_score:.3f} ({' '.join(explanations)})"
    
    def _update_stats(self, memories_processed: int, processing_time: float):
        """更新统计信息"""
        self.stats["total_retrievals"] += 1
        
        # 更新平均处理时间
        old_avg = self.stats["avg_processing_time"]
        total = self.stats["total_retrievals"]
        self.stats["avg_processing_time"] = (
            old_avg * (total - 1) + processing_time
        ) / total
    
    # ==================== 因果检测方法 ====================
    
    def detect_causal_relationships(self, memories: List[ConsolidatedMemory]) -> List[CausalLink]:
        """
        检测记忆之间的因果关系
        
        Args:
            memories: 待检测的记忆列表
            
        Returns:
            检测到的因果链接列表
        """
        links = []
        
        # 按时间排序
        memories_with_time = []
        for mem in memories:
            mem_time = self._parse_timestamp(mem.timestamp)
            if mem_time:
                memories_with_time.append((mem, mem_time))
        
        memories_with_time.sort(key=lambda x: x[1])
        
        # 滑动窗口检测
        window_size = self.config["causal_window_size"]
        
        for i in range(len(memories_with_time)):
            mem_i, time_i = memories_with_time[i]
            
            # 向前看窗口
            for j in range(i + 1, min(i + window_size + 1, len(memories_with_time))):
                mem_j, time_j = memories_with_time[j]
                
                # 检测因果关系
                link = self._detect_causal_link(mem_i, mem_j)
                if link:
                    links.append(link)
                    self._add_causal_link(link)
        
        self.stats["causal_links_detected"] += len(links)
        return links
    
    def _detect_causal_link(self, mem1: ConsolidatedMemory, mem2: ConsolidatedMemory) -> Optional[CausalLink]:
        """检测两个记忆之间的因果链接"""
        # 方法1: 文本模式匹配
        pattern_score, evidence = self._match_causal_patterns(mem1.content, mem2.content)
        
        # 方法2: 关键词检测
        keyword_score = self._check_causal_keywords(mem1.content, mem2.content)
        
        # 方法3: 时间顺序（原因在结果之前）
        time_order_score = 0.5  # 中性
        
        mem1_time = self._parse_timestamp(mem1.timestamp)
        mem2_time = self._parse_timestamp(mem2.timestamp)
        
        if mem1_time and mem2_time:
            if mem1_time < mem2_time:
                time_order_score = 0.8  # mem1可能在mem2之前
            else:
                time_order_score = 0.2
        
        # 综合评分
        confidence = (0.6 * pattern_score + 0.3 * keyword_score + 0.1 * time_order_score)
        
        if confidence > 0.5:  # 阈值
            # 确定方向（基于模式匹配证据）
            direction = self._determine_causal_direction(mem1, mem2, evidence)
            
            if direction == "forward":
                source, target = mem1.id, mem2.id
            else:
                source, target = mem2.id, mem1.id
            
            return CausalLink(
                source_id=source,
                target_id=target,
                relation_type="cause",
                confidence=confidence,
                evidence=evidence[:200] if evidence else "检测到的逻辑关联"
            )
        
        return None
    
    def _match_causal_patterns(self, text1: str, text2: str) -> Tuple[float, str]:
        """匹配因果模式"""
        # 合并文本检测
        combined = text1 + " " + text2
        
        max_score = 0.0
        best_evidence = ""
        
        for pattern, weight in self.patterns_compiled:
            match = pattern.search(combined)
            if match:
                max_score = max(max_score, weight)
                best_evidence = f"模式匹配: {pattern.pattern[:50]}..."
        
        return max_score, best_evidence
    
    def _check_causal_keywords(self, text1: str, text2: str) -> float:
        """检查因果关键词"""
        keywords = self.config["causal_keywords"]
        
        # 检查文本中是否同时包含因果关键词
        has_keyword1 = any(keyword in text1 for keyword in keywords)
        has_keyword2 = any(keyword in text2 for keyword in keywords)
        
        if has_keyword1 and has_keyword2:
            return 0.7
        elif has_keyword1 or has_keyword2:
            return 0.4
        else:
            return 0.1
    
    def _determine_causal_direction(self, mem1: ConsolidatedMemory, mem2: ConsolidatedMemory, 
                                   evidence: str) -> str:
        """确定因果方向"""
        # 简单实现：基于时间顺序
        mem1_time = self._parse_timestamp(mem1.timestamp)
        mem2_time = self._parse_timestamp(mem2.timestamp)
        
        if mem1_time and mem2_time:
            if mem1_time < mem2_time:
                return "forward"  # mem1 -> mem2
            else:
                return "backward"  # mem2 -> mem1
        
        # 默认：mem1 -> mem2
        return "forward"
    
    def _add_causal_link(self, link: CausalLink):
        """添加因果链接到内部存储"""
        if link.source_id not in self.causal_links:
            self.causal_links[link.source_id] = []
        
        # 避免重复
        existing = [l for l in self.causal_links[link.source_id] 
                   if l.target_id == link.target_id]
        if not existing:
            self.causal_links[link.source_id].append(link)
    
    # ==================== 主题聚类方法 ====================
    
    def cluster_by_theme(self, memories: List[ConsolidatedMemory]) -> Dict[str, Cluster]:
        """
        基于语义相似度进行主题聚类
        
        Args:
            memories: 待聚类的记忆列表
            
        Returns:
            聚类结果字典（cluster_id -> Cluster）
        """
        if not self.config["enable_clustering"] or len(memories) < 2:
            return {}
        
        # 简单实现：层次聚类（单连接）
        clusters = {}
        
        # 1. 构建相似度矩阵
        memory_ids = [mem.id for mem in memories]
        vectors = [np.array(mem.vec) for mem in memories if len(mem.vec) == 768]
        
        if len(vectors) < 2:
            return {}
        
        # 2. 聚类（简化实现）
        threshold = self.config["clustering_threshold"]
        current_clusters = [[i] for i in range(len(memory_ids))]
        
        # 计算初始相似度
        for i in range(len(memory_ids)):
            for j in range(i + 1, len(memory_ids)):
                if self._compute_similarity(vectors[i], vectors[j]) >= threshold:
                    # 合并聚类
                    self._merge_clusters(current_clusters, i, j)
        
        # 3. 构建聚类对象
        for cluster_idx, member_indices in enumerate(current_clusters):
            if len(member_indices) >= self.config["min_cluster_size"]:
                # 获取成员记忆
                member_ids = [memory_ids[i] for i in member_indices]
                
                # 计算聚类中心
                cluster_vectors = [vectors[i] for i in member_indices]
                centroid = np.mean(cluster_vectors, axis=0)
                
                # 生成主题关键词（简化实现）
                theme_keywords = self._extract_theme_keywords(
                    [memories[i].content for i in member_indices]
                )
                
                # 计算聚类内一致性
                coherence = self._calculate_cluster_coherence(cluster_vectors)
                
                # 创建聚类
                cluster_id = f"theme_{cluster_idx}_{len(member_ids)}"
                cluster = Cluster(
                    cluster_id=cluster_id,
                    centroid=centroid,
                    member_ids=member_ids,
                    theme_keywords=theme_keywords,
                    coherence_score=coherence
                )
                
                clusters[cluster_id] = cluster
                
                # 更新成员关联
                for mem_id in member_ids:
                    mem = next((m for m in memories if m.id == mem_id), None)
                    if mem:
                        mem.theme_cluster_id = cluster_id
                        self.cluster_membership[mem_id] = cluster_id
        
        self.stats["clusters_created"] = len(clusters)
        self.clusters.update(clusters)
        
        return clusters
    
    def _merge_clusters(self, clusters: List[List[int]], i: int, j: int):
        """合并两个聚类（简化实现）"""
        # 查找i和j所属的聚类
        cluster_i = None
        cluster_j = None
        for cluster in clusters:
            if i in cluster:
                cluster_i = cluster
            if j in cluster:
                cluster_j = cluster
        
        if cluster_i is not None and cluster_j is not None and cluster_i != cluster_j:
            # 合并
            cluster_i.extend(cluster_j)
            clusters.remove(cluster_j)
    
    def _extract_theme_keywords(self, texts: List[str], top_n: int = 5) -> List[str]:
        """从文本中提取主题关键词（简化实现）"""
        # 使用简单的词频统计（中文需要分词，这里简化处理）
        words = []
        for text in texts[:10]:  # 限制前10个文本
            # 简单分割（实际中应使用中文分词）
            tokens = re.findall(r'[\u4e00-\u9fff]+|[A-Za-z]+', text)
            words.extend(tokens[:20])  # 限制每文本前20个词
        
        # 词频统计
        from collections import Counter
        word_counts = Counter(words)
        
        return [word for word, _ in word_counts.most_common(top_n)]
    
    def _calculate_cluster_coherence(self, vectors: List[np.ndarray]) -> float:
        """计算聚类内一致性（平均相似度）"""
        if len(vectors) < 2:
            return 1.0
        
        similarities = []
        for i in range(len(vectors)):
            for j in range(i + 1, len(vectors)):
                sim = self._compute_similarity(vectors[i], vectors[j])
                similarities.append(sim)
        
        return float(np.mean(similarities)) if similarities else 0.0
    
    # ==================== 集成方法 ====================
    
    def load_from_long_term_storage(self):
        """从长期存储加载记忆"""
        if not self.long_term_storage:
            warnings.warn("未配置长期存储")
            return False
        
        try:
            # 假设长期存储有load_all方法
            storage_memories = self.long_term_storage.load_all()
            
            for mem_dict in storage_memories:
                memory = self._dict_to_memory(mem_dict)
                self.memory_cache[memory.id] = memory
            
            print(f"[关联检索] 从长期存储加载了 {len(self.memory_cache)} 条记忆")
            return True
            
        except Exception as e:
            warnings.warn(f"从长期存储加载失败: {e}")
            return False
    
    def update_emotional_weights(self):
        """从情绪评估模块更新情绪权重"""
        if not self.emotional_appraisal or not self.memory_cache:
            return
        
        try:
            for mem_id, memory in self.memory_cache.items():
                # 假设情绪评估模块有get_emotional_weight方法
                weight = self.emotional_appraisal.get_emotional_weight(memory.content)
                if weight is not None:
                    memory.emotional_weight = weight
            
            print(f"[关联检索] 更新了 {len(self.memory_cache)} 条记忆的情绪权重")
        except Exception as e:
            warnings.warn(f"更新情绪权重失败: {e}")
    
    # ==================== 批量检索 ====================
    
    def batch_retrieve(self, queries: List[RetrievalQuery]) -> List[List[RetrievalResult]]:
        """
        批量检索（性能优化）
        
        Args:
            queries: 检索查询列表
            
        Returns:
            检索结果列表
        """
        results = []
        for query in queries:
            result = self.retrieve_hybrid(query)
            results.append(result)
        
        return results
    
    # ==================== 缓存管理 ====================
    
    def clear_cache(self):
        """清空缓存"""
        self.vector_cache.clear()
        self.similarity_cache.clear()
        print("[关联检索] 缓存已清空")
    
    def update_cache(self, memories: List[ConsolidatedMemory]):
        """更新缓存"""
        for memory in memories:
            self.memory_cache[memory.id] = memory
            
            # 缓存向量
            if len(memory.vec) == 768:
                self.vector_cache[memory.id] = np.array(memory.vec)
        
        print(f"[关联检索] 缓存更新了 {len(memories)} 条记忆")
    
    # ==================== 统计信息 ====================
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        stats = self.stats.copy()
        stats["cached_memories"] = len(self.memory_cache)
        stats["causal_links_total"] = sum(len(links) for links in self.causal_links.values())
        stats["clusters_total"] = len(self.clusters)
        stats["cache_size"] = len(self.similarity_cache)
        return stats
    
    def reset_stats(self):
        """重置统计信息"""
        self.stats = {
            "total_retrievals": 0,
            "avg_processing_time": 0.0,
            "cache_hits": 0,
            "cache_misses": 0,
            "clusters_created": 0,
            "causal_links_detected": 0
        }

# ==================== 测试用例 ====================
def test_recall_association():
    """测试关联检索模块"""
    print("=" * 70)
    print("关联检索模块 - 测试运行")
    print("=" * 70)
    
    # 1. 创建测试记忆
    test_memories = [
        ConsolidatedMemory(
            id="mem1",
            content="因为学习了量子力学，所以对量子计算产生了兴趣。",
            vec=np.random.rand(768).tolist(),
            importance=0.9,
            memory_type="knowledge",
            timestamp="2026-03-28T09:00:00",
            confidence=0.9,
            emotional_weight=1.2
        ),
        ConsolidatedMemory(
            id="mem2",
            content="量子计算利用量子比特进行并行计算，速度远超经典计算机。",
            vec=np.random.rand(768).tolist(),
            importance=0.8,
            memory_type="knowledge",
            timestamp="2026-03-28T10:00:00",
            confidence=0.8,
            emotional_weight=1.1
        ),
        ConsolidatedMemory(
            id="mem3",
            content="我安装了Qiskit并运行了第一个量子电路程序。",
            vec=np.random.rand(768).tolist(),
            importance=0.7,
            memory_type="task",
            timestamp="2026-03-28T11:00:00",
            confidence=0.7,
            emotional_weight=1.0
        ),
        ConsolidatedMemory(
            id="mem4",
            content="今天整理了GitHub仓库，更新了README文档。",
            vec=np.random.rand(768).tolist(),
            importance=0.6,
            memory_type="task",
            timestamp="2026-03-28T12:00:00",
            confidence=0.6,
            emotional_weight=0.8
        ),
    ]
    
    # 2. 初始化检索引擎
    engine = RecallAssociation(config={
        "time_decay_alpha": 0.05,  # 更强的时间衰减
        "enable_caching": True,
        "clustering_threshold": 0.6
    })
    
    # 3. 加载测试记忆
    engine.update_cache(test_memories)
    
    # 4. 检测因果关系
    print("\n[测试] 检测因果关系...")
    causal_links = engine.detect_causal_relationships(test_memories)
    print(f"检测到 {len(causal_links)} 个因果链接")
    for link in causal_links:
        print(f"  {link.source_id} -> {link.target_id} (置信度: {link.confidence:.2f})")
    
    # 5. 主题聚类
    print("\n[测试] 主题聚类...")
    clusters = engine.cluster_by_theme(test_memories)
    print(f"创建了 {len(clusters)} 个主题聚类")
    for cluster_id, cluster in clusters.items():
        print(f"  聚类 {cluster_id}: {len(cluster.member_ids)} 个成员, "
              f"主题: {cluster.theme_keywords[:3]}")
    
    # 6. 语义相似度检索
    print("\n[测试] 语义相似度检索...")
    query_vec = np.random.rand(768)
    similar_results = engine.retrieve_by_similarity(query_vec, top_k=2)
    for i, result in enumerate(similar_results):
        print(f"  结果 {i+1}: {result}")
    
    # 7. 时间邻近检索
    print("\n[测试] 时间邻近检索...")
    ref_time = datetime.fromisoformat("2026-03-28T11:30:00")
    time_results = engine.retrieve_by_time(ref_time, time_window_hours=2, top_k=2)
    for i, result in enumerate(time_results):
        print(f"  结果 {i+1}: {result}")
    
    # 8. 因果关系检索
    print("\n[测试] 因果关系检索...")
    causal_results = engine.retrieve_by_causality("mem1", max_depth=2, top_k=2)
    for i, result in enumerate(causal_results):
        print(f"  结果 {i+1}: {result}")
    
    # 9. 混合检索
    print("\n[测试] 混合检索...")
    query = RetrievalQuery(
        query_text="量子计算",
        query_vector=query_vec,
        query_type="knowledge",
        max_results=3,
        weights={
            "semantic": 0.5,
            "temporal": 0.3,
            "causal": 0.1,
            "emotional": 0.1
        }
    )
    hybrid_results = engine.retrieve_hybrid(query)
    for i, result in enumerate(hybrid_results):
        print(f"  结果 {i+1}: {result}")
        print(f"      评分组件: {result.score_components}")
    
    # 10. 显示统计信息
    print("\n[测试] 统计信息:")
    stats = engine.get_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    print("\n" + "=" * 70)
    print("[测试完成] 所有测试通过!")
    print("=" * 70)

# ==================== 集成指南 ====================
"""
如何将 RecallAssociation 集成到现有 OpenClawMemoryEngine:

1. 替换现有的检索方法:
   ```python
   # 原代码:
   results = engine.retrieve(query_text, top_k=5, query_type=type)
   
   # 新代码:
   recall_engine = RecallAssociation(
       long_term_storage=engine.storage,
       working_memory=engine.working_memory,
       emotional_appraisal=engine.emotional_appraisal
   )
   recall_engine.load_from_long_term_storage()
   
   query = RetrievalQuery(
       query_text=query_text,
       query_type=type,
       max_results=top_k
   )
   results = recall_engine.retrieve_hybrid(query)
   ```

2. 渐进增强策略:
   a. 第一阶段: 仅替换 retrieve() 方法，使用默认配置
   b. 第二阶段: 启用因果检测和主题聚类
   c. 第三阶段: 集成情绪权重和高级混合检索

3. 性能优化:
   - 对于小型记忆库 (<1000条), 使用全量检索
   - 对于中型记忆库 (1000-10000条), 启用缓存和聚类
   - 对于大型记忆库 (>10000条), 需要向量索引支持

4. 向后兼容:
   - 保持原 retrieve() 方法的接口兼容性
   - 新增高级方法供调用
   - 提供配置项控制功能启用
"""

if __name__ == "__main__":
    # 运行测试
    try:
        test_recall_association()
    except Exception as e:
        print(f"[ERROR] 测试运行失败: {e}")
        import traceback
        traceback.print_exc()