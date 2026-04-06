#!/usr/bin/env python3
"""
增强版工作记忆模块（基于对话轮次和重要性驱动）

重新设计基于三个核心原则：
1. 记忆保持以对话轮次而非绝对时间为单位
2. 衰减速率由重要性决定（重要记忆衰减更慢）
3. 组块大小根据模型能力和内容复杂度动态调整
"""

import os
import re
import json
import hashlib
import numpy as np
from datetime import datetime
from typing import List, Dict, Optional, Tuple, Any, Union
from dataclasses import dataclass, field, asdict
from enum import Enum
from collections import OrderedDict, defaultdict
import warnings
from math import exp, log

# =========== 可选依赖检测 ===========
try:
    import ollama
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False

# =========== 数据类型定义 ===========
class MemoryType(str, Enum):
    """记忆类型枚举"""
    FACT = "fact"           # 客观事实
    DECISION = "decision"   # 决策
    OPINION = "opinion"     # 观点
    INSTRUCTION = "instruction"  # 指令
    EXPERIENCE = "experience"    # 经验
    CODE = "code"           # 代码
    LOG = "log"             # 日志
    UNKNOWN = "unknown"     # 未知


@dataclass
class EnhancedMemory:
    """增强版记忆数据结构（包含重要性驱动衰减所需字段）"""
    # 基础信息
    id: str
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    
    # 向量嵌入
    embedding_vector: np.ndarray = None
    embedding_dim: int = 768
    embedding_model: str = "unknown"
    
    # 语义特征
    semantic_features: List[str] = field(default_factory=list)  # 关键词列表
    semantic_keywords: List[Tuple[str, float]] = field(default_factory=list)  # 带权重的关键词
    
    # 类型分类
    chunk_type: MemoryType = MemoryType.UNKNOWN
    type_confidence: float = 0.5
    
    # 重要性维度
    importance: float = 0.5
    retention_priority: float = 0.5  # 从情感评估模块获取（0-1）
    
    # 元数据
    source: str = ""
    tags: List[str] = field(default_factory=list)
    
    # 访问记录（使用对话轮次而非绝对时间）
    last_accessed_turn: int = 0  # 最后访问时的对话轮次
    access_count: int = 0
    last_access_time: datetime = field(default_factory=datetime.now)  # 保留时间字段兼容
    emotional_intensity: float = 0.0  # 情绪强度（可选）
    
    # 衰减相关参数
    decay_lambda: float = 0.1  # 基础衰减常数（基于轮次）
    retention_score: float = 0.0  # 当前留存分数
    
    def __post_init__(self):
        """初始化后处理"""
        self.last_accessed_turn = 0  # 初始化为0
        if self.retention_priority > 0:
            # 初始留存分数 = 重要性 × 留存优先级
            self.retention_score = self.importance * self.retention_priority
        else:
            self.retention_score = self.importance
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为可序列化的字典"""
        data = asdict(self)
        # 处理特殊类型
        data['timestamp'] = self.timestamp.isoformat()
        data['last_access_time'] = self.last_access_time.isoformat()
        data['embedding_vector'] = self.embedding_vector.tolist() if self.embedding_vector is not None else None
        data['chunk_type'] = self.chunk_type.value
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EnhancedMemory':
        """从字典还原"""
        # 转换特殊字段
        data = data.copy()
        if isinstance(data['timestamp'], str):
            data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        if isinstance(data.get('last_access_time'), str):
            data['last_access_time'] = datetime.fromisoformat(data['last_access_time'])
        if data.get('embedding_vector'):
            data['embedding_vector'] = np.array(data['embedding_vector'])
        if isinstance(data.get('chunk_type'), str):
            data['chunk_type'] = MemoryType(data['chunk_type'])
        return cls(**data)
    
    def update_access(self, current_turn: int):
        """更新访问记录（使用对话轮次）"""
        self.last_access_time = datetime.now()
        self.last_accessed_turn = current_turn
        self.access_count += 1
        
        # 每次访问轻微提升留存分数（使用频率增强）
        self.retention_score = min(1.0, self.retention_score + 0.05)
    
    def calculate_current_score(self, current_turn: int) -> float:
        """
        计算当前记忆的留存分数（基于重要性驱动的衰减）
        
        Args:
            current_turn: 当前对话轮次
            
        Returns:
            当前留存分数（0-1）
        """
        # 如果没有重要性数据，使用默认衰减
        if not hasattr(self, 'importance') or self.importance <= 0:
            return 0.1
        
        # 计算轮次变化
        turns_since_accessed = max(0, current_turn - self.last_accessed_turn)
        
        # **核心改进1：衰减常数与重要性负相关**
        # 重要记忆衰减更慢（lambda_i = lambda_base / (1 + importance)）
        lambda_base = self.decay_lambda
        importance_boost = 1.0 + self.importance * 2.0  # 重要记忆衰减更慢
        lambda_i = lambda_base / importance_boost
        
        # **核心改进2：使用轮次而非时间计算衰减**
        decay = exp(-lambda_i * turns_since_accessed)
        
        # **核心改进3：情绪增强效应（如果可用）**
        emotional_boost = 1.0
        if hasattr(self, 'emotional_intensity') and self.emotional_intensity > 0:
            emotional_boost = 1.0 + min(self.emotional_intensity * 0.5, 0.5)
        
        # 综合留存分数 = 基础重要性 × 衰减 × 情绪增强 × 保留权重
        retention_priority = getattr(self, 'retention_priority', 0.5)
        
        current_score = (
            self.importance * 
            retention_priority * 
            decay * 
            emotional_boost
        )
        
        # 更新内部留存分数
        self.retention_score = current_score
        
        return current_score


# =========== 增强型工作记忆管理器 ===========
    def _init_fallback_components(self, embedding_backend):
        """初始化简化组件作为后备"""
        # 简化嵌入引擎
        class FallbackEmbeddingEngine:
            def __init__(self, preferred_backend="pseudo"):
                self.preferred_backend = preferred_backend
                self.embedding_dim = 768
                
            def embed(self, text):
                import numpy as np
                import hashlib
                # 生成伪嵌入向量
                h = hashlib.sha256(text.encode()).hexdigest()
                seed = int(h[:8], 16) % 10000
                np.random.seed(seed)
                vec = np.random.randn(self.embedding_dim)
                norm = np.linalg.norm(vec)
                if norm > 0:
                    vec = vec / norm
                return vec
                
            def get_backend_info(self):
                return {
                    "active_backend": "pseudo",
                    "embedding_dim": self.embedding_dim
                }
        
        # 简化的特征提取器
        class FallbackFeatureExtractor:
            def extract_keywords(self, text):
                import re
                from collections import defaultdict
                words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
                word_freq = defaultdict(int)
                for word in words:
                    if len(word) > 2 and word not in ['the', 'and', 'for', 'that', 'this', 'with', 'have', 'from']:
                        word_freq[word] += 1
                
                sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
                return [(word, min(freq/10, 1.0)) for word, freq in sorted_words[:5]]
        
        # 简化的类型分类器
        class FallbackTypeClassifier:
            def classify(self, text, semantic_keywords=None):
                from .working_memory_enhanced import MemoryType
                text_lower = text.lower()
                if 'error' in text_lower or 'warning' in text_lower:
                    return MemoryType.LOG, 0.7
                elif 'def ' in text_lower or 'class ' in text_lower:
                    return MemoryType.CODE, 0.8
                elif 'should' in text_lower or 'must' in text_lower:
                    return MemoryType.INSTRUCTION, 0.7
                else:
                    return MemoryType.FACT, 0.5
        
        self.embedding_engine = FallbackEmbeddingEngine(preferred_backend=embedding_backend)
        self.feature_extractor = FallbackFeatureExtractor()
        self.type_classifier = FallbackTypeClassifier()


class EnhancedWorkingMemory:
    """
    增强版工作记忆管理器
    
    核心改进：
    1. 记忆保持以对话轮次为单位
    2. 衰减速率由重要性决定
    3. 动态容量策略（基于模型上下文）
    """
    
    def __init__(self, capacity: int = None, embedding_backend: str = "ollama",
                 enable_turn_based_decay: bool = True):
        """
        初始化增强工作记忆
        
        Args:
            capacity: 缓冲区容量（None表示自动估算）
            embedding_backend: 嵌入后端偏好
            enable_turn_based_decay: 是否启用轮次基础衰减
        """
        # 核心状态
        self.total_turns = 0  # 对话总轮次
        self.enable_turn_based_decay = enable_turn_based_decay
        
        # **动态容量估算**
        if capacity is None:
            self.capacity = self._estimate_capacity()
        else:
            self.capacity = capacity
        
        self.buffer = OrderedDict()  # id -> EnhancedMemory
        
        # 子组件初始化
        try:
            # 尝试复用现有组件
            from working_memory_fixed import EmbeddingEngine, SemanticFeatureExtractor, TypeClassifier
            self.embedding_engine = EmbeddingEngine(preferred_backend=embedding_backend)
            self.feature_extractor = SemanticFeatureExtractor(method="rule_based")
            self.type_classifier = TypeClassifier()
        except ImportError:
            # 如果不可用，创建简化的替代品
            print("[警告] 无法导入现有组件，使用简化版本")
            self._init_fallback_components(embedding_backend)
        
        # 统计信息
        self.stats = {
            "total_encoded": 0,
            "evicted": 0,
            "evicted_by_decay": 0,
            "hits": 0,
            "misses": 0,
            "turns_total": 0,
            "avg_retention_score": 0.0
        }
        
        # 配置参数
        self.base_decay_lambda = 0.1  # 每轮次基础衰减率
        self.retention_threshold = 0.1  # 留存阈值
        
        print(f"[EnhancedWorkingMemory] 初始化完成，容量={self.capacity}")
        print(f"  启用轮次基础衰减: {enable_turn_based_decay}")
    
    def _estimate_capacity(self) -> int:
        """
        估算适合当前模型的工作记忆容量
        
        **核心改进3：动态组块大小**
        - 不假设AI与人类有相同的工作记忆限制
        - 根据估计的模型上下文窗口动态调整
        - 考虑内容复杂度和注意力机制
        """
        # 尝试推断当前模型能力
        # 这里可以根据实际环境调整
        
        # 常见模型上下文窗口（token数）
        model_contexts = {
            "gpt-4": 128_000,
            "gpt-4-turbo": 128_000,
            "gpt-3.5-turbo": 16_000,
            "claude-3": 200_000,
            "claude-3.5-sonnet": 200_000,
            "gemini-pro": 32_000,
            "deepseek-v3": 128_000,
            "default": 32_000  # 保守估计
        }
        
        # 尝试从环境变量或配置获取模型信息
        model_estimate = os.environ.get("MODEL_NAME", "default")
        context_size = model_contexts.get(model_estimate.lower(), model_contexts["default"])
        
        # **AI vs 人类差异**
        # 人类工作记忆：约4-7个组块（Miller定律）
        # AI工作记忆：由上下文窗口决定，远大于人类
        
        # 假设平均每条记忆：500字符 ≈ 125 tokens（4:1字符:token比例）
        avg_tokens_per_memory = 125
        
        # 占用模型上下文的一定比例（15-30%）
        # 更高比例给AI，因为它本来就是为处理大量上下文设计的
        usage_percentage = 0.25  # 25%的上下文用于工作记忆
        
        # 计算容量
        estimated_capacity = int(context_size * usage_percentage / avg_tokens_per_memory)
        
        # 设置合理的上下限
        min_capacity = 10  # 最小，保证基本功能
        max_capacity = 100 # 最大，避免过多资源消耗
        
        final_capacity = max(min_capacity, min(estimated_capacity, max_capacity))
        
        print(f"[容量估算] 模型估计: {model_estimate}")
        print(f"          上下文窗口: {context_size:,} tokens")
        print(f"          估算容量: {estimated_capacity}")
        print(f"          最终容量: {final_capacity}")
        
        return final_capacity
    
    def increment_turn(self):
        """增加对话轮次计数器"""
        self.total_turns += 1
        self.stats["turns_total"] += 1
    
    def encode(self, content: str, importance: float = 0.5, 
               retention_priority: float = None, source: str = "", 
               tags: List[str] = None, emotional_intensity: float = 0.0) -> EnhancedMemory:
        """
        编码新记忆并添加到缓冲区
        
        **核心改进：集成重要性衰减和情感增强**
        
        Args:
            content: 记忆内容
            importance: 重要性分数 (0-1)
            retention_priority: 留存优先级（从情感评估模块，0-1）
            source: 来源
            tags: 标签列表
            emotional_intensity: 情绪强度（0-1）
            
        Returns:
            编码后的记忆对象
        """
        # 生成唯一ID
        mem_id = self._generate_id(content)
        
        # 如果已存在，更新访问记录
        if mem_id in self.buffer:
            memory = self.buffer[mem_id]
            memory.update_access(self.total_turns)
            self.buffer.move_to_end(mem_id)  # 移动到最近位置
            self.stats["hits"] += 1
            return memory
        
        self.stats["misses"] += 1
        
        # 1. 生成向量嵌入
        embedding_vector = self.embedding_engine.embed(content)
        
        # 2. 提取语义特征
        semantic_keywords = self.feature_extractor.extract_keywords(content)
        semantic_features = [kw for kw, _ in semantic_keywords]
        
        # 3. 分类记忆类型
        chunk_type, type_confidence = self.type_classifier.classify(content, semantic_keywords)
        
        # 4. 使用默认留存优先级如果未提供
        if retention_priority is None:
            # 根据类型和重要性估算
            retention_priority = importance * 0.7 + type_confidence * 0.3
        
        # 5. 创建增强记忆对象
        memory = EnhancedMemory(
            id=mem_id,
            content=content,
            embedding_vector=embedding_vector,
            semantic_features=semantic_features,
            semantic_keywords=semantic_keywords,
            chunk_type=chunk_type,
            type_confidence=type_confidence,
            importance=importance,
            retention_priority=retention_priority,
            source=source,
            tags=tags or [],
            emotional_intensity=emotional_intensity,
            last_accessed_turn=self.total_turns,
            access_count=1,
            decay_lambda=self.base_decay_lambda
        )
        
        # 初始留存分数计算
        memory.retention_score = memory.calculate_current_score(self.total_turns)
        
        # 6. 添加到缓冲区（应用基于留存的淘汰策略）
        self._add_to_buffer_with_retention_awareness(mem_id, memory)
        
        self.stats["total_encoded"] += 1
        
        print(f"[编码] {mem_id} | 重要性:{importance:.2f} | 留存:{retention_priority:.2f}")
        
        return memory
    
    def _generate_id(self, content: str) -> str:
        """生成记忆ID"""
        # 使用内容和时间戳的哈希
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        unique_str = f"{content[:100]}_{timestamp}_{self.total_turns}"
        return hashlib.md5(unique_str.encode()).hexdigest()[:12]
    
    def _add_to_buffer_with_retention_awareness(self, mem_id: str, memory: EnhancedMemory):
        """
        基于留存分数的智能缓冲区管理
        
        **改进策略**：
        1. 如果缓冲区未满，直接添加
        2. 如果已满，淘汰留存分数最低的记忆（而不是最久未访问）
        3. 考虑重要性、访问频率、情绪强度等综合因素
        """
        # 如果缓冲区已满
        if len(self.buffer) >= self.capacity:
            # 找到留存分数最低的记忆
            lowest_score = float('inf')
            lowest_id = None
            
            # 重新计算所有记忆的当前留存分数
            for existing_id, existing_memory in self.buffer.items():
                current_score = existing_memory.calculate_current_score(self.total_turns)
                
                # 更新缓存分数
                existing_memory.retention_score = current_score
                
                # 找出分数最低的
                if current_score < lowest_score:
                    lowest_score = current_score
                    lowest_id = existing_id
            
            # 如果新记忆比最低分记忆更值得保留
            new_score = memory.retention_score
            
            if lowest_id is not None and lowest_score < new_score:
                # 淘汰最低分记忆
                del self.buffer[lowest_id]
                print(f"[淘汰] {lowest_id} | 分数:{lowest_score:.3f} < 新:{new_score:.3f}")
                self.stats["evicted"] += 1
                self.stats["evicted_by_decay"] += 1
            else:
                # 新记忆不值得保留（不应发生，但保留逻辑）
                print(f"[放弃] 新记忆分数({new_score:.3f})不够高")
                return
        
        # 添加到缓冲区
        self.buffer[mem_id] = memory
    
    def prune_low_value_memories(self, threshold: float = None):
        """
        主动淘汰低价值记忆
        
        **核心改进**：定期清理而不等待缓冲区满
        """
        if threshold is None:
            threshold = self.retention_threshold
        
        print(f"[清理] 开始清理，阈值:{threshold:.3f}")
        
        to_remove = []
        total_before = len(self.buffer)
        
        # 重新计算并筛选
        for mem_id, memory in self.buffer.items():
            current_score = memory.calculate_current_score(self.total_turns)
            memory.retention_score = current_score
            
            if current_score < threshold:
                to_remove.append(mem_id)
                print(f"  淘汰: {mem_id} | 分数:{current_score:.3f} | 重要性:{memory.importance:.2f}")
        
        # 移除淘汰的记忆
        for mem_id in to_remove:
            del self.buffer[mem_id]
        
        removed_count = len(to_remove)
        self.stats["evicted"] += removed_count
        self.stats["evicted_by_decay"] += removed_count
        
        print(f"[清理] 完成，移除{removed_count}条，剩余{len(self.buffer)}条")
    
    def get(self, mem_id: str) -> Optional[EnhancedMemory]:
        """
        获取记忆（更新访问记录和留存分数）
        
        **改进**：每次访问都会重新计算留存分数
        """
        if mem_id in self.buffer:
            memory = self.buffer[mem_id]
            
            # 更新访问（使用轮次）
            memory.update_access(self.total_turns)
            
            # 重新计算留存分数（访问提升）
            memory.retention_score = memory.calculate_current_score(self.total_turns)
            
            # LRU：移动到最近位置
            self.buffer.move_to_end(mem_id)
            
            self.stats["hits"] += 1
            return memory
        
        self.stats["misses"] += 1
        return None
    
    def query_similar(self, query_text: str, top_k: int = 5, 
                      min_similarity: float = 0.3, 
                      filter_by_retention: bool = True) -> List[Tuple[EnhancedMemory, float]]:
        """
        查询相似记忆（可选按留存分数过滤）
        
        Args:
            query_text: 查询文本
            top_k: 返回结果数量
            min_similarity: 最小相似度阈值
            filter_by_retention: 是否根据留存分数过滤
            
        Returns:
            (记忆, 相似度) 列表
        """
        if not self.buffer:
            return []
        
        # 生成查询向量
        query_vec = self.embedding_engine.embed(query_text)
        
        # 计算相似度并考虑留存分数
        results = []
        for memory in self.buffer.values():
            if memory.embedding_vector is None:
                continue
            
            # 余弦相似度
            norm_memory = np.linalg.norm(memory.embedding_vector)
            if norm_memory == 0:
                continue
                
            similarity = np.dot(query_vec, memory.embedding_vector) / (
                np.linalg.norm(query_vec) * norm_memory + 1e-8
            )
            
            # **增强：结合留存分数调整最终评分**
            if filter_by_retention:
                # 重新计算当前留存分数
                retention_score = memory.calculate_current_score(self.total_turns)
                
                # 综合评分 = 相似度 × 留存分数（更高留存分数提升相关度）
                adjusted_similarity = similarity * (0.7 + 0.3 * retention_score)
            else:
                adjusted_similarity = similarity
            
            if similarity >= min_similarity:
                results.append((memory, similarity, adjusted_similarity))
        
        # 按调整后的相似度排序
        results.sort(key=lambda x: x[2], reverse=True)
        
        # 返回记忆和原始相似度
        return [(mem, sim) for mem, sim, _ in results[:top_k]]
    
    def get_buffer_stats(self) -> Dict[str, Any]:
        """获取缓冲区统计信息（含留存分析）"""
        type_distribution = defaultdict(int)
        total_importance = 0.0
        total_retention = 0.0
        
        # 重新计算所有记忆的当前分数并收集统计
        for memory in self.buffer.values():
            current_score = memory.calculate_current_score(self.total_turns)
            memory.retention_score = current_score
            
            type_distribution[memory.chunk_type.value] += 1
            total_importance += memory.importance
            total_retention += current_score
        
        # 计算平均值
        buffer_size = len(self.buffer)
        avg_importance = total_importance / buffer_size if buffer_size > 0 else 0
        avg_retention = total_retention / buffer_size if buffer_size > 0 else 0
        
        # 命中率
        total_accesses = self.stats["hits"] + self.stats["misses"]
        hit_rate = self.stats["hits"] / total_accesses if total_accesses > 0 else 0
        
        # 保存平均留存分数到统计
        self.stats["avg_retention_score"] = avg_retention
        
        return {
            "buffer_size": buffer_size,
            "capacity": self.capacity,
            "type_distribution": dict(type_distribution),
            "average_importance": avg_importance,
            "average_retention_score": avg_retention,
            "total_encoded": self.stats["total_encoded"],
            "evicted": self.stats["evicted"],
            "evicted_by_decay": self.stats["evicted_by_decay"],
            "hit_rate": hit_rate,
            "hits": self.stats["hits"],
            "misses": self.stats["misses"],
            "total_turns": self.total_turns,
            "turn_based_decay_enabled": self.enable_turn_based_decay,
            "pruning_threshold": self.retention_threshold
        }
    
    def clear(self):
        """清空缓冲区"""
        self.buffer.clear()
        self.total_turns = 0
        print("[清理] 工作记忆缓冲区已清空")
    
    def summarize_enhancements(self):
        """总结重构的改进"""
        print("=" * 80)
        print("增强版工作记忆模块 - 重构总结")
        print("=" * 80)
        
        print("\n[核心重构1] 从时间衰减转向对话轮次衰减")
        print("   • 人类记忆：随时间自然衰退（18秒规则）")
        print("   • AI记忆：无自然衰退，衰减应基于使用频率")
        print("   • 实现：使用对话轮次计算衰减而非绝对时间")
        
        print("\n[核心重构2] 重要性驱动衰减速率")
        print("   • 重要记忆（importance↑）→ 衰减更慢（lambda↓）")
        print("   • 公式：λ_i = λ_base / (1 + importance)")
        print("   • 留存分数 = importance × exp(-λ_i × turns_passed)")
        
        print("\n[核心重构3] 动态容量策略")
        print("   • 人类：工作记忆 ~7±2组块（Miller定律）")
        print("   • AI：容量与模型上下文窗口成正比")
        print(f"   • 当前容量：{self.capacity}（基于模型上下文估算）")
        
        print("\n[新增功能] 留存感知淘汰")
        print("   • 淘汰策略：淘汰留存分数最低的记忆，而非LRU")
        print("   • 主动清理：定期清理低留存分数记忆")
        print(f"   • 阈值：{self.retention_threshold}")
        
        print("\n" + "=" * 80)
    
    # 保持兼容性的方法
    def save_buffer(self, filepath: str):
        """保存缓冲区到文件"""
        buffer_data = {
            "metadata": {
                "capacity": self.capacity,
                "saved_at": datetime.now().isoformat(),
                "stats": self.stats,
                "total_turns": self.total_turns,
                "enable_turn_based_decay": self.enable_turn_based_decay
            },
            "memories": [memory.to_dict() for memory in self.buffer.values()]
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(buffer_data, f, indent=2, ensure_ascii=False)
        
        print(f"[保存] 缓冲区已保存到 {filepath}")
    
    def load_buffer(self, filepath: str):
        """从文件加载缓冲区"""
        if not os.path.exists(filepath):
            print(f"[警告] 文件不存在: {filepath}")
            return False
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                buffer_data = json.load(f)
            
            # 恢复统计信息
            metadata = buffer_data.get("metadata", {})
            self.stats.update(metadata.get("stats", {}))
            self.total_turns = metadata.get("total_turns", 0)
            
            # 恢复记忆
            self.buffer.clear()
            for mem_dict in buffer_data.get("memories", []):
                memory = EnhancedMemory.from_dict(mem_dict)
                self.buffer[memory.id] = memory
            
            print(f"[加载] 从 {filepath} 加载了 {len(self.buffer)} 条记忆")
            return True
        
        except Exception as e:
            print(f"[错误] 加载缓冲区失败: {e}")
            return False


# =========== 集成示例和测试 ===========
def demonstrate_enhancements():
    """展示增强功能"""
    print("=" * 80)
    print("增强版工作记忆 - 演示")
    print("=" * 80)
    
    # 1. 初始化（智能容量估算）
    print("\n[1] 初始化增强工作记忆")
    wm = EnhancedWorkingMemory(capacity=None)  # None表示自动估算
    
    # 显示初始状态
    stats = wm.get_buffer_stats()
    print(f"  容量: {stats['capacity']}")
    print(f"  轮次基础衰减: {stats['turn_based_decay_enabled']}")
    
    # 2. 模拟对话轮次
    print("\n[2] 模拟对话轮次（重要性驱动衰减演示）")
    
    # 创建不同重要性的测试记忆
    test_memories = [
        ("高重要性记忆：用户的核心偏好", 0.9, 0.8, 0.7),
        ("中重要性记忆：常规任务指令", 0.6, 0.5, 0.3),
        ("低重要性记忆：临时聊天消息", 0.3, 0.2, 0.1),
    ]
    
    print("   模拟编码3条不同重要性的记忆...")
    for i, (content, importance, retention, emotion) in enumerate(test_memories):
        wm.increment_turn()  # 模拟一次对话
        memory = wm.encode(
            content, 
            importance=importance,
            retention_priority=retention,
            emotional_intensity=emotion,
            source=f"test_{i+1}"
        )
        
        # 计算初始留存分数
        initial_score = memory.retention_score
        print(f"      {i+1}. {content[:30]}...")
        print(f"         重要性: {importance:.2f} | 留存优先级: {retention:.2f}")
        print(f"         情绪强度: {emotion:.2f} | 初始留存分数: {initial_score:.3f}")
    
    # 3. 展示重要性驱动衰减
    print("\n[3] 模拟5个对话轮次后的衰减")
    
    initial_scores = {}
    for mem_id, memory in wm.buffer.items():
        initial_scores[mem_id] = memory.retention_score
    
    # 模拟多次对话轮次
    for turn in range(5):
        wm.increment_turn()  # 每次模拟一次对话
    
    # 重新计算所有留存分数
    for mem_id, memory in wm.buffer.items():
        new_score = memory.calculate_current_score(wm.total_turns)
        memory.retention_score = new_score
        initial_score = initial_scores.get(mem_id, new_score)
        
        importance = memory.importance
        score_loss = initial_score - new_score
        relative_loss = score_loss / initial_score if initial_score > 0 else 0
        
        print(f"   {memory.content[:25]}...")
        print(f"     重要性: {importance:.2f} | 分数变化: {initial_score:.3f} → {new_score:.3f}")
        print(f"     相对损失: {relative_loss:.1%}")
    
    # 4. 展示动态容量和清理
    print("\n[4] 填充缓冲区展示淘汰策略")
    
    # 添加更多记忆以触发淘汰
    for i in range(10):
        wm.increment_turn()
        wm.encode(
            f"填充记忆 {i+1}",
            importance=0.2 + (i % 2) * 0.3,  # 混合重要性
            retention_priority=0.3 + (i % 2) * 0.4,
            source="fill_test"
        )
    
    # 执行主动清理
    print("   执行主动清理...")
    wm.prune_low_value_memories(threshold=0.15)
    
    # 最终统计
    print("\n[5] 最终统计")
    stats = wm.get_buffer_stats()
    print(f"   缓冲区大小: {stats['buffer_size']}/{stats['capacity']}")
    print(f"   淘汰总数: {stats['evicted']}（其中{stats['evicted_by_decay']}因衰减淘汰）")
    print(f"   平均留存分数: {stats['average_retention_score']:.3f}")
    print(f"   总对话轮次: {stats['total_turns']}")
    
    # 展示集成能力
    print("\n[6] 与情感评估模块集成示例")
    print("   提示：此模块设计时考虑了与emotional_appraisal的集成")
    print("   字段映射：")
    print("      - retention_priority <- emotional_appraisal.retention_priority")
    print("      - emotional_intensity <- emotional_appraisal.emotional_intensity")
    print("   集成代码示例：")
    
    integration_example = """
# 集成工作记忆与情感评估
from emotional_appraisal import EmotionalAppraisalEngine, RawMemoryChunk

class IntegratedSystem:
    def __init__(self):
        self.working_memory = EnhancedWorkingMemory(capacity=None)
        self.emotion_engine = EmotionalAppraisalEngine()
    
    def process_with_emotion(self, content):
        # 1. 情感评估
        raw_memory = RawMemoryChunk(
            content=content,
            timestamp=datetime.now().isoformat(),
            source="user"
        )
        appraised = self.emotion_engine.appraise_memory(raw_memory)
        
        # 2. 工作记忆编码（使用情感评估结果）
        encoded = self.working_memory.encode(
            content=content,
            importance=appraised.significance_score,
            retention_priority=appraised.retention_priority,
            emotional_intensity=appraised.emotional_intensity
        )
        
        return encoded
    """
    
    print(integration_example)
    
    # 总结
    wm.summarize_enhancements()
    
    print("\n" + "=" * 80)
    print("演示完成!")
    print("=" * 80)


if __name__ == "__main__":
    # 运行演示
    demonstrate_enhancements()
    
    print("\n[使用方法]：")
    print("""
1. 替代标准工作记忆：
   from working_memory_enhanced import EnhancedWorkingMemory
   wm = EnhancedWorkingMemory(capacity=None)  # 自动估算容量
   
2. 集成到现有记忆引擎：
   # 在OpenClawMemoryEngine中替换working_memory
   self.working_memory = EnhancedWorkingMemory(capacity=None)
   
3. 与情感评估模块集成：
   # 获取情感评估结果后
   memory = wm.encode(
       content=text,
       importance=emotion_result.significance_score,
       retention_priority=emotion_result.retention_priority,
       emotional_intensity=emotion_result.emotional_intensity
   )
   
4. 使用对话轮次：
   # 每次用户或AI回复时
   wm.increment_turn()
   
5. 主动清理低价值记忆：
   wm.prune_low_value_memories(threshold=0.1)
    """)