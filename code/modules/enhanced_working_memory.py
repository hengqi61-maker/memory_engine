#!/usr/bin/env python3
"""
增强工作记忆系统 (Enhanced Working Memory)
集成十八秒定律的三层记忆模型：瞬时记忆、工作记忆、长期记忆
"""

import os
import re
import json
import hashlib
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple, Any, Union
from dataclasses import dataclass, field, asdict
from enum import Enum
from collections import OrderedDict, defaultdict, deque
import heapq
import math

# 尝试导入可选依赖
try:
    import ollama
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False
    print("[WARN] Ollama不可用，将使用伪嵌入向量")

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

try:
    import networkx as nx
    NETWORKX_AVAILABLE = True
except ImportError:
    NETWORKX_AVAILABLE = False


class MemoryHierarchy(Enum):
    """记忆层级枚举"""
    ULTRA_SHORT_TERM = "ultra_short_term"   # 瞬时记忆 (0-18秒)
    WORKING_MEMORY = "working_memory"       # 工作记忆 (数分钟-小时)
    LONG_TERM = "long_term"                 # 长期记忆 (数天-永久)


class MemoryType(str, Enum):
    """记忆类型枚举"""
    FACT = "fact"           # 客观事实
    DECISION = "decision"   # 决策
    OPINION = "opinion"     # 观点
    INSTRUCTION = "instruction"  # 指令
    EXPERIENCE = "experience"    # 经验
    CODE = "code"           # 代码
    LOG = "log"             # 日志
    PERSONAL = "personal"   # 个人信息
    EMOTIONAL = "emotional" # 情感记忆
    UNKNOWN = "unknown"     # 未知


class MemoryEncoding(Enum):
    """记忆编码类型"""
    SEMANTIC = "semantic"   # 语义编码
    PHONETIC = "phonetic"   # 音韵编码
    VISUAL = "visual"       # 视觉编码
    EMOTIONAL = "emotional" # 情感编码


@dataclass
class MemoryItem:
    """记忆项基础数据结构"""
    # 基础信息
    id: str
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    hierarchy: MemoryHierarchy = MemoryHierarchy.ULTRA_SHORT_TERM
    type: MemoryType = MemoryType.UNKNOWN
    
    # 编码信息
    encodings: List[MemoryEncoding] = field(default_factory=list)
    semantic_vector: np.ndarray = None       # 语义向量（用于相似度计算）
    phonetic_features: List[str] = None      # 音韵特征
    structural_features: Dict[str, Any] = None  # 结构特征
    
    # 记忆特性
    importance: float = 0.5                  # 重要性 (0-1)
    emotional_value: float = 0.0             # 情感价值 (-1到1)
    confidence: float = 0.5                  # 置信度
    coherence: float = 0.5                   # 内在一致性
    
    # 访问记录 (用于遗忘曲线)
    access_count: int = 0
    last_accessed: datetime = field(default_factory=datetime.now)
    first_encoded: datetime = field(default_factory=datetime.now)
    
    # 关联信息
    source: str = ""
    context: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    associations: List[str] = field(default_factory=list)  # 关联记忆ID
    
    # 元数据
    lifespan: float = 18.0  # 原始生命周期 (秒)
    current_activation: float = 1.0  # 当前激活水平 (0-1)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为可序列化的字典"""
        data = asdict(self)
        # 处理特殊类型
        data['timestamp'] = self.timestamp.isoformat()
        data['last_accessed'] = self.last_accessed.isoformat()
        data['first_encoded'] = self.first_encoded.isoformat()
        data['hierarchy'] = self.hierarchy.value
        data['type'] = self.type.value
        data['encodings'] = [enc.value for enc in self.encodings]
        data['semantic_vector'] = self.semantic_vector.tolist() if self.semantic_vector is not None else None
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MemoryItem':
        """从字典还原"""
        data = data.copy()
        # 转换特殊字段
        if 'timestamp' in data:
            data['timestamp'] = datetime.fromisoformat(data['timestamp']) if isinstance(data['timestamp'], str) else data['timestamp']
        
        if 'last_accessed' in data:
            data['last_accessed'] = datetime.fromisoformat(data['last_accessed']) if isinstance(data['last_accessed'], str) else data['last_accessed']
        
        if 'first_encoded' in data:
            data['first_encoded'] = datetime.fromisoformat(data['first_encoded']) if isinstance(data['first_encoded'], str) else data['first_encoded']
        
        if 'semantic_vector' in data and data['semantic_vector']:
            data['semantic_vector'] = np.array(data['semantic_vector'])
        
        if 'hierarchy' in data and isinstance(data['hierarchy'], str):
            data['hierarchy'] = MemoryHierarchy(data['hierarchy'])
        
        if 'type' in data and isinstance(data['type'], str):
            data['type'] = MemoryType(data['type'])
        
        if 'encodings' in data:
            data['encodings'] = [MemoryEncoding(enc) for enc in data['encodings']]
        
        return cls(**data)
    
    def update_access(self):
        """更新访问记录"""
        self.last_accessed = datetime.now()
        self.access_count += 1
    
    def calculate_decay(self, current_time: datetime = None) -> float:
        """
        计算记忆衰减
        基于记忆层级和时间流逝
        """
        if current_time is None:
            current_time = datetime.now()
        
        time_elapsed = (current_time - self.last_accessed).total_seconds()
        initial_activation = 1.0
        
        # 根据记忆层级使用不同衰减函数
        if self.hierarchy == MemoryHierarchy.ULTRA_SHORT_TERM:
            # 瞬时记忆：快速指数衰减 (τ ≈ 18秒)
            tau = 18.0  # 衰减时间常数
            self.current_activation = initial_activation * math.exp(-time_elapsed / tau)
            
        elif self.hierarchy == MemoryHierarchy.WORKING_MEMORY:
            # 工作记忆：对数衰减
            # 基础衰减加上注意力增强
            base_decay = 0.05
            attention_factor = math.log(time_elapsed + 1) * 0.1
            
            # 重要性影响衰减速率
            importance_factor = (1.0 - self.importance) * 0.3
            decay_rate = base_decay + importance_factor - attention_factor
            
            self.current_activation = max(0.0, initial_activation - decay_rate * time_elapsed)
            
        else:  # LONG_TERM
            # 长期记忆：渐进式衰减 + 艾宾浩斯遗忘曲线
            # 公式: R = e^(-t/S) 其中S是记忆强度
            memory_strength = self.importance * self.confidence * 100
            # 防止除以零
            if memory_strength < 1:
                memory_strength = 1
            
            retention = math.exp(-time_elapsed / memory_strength)
            
            # 情感价值增强记忆保持
            emotional_boost = 1.0 + abs(self.emotional_value) * 0.5
            self.current_activation = min(1.0, retention * emotional_boost)
        
        return self.current_activation


class UltraShortTermMemory:
    """瞬时记忆模块 (18秒保持窗口)"""
    
    def __init__(self, max_items: int = 7):
        """
        瞬时记忆初始化
        
        Args:
            max_items: 最大容量，基于"7±2"定律
        """
        self.max_items = max_items
        self.buffer = OrderedDict()  # id -> (MemoryItem, access_time)
        self.lifespan = 18.0  # 秒
    
    def add(self, memory: MemoryItem) -> bool:
        """
        添加记忆到瞬时记忆
        
        Args:
            memory: 记忆项
            
        Returns:
            是否添加成功
        """
        # 设置记忆层级
        memory.hierarchy = MemoryHierarchy.ULTRA_SHORT_TERM
        memory.lifespan = self.lifespan
        
        # 如果缓冲区已满，淘汰最旧的记忆
        if len(self.buffer) >= self.max_items:
            oldest_id = next(iter(self.buffer))
            del self.buffer[oldest_id]
        
        # 添加记忆
        self.buffer[memory.id] = (memory, datetime.now())
        memory.first_encoded = datetime.now()
        memory.update_access()
        
        print(f"[瞬时记忆] 添加: {memory.content[:50]}... (总容量: {len(self.buffer)}/{self.max_items})")
        return True
    
    def get(self, mem_id: str) -> Optional[MemoryItem]:
        """获取记忆，更新访问时间"""
        if mem_id in self.buffer:
            memory, _ = self.buffer[mem_id]
            current_time = datetime.now()
            
            # 检查是否过期 (超过18秒)
            time_since_last_access = (current_time - memory.last_accessed).total_seconds()
            if time_since_last_access > self.lifespan:
                print(f"[瞬时记忆] 记忆 {mem_id} 已过期 ({time_since_last_access:.1f}秒)")
                del self.buffer[mem_id]
                return None
            
            # 更新访问时间
            self.buffer[mem_id] = (memory, current_time)
            memory.update_access()
            memory.calculate_decay(current_time)
            
            return memory
        
        return None
    
    def cleanup(self, current_time: datetime = None) -> List[str]:
        """
        清理过期的瞬时记忆
        
        Returns:
            被清理的记忆ID列表
        """
        if current_time is None:
            current_time = datetime.now()
        
        expired_ids = []
        
        for mem_id, (memory, last_access) in list(self.buffer.items()):
            time_elapsed = (current_time - last_access).total_seconds()
            
            if time_elapsed > self.lifespan:
                expired_ids.append(mem_id)
                del self.buffer[mem_id]
                print(f"[瞬时记忆] 清理过期记忆: {mem_id[:8]} (已存 {time_elapsed:.1f}秒)")
        
        return expired_ids
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        current_time = datetime.now()
        avg_age = 0.0
        
        if self.buffer:
            ages = [(current_time - access_time).total_seconds() 
                   for _, access_time in self.buffer.values()]
            avg_age = sum(ages) / len(ages)
        
        return {
            "capacity": self.max_items,
            "current_size": len(self.buffer),
            "average_age_seconds": avg_age,
            "lifespan_seconds": self.lifespan,
            "memory_ids": list(self.buffer.keys())
        }


class WorkingMemoryManager:
    """工作记忆管理器"""
    
    def __init__(self, capacity: int = 30, 
                 consolidation_threshold: float = 0.7,
                 rehearsal_cycles: int = 3):
        """
        初始化工作记忆管理器
        
        Args:
            capacity: 工作记忆容量
            consolidation_threshold: 巩固阈值 (当激活水平高于此值时考虑转移到长期记忆)
            rehearsal_cycles: 排练次数阈值 (达到此次数才考虑长期存储)
        """
        self.capacity = capacity
        self.consolidation_threshold = consolidation_threshold
        self.rehearsal_cycles = rehearsal_cycles
        
        # 主存储：基于LRU的策略
        self.buffer = OrderedDict()  # id -> MemoryItem
        
        # 激活网络：记忆之间的关联
        self.associations = defaultdict(set)  # mem_id -> {associated_ids}
        
        # 统计信息
        self.stats = {
            "total_encoded": 0,
            "transfer_to_long_term": 0,
            "evicted": 0,
            "rehearsal_counts": defaultdict(int),
            "access_patterns": defaultdict(int)
        }
    
    def add_from_ultra_short_term(self, memory: MemoryItem) -> bool:
        """
        从瞬时记忆转移记忆到工作记忆
        
        Args:
            memory: 瞬时记忆项
            
        Returns:
            是否转移成功
        """
        # 检查记忆是否足够重要
        if memory.importance < 0.3 and memory.access_count < 2:
            print(f"[工作记忆] 跳过不重要记忆: {memory.content[:50]}...")
            return False
        
        # 更新记忆层级
        memory.hierarchy = MemoryHierarchy.WORKING_MEMORY
        memory.first_encoded = datetime.now()
        
        # 如果缓冲区已满，应用混合淘汰策略
        if len(self.buffer) >= self.capacity:
            candidate_id = self._select_eviction_candidate()
            if candidate_id:
                del self.buffer[candidate_id]
                self.stats["evicted"] += 1
                print(f"[工作记忆] 淘汰记忆: {candidate_id[:8]}")
        
        # 添加到工作记忆
        self.buffer[memory.id] = memory
        memory.update_access()
        self.stats["total_encoded"] += 1
        
        # 初始化排练计数
        self.stats["rehearsal_counts"][memory.id] = memory.access_count
        
        print(f"[工作记忆] 新记忆: {memory.content[:50]}... (容量: {len(self.buffer)}/{self.capacity})")
        return True
    
    def _select_eviction_candidate(self) -> Optional[str]:
        """选择淘汰候选记忆，基于混合策略"""
        if not self.buffer:
            return None
        
        current_time = datetime.now()
        candidates = []
        
        for mem_id, memory in self.buffer.items():
            # 计算淘汰分数 (越高越可能被淘汰)
            time_elapsed = (current_time - memory.last_accessed).total_seconds()
            current_activation = memory.calculate_decay(current_time)
            
            # 淘汰分数 = 低激活 + 低重要性 + 长时间未访问
            eviction_score = (
                (1.0 - current_activation) * 0.4 +
                (1.0 - memory.importance) * 0.3 +
                min(time_elapsed / 3600, 1.0) * 0.3
            )
            
            candidates.append((eviction_score, mem_id))
        
        # 选择淘汰分数最高的
        candidates.sort(reverse=True, key=lambda x: x[0])
        return candidates[0][1] if candidates else None
    
    def get(self, mem_id: str) -> Optional[MemoryItem]:
        """获取记忆，更新访问记录和排练计数"""
        if mem_id in self.buffer:
            memory = self.buffer[mem_id]
            
            # 更新访问
            memory.update_access()
            self.buffer.move_to_end(mem_id)  # LRU
            
            # 更新排练计数
            self.stats["rehearsal_counts"][mem_id] += 1
            
            # 计算当前激活水平
            memory.calculate_decay()
            
            # 检查是否达到巩固条件
            if (memory.current_activation > self.consolidation_threshold and 
                self.stats["rehearsal_counts"][mem_id] >= self.rehearsal_cycles):
                print(f"[工作记忆] 记忆 {mem_id[:8]} 准备好转移到长期记忆")
            
            return memory
        
        return None
    
    def query_by_relevance(self, query: str, top_k: int = 5, 
                          min_similarity: float = 0.3) -> List[Tuple[MemoryItem, float]]:
        """
        基于相关性的查询
        
        Args:
            query: 查询文本
            top_k: 返回结果数量
            min_similarity: 最小相似度阈值
            
        Returns:
            记忆项和相似度的列表
        """
        # 这里需要语义向量来计算相似度
        # 为简化，我们使用关键词匹配
        results = []
        query_lower = query.lower()
        query_words = set(re.findall(r'\w+', query_lower))
        
        for memory in self.buffer.values():
            if not query_words:
                score = 0.1  # 默认低分
            else:
                # 简单关键词匹配
                content_words = set(re.findall(r'\w+', memory.content.lower()))
                common = query_words.intersection(content_words)
                score = len(common) / max(len(query_words), 1)
            
            if score >= min_similarity:
                # 结合激活水平调整分数
                activation_boost = memory.current_activation * 0.2
                final_score = score * 0.8 + activation_boost
                
                results.append((memory, final_score))
        
        # 排序
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_k]
    
    def find_consolidation_candidates(self) -> List[MemoryItem]:
        """查找准备转移到长期记忆的候选记忆"""
        candidates = []
        current_time = datetime.now()
        
        for mem_id, memory in self.buffer.items():
            # 计算时间流逝
            time_since_encoded = (current_time - memory.first_encoded).total_seconds()
            
            # 检查记忆是否准备好巩固
            if (memory.current_activation > self.consolidation_threshold and
                self.stats["rehearsal_counts"][mem_id] >= self.rehearsal_cycles and
                time_since_encoded > 300):  # 至少存在5分钟
                
                memory.hierarchy = MemoryHierarchy.LONG_TERM  # 标记为长期记忆
                candidates.append(memory)
                
                print(f"[工作记忆] 选择巩固候选: {memory.content[:50]}...")
                print(f"   激活: {memory.current_activation:.2f}, "
                      f"排练: {self.stats['rehearsal_counts'][mem_id]}, "
                      f"时长: {time_since_encoded:.0f}秒")
        
        return candidates
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        type_distribution = defaultdict(int)
        total_activation = 0.0
        
        for memory in self.buffer.values():
            type_distribution[memory.type.value] += 1
            activation = memory.calculate_decay()
            total_activation += activation
        
        avg_activation = total_activation / len(self.buffer) if self.buffer else 0
        
        # 计算准备转移的记忆数量
        candidates = self.find_consolidation_candidates()
        
        return {
            "capacity": self.capacity,
            "current_size": len(self.buffer),
            "type_distribution": dict(type_distribution),
            "average_activation": avg_activation,
            "consolidation_candidates": len(candidates),
            "total_encoded": self.stats["total_encoded"],
            "transfer_to_long_term": self.stats["transfer_to_long_term"],
            "evicted": self.stats["evicted"]
        }


class MemoryConsolidator:
    """记忆巩固器，负责睡眠周期的记忆巩固"""
    
    def __init__(self, long_term_storage_path: str = None):
        """
        初始化记忆巩固器
        
        Args:
            long_term_storage_path: 长期记忆存储路径
        """
        self.long_term_storage_path = long_term_storage_path
        if long_term_storage_path:
            os.makedirs(os.path.dirname(long_term_storage_path), exist_ok=True)
        
        # 长期记忆存储
        self.long_term_memories = []
        
        # 加载现有长期记忆
        self._load_long_term_memories()
        
        # 巩固策略参数
        self.reconsolidation_interval = 86400  # 24小时
        self.max_long_term_memories = 1000
        self.consolidation_strength_boost = 1.5  # 巩固时的强度提升
    
    def _load_long_term_memories(self):
        """加载长期记忆"""
        if not self.long_term_storage_path or not os.path.exists(self.long_term_storage_path):
            self.long_term_memories = []
            return
        
        try:
            with open(self.long_term_storage_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if isinstance(data, list):
                self.long_term_memories = [MemoryItem.from_dict(mem) for mem in data]
                print(f"[长期记忆] 加载了 {len(self.long_term_memories)} 条长期记忆")
            else:
                self.long_term_memories = []
                print(f"[WARN] 长期记忆文件格式错误")
        
        except Exception as e:
            print(f"[ERROR] 加载长期记忆失败: {e}")
            self.long_term_memories = []
    
    def consolidate_memories(self, working_memories: List[MemoryItem]) -> List[MemoryItem]:
        """
        巩固工作记忆到长期记忆
        
        Args:
            working_memories: 工作记忆列表
            
        Returns:
            成功巩固的记忆列表
        """
        if not working_memories:
            return []
        
        consolidated = []
        current_time = datetime.now()
        
        for memory in working_memories:
            # 1. 检查记忆强度
            memory_strength = (memory.importance * 0.4 + 
                              memory.confidence * 0.3 + 
                              memory.current_activation * 0.3)
            
            # 2. 情感增强
            if abs(memory.emotional_value) > 0.5:
                memory_strength *= 1.5
            
            # 3. 检查是否足够强以巩固
            if memory_strength < 0.6:
                continue
            
            # 4. 处理重复/相似记忆
            existing_similar = self._find_similar_memory(memory)
            if existing_similar:
                # 合并到现有记忆
                self._merge_memories(existing_similar, memory)
                print(f"[巩固] 合并到现有记忆: {existing_similar.content[:50]}...")
            else:
                # 创建新长期记忆
                long_term_memory = self._prepare_for_long_term(memory)
                self.long_term_memories.append(long_term_memory)
                consolidated.append(long_term_memory)
                print(f"[巩固] 创建新长期记忆: {long_term_memory.content[:50]}...")
        
        # 5. 保存长期记忆
        if consolidated:
            self._save_long_term_memories()
        
        return consolidated
    
    def _find_similar_memory(self, memory: MemoryItem) -> Optional[MemoryItem]:
        """查找相似的长期记忆"""
        if not memory.semantic_vector or len(self.long_term_memories) == 0:
            return None
        
        best_similarity = 0.7  # 相似度阈值
        best_match = None
        
        for existing in self.long_term_memories:
            if not existing.semantic_vector:
                continue
            
            # 计算余弦相似度
            try:
                similarity = np.dot(memory.semantic_vector, existing.semantic_vector) / (
                    np.linalg.norm(memory.semantic_vector) * np.linalg.norm(existing.semantic_vector) + 1e-8
                )
                
                if similarity > best_similarity:
                    best_similarity = similarity
                    best_match = existing
            except:
                continue
        
        return best_match
    
    def _merge_memories(self, target: MemoryItem, source: MemoryItem):
        """合并两个记忆"""
        # 更新内容 (如果有新信息)
        if len(source.content) > len(target.content) * 1.2:  # 源内容显著更长
            new_content = f"{target.content}\n\n附加信息: {source.content}"
            target.content = new_content
        
        # 更新重要性和置信度
        target.importance = max(target.importance, source.importance)
        target.confidence = (target.confidence + source.confidence) / 2
        
        # 更新情感价值（取平均值）
        target.emotional_value = (target.emotional_value + source.emotional_value) / 2
        
        # 合并标签和关联
        target.tags = list(set(target.tags + source.tags))
        target.associations = list(set(target.associations + source.associations))
        
        # 更新元数据
        target.access_count += source.access_count
        target.last_accessed = datetime.now()
        
        # 增强记忆强度
        target.importance *= self.consolidation_strength_boost
        target.confidence = min(target.confidence * 1.2, 1.0)
    
    def _prepare_for_long_term(self, memory: MemoryItem) -> MemoryItem:
        """准备记忆用于长期存储"""
        long_term_memory = MemoryItem(
            id=memory.id,
            content=memory.content,
            timestamp=memory.timestamp,
            hierarchy=MemoryHierarchy.LONG_TERM,
            type=memory.type,
            importance=memory.importance * self.consolidation_strength_boost,
            emotional_value=memory.emotional_value,
            confidence=min(memory.confidence * 1.2, 1.0),
            semantic_vector=memory.semantic_vector,
            source=memory.source,
            tags=memory.tags.copy(),
            associations=memory.associations.copy(),
            access_count=memory.access_count,
            last_accessed=datetime.now(),
            first_encoded=memory.first_encoded,
            context=memory.context.copy()
        )
        
        return long_term_memory
    
    def _save_long_term_memories(self):
        """保存长期记忆到文件"""
        if not self.long_term_storage_path:
            return
        
        try:
            # 转换为字典
            memories_dict = [mem.to_dict() for mem in self.long_term_memories]
            
            # 临时文件保存
            tmp_path = self.long_term_storage_path + ".tmp"
            with open(tmp_path, 'w', encoding='utf-8') as f:
                json.dump(memories_dict, f, indent=2, ensure_ascii=False)
            
            # 原子替换
            if os.path.exists(self.long_term_storage_path):
                backup_path = self.long_term_storage_path + ".bak"
                os.replace(self.long_term_storage_path, backup_path)
            
            os.replace(tmp_path, self.long_term_storage_path)
            
            print(f"[长期记忆] 保存了 {len(self.long_term_memories)} 条记忆")
            
        except Exception as e:
            print(f"[ERROR] 保存长期记忆失败: {e}")
    
    def prune_long_term_memories(self, max_items: int = None):
        """修剪长期记忆，移除最弱的记忆"""
        if max_items is None:
            max_items = self.max_long_term_memories
        
        if len(self.long_term_memories) <= max_items:
            return
        
        # 计算每个记忆的强度分数
        memory_scores = []
        current_time = datetime.now()
        
        for i, memory in enumerate(self.long_term_memories):
            # 强度 = 重要性 × 置信度 × 情感强度 × 时间衰减
            time_elapsed = (current_time - memory.last_accessed).total_seconds()
            time_factor = math.exp(-time_elapsed / (self.reconsolidation_interval * 7))  # 1周衰减
            
            strength = (memory.importance * 
                       memory.confidence * 
                       (1.0 + abs(memory.emotional_value)) * 
                       time_factor)
            
            memory_scores.append((strength, i))
        
        # 按强度排序
        memory_scores.sort(key=lambda x: x[0])
        
        # 移除最弱的记忆
        remove_count = len(self.long_term_memories) - max_items
        remove_indices = [idx for _, idx in memory_scores[:remove_count]]
        
        # 反向删除以避免索引问题
        for idx in sorted(remove_indices, reverse=True):
            removed_memory = self.long_term_memories.pop(idx)
            print(f"[修剪] 移除长期记忆: {removed_memory.content[:50]}...")
        
        # 重新保存
        self._save_long_term_memories()
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        type_distribution = defaultdict(int)
        total_importance = 0.0
        total_confidence = 0.0
        
        for memory in self.long_term_memories:
            type_distribution[memory.type.value] += 1
            total_importance += memory.importance
            total_confidence += memory.confidence
        
        avg_importance = total_importance / len(self.long_term_memories) if self.long_term_memories else 0
        avg_confidence = total_confidence / len(self.long_term_memories) if self.long_term_memories else 0
        
        return {
            "total_memories": len(self.long_term_memories),
            "max_capacity": self.max_long_term_memories,
            "type_distribution": dict(type_distribution),
            "average_importance": avg_importance,
            "average_confidence": avg_confidence,
            "reconsolidation_interval_hours": self.reconsolidation_interval / 3600
        }


class SemanticFeatureExtractor:
    """语义特征提取器"""
    
    def __init__(self):
        # 这里可以添加实际的特征提取逻辑
        pass
    
    def extract_semantic_features(self, text: str) -> Dict[str, Any]:
        """提取语义特征"""
        # 简单的关键词提取
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
        word_freq = defaultdict(int)
        
        for word in words:
            # 过滤停用词
            if len(word) > 2 and word not in ['the', 'and', 'for', 'that', 'this']:
                word_freq[word] += 1
        
        # 提取主要主题
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        main_topics = [word for word, freq in sorted_words[:5]]
        
        return {
            "main_topics": main_topics,
            "word_count": len(words),
            "unique_words": len(set(words)),
            "avg_word_length": sum(len(w) for w in words) / len(words) if words else 0
        }


class EnhancedMemorySystem:
    """增强记忆系统 (整合三层模型)"""
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        初始化增强记忆系统
        
        Args:
            config: 配置字典
        """
        # 默认配置
        default_config = {
            "ultra_short_term": {
                "max_items": 7,
                "lifespan_seconds": 18.0
            },
            "working_memory": {
                "capacity": 30,
                "consolidation_threshold": 0.7,
                "rehearsal_cycles": 3
            },
            "long_term": {
                "storage_path": "memory/long_term_memories.json",
                "max_memories": 1000,
                "reconsolidation_interval_hours": 24
            }
        }
        
        # 合并用户配置
        if config:
            for key in default_config:
                if key in config:
                    default_config[key].update(config[key])
        
        self.config = default_config
        
        # 初始化组件
        print("=" * 70)
        print("增强记忆系统初始化")
        print("=" * 70)
        
        # 1. 瞬时记忆
        self.ultra_short_term = UltraShortTermMemory(
            max_items=self.config["ultra_short_term"]["max_items"]
        )
        
        # 2. 工作记忆
        self.working_memory = WorkingMemoryManager(
            capacity=self.config["working_memory"]["capacity"],
            consolidation_threshold=self.config["working_memory"]["consolidation_threshold"],
            rehearsal_cycles=self.config["working_memory"]["rehearsal_cycles"]
        )
        
        # 3. 记忆巩固器 (负责长期记忆)
        self.consolidator = MemoryConsolidator(
            long_term_storage_path=self.config["long_term"]["storage_path"]
        )
        
        # 4. 特征提取器
        self.feature_extractor = SemanticFeatureExtractor()
        
        # 系统状态
        self.system_start_time = datetime.now()
        self.total_memories_processed = 0
        self.last_sleep_cycle = None
        
        print(f"[系统] 瞬时记忆: {self.ultra_short_term.max_items} 项")
        print(f"[系统] 工作记忆: {self.working_memory.capacity} 项")
        print(f"[系统] 长期记忆: {len(self.consolidator.long_term_memories)} 项已加载")
        print("=" * 70)
    
    def encode_memory(self, content: str, importance: float = 0.5, 
                     memory_type: MemoryType = None, source: str = "",
                     tags: List[str] = None, emotional_value: float = 0.0) -> str:
        """
        编码新记忆
        
        Args:
            content: 记忆内容
            importance: 重要性分数
            memory_type: 记忆类型
            source: 来源信息
            tags: 标签列表
            emotional_value: 情感价值
            
        Returns:
            记忆ID
        """
        # 1. 提取特征
        semantic_features = self.feature_extractor.extract_semantic_features(content)
        
        # 2. 确定记忆类型
        if memory_type is None:
            memory_type = self._detect_memory_type(content)
        
        # 3. 创建记忆ID
        timestamp_str = datetime.now().strftime("%Y%m%d%H%M%S")
        content_hash = hashlib.md5(content.encode()).hexdigest()[:8]
        mem_id = f"mem_{timestamp_str}_{content_hash}"
        
        # 4. 创建记忆项
        memory = MemoryItem(
            id=mem_id,
            content=content,
            importance=importance,
            type=memory_type,
            source=source,
            tags=tags or [],
            emotional_value=emotional_value,
            context=semantic_features
        )
        
        # 5. 先添加到瞬时记忆
        success = self.ultra_short_term.add(memory)
        if success:
            self.total_memories_processed += 1
            
            # 6. 如果记忆重要或有情感价值，直接考虑转移到工作记忆
            if importance > 0.7 or abs(emotional_value) > 0.5:
                print(f"[编码] 重要/情感记忆，直接考虑工作记忆")
                self._transfer_to_working_if_needed(memory)
        
        return mem_id if success else ""
    
    def _detect_memory_type(self, content: str) -> MemoryType:
        """自动检测记忆类型"""
        content_lower = content.lower()
        
        if any(keyword in content_lower for keyword in ["量子", "物理", "计算", "科学", "研究"]):
            return MemoryType.FACT
        elif any(keyword in content_lower for keyword in ["决定", "选择", "应该", "会", "将"]):
            return MemoryType.DECISION
        elif any(keyword in content_lower for keyword in ["认为", "觉得", "喜欢", "不喜欢", "观点"]):
            return MemoryType.OPINION
        elif any(keyword in content_lower for keyword in ["def ", "class ", "import ", "function", "代码"]):
            return MemoryType.CODE
        elif any(keyword in content_lower for keyword in ["学习", "经验", "尝试", "解决", "发现"]):
            return MemoryType.EXPERIENCE
        elif any(keyword in content_lower for keyword in ["错误", "警告", "成功", "失败", "日志"]):
            return MemoryType.LOG
        else:
            return MemoryType.UNKNOWN
    
    def _transfer_to_working_if_needed(self, memory: MemoryItem):
        """检查并转移到工作记忆"""
        # 这里可以添加更复杂的转移逻辑
        # 比如基于注意力、重复率等
        
        # 简单规则：重要性>0.5 或 有情感价值
        if memory.importance > 0.5 or abs(memory.emotional_value) > 0.3:
            self.working_memory.add_from_ultra_short_term(memory)
    
    def get_memory(self, mem_id: str) -> Optional[MemoryItem]:
        """获取记忆（从所有层级）"""
        # 1. 检查瞬时记忆
        memory = self.ultra_short_term.get(mem_id)
        if memory:
            return memory
        
        # 2. 检查工作记忆
        memory = self.working_memory.get(mem_id)
        if memory:
            return memory
        
        # 3. 检查长期记忆
        # 这里需要实现长期记忆的检索
        # 为简化，我们暂时返回None
        
        return None
    
    def query(self, query_text: str, top_k: int = 5) -> List[Tuple[MemoryItem, float]]:
        """综合查询所有层级的记忆"""
        results = []
        
        # 1. 查询工作记忆
        working_results = self.working_memory.query_by_relevance(query_text, top_k=top_k)
        results.extend(working_results)
        
        # 2. 查询瞬时记忆（简单过滤）
        query_lower = query_text.lower()
        for _, (memory, _) in self.ultra_short_term.buffer.items():
            if query_lower in memory.content.lower():
                # 计算简单相关性分数
                content_lower = memory.content.lower()
                occurrences = content_lower.count(query_lower)
                word_count = len(content_lower.split())
                score = min(occurrences * 0.2, 1.0)
                
                results.append((memory, score))
        
        # 3. 排序并返回
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_k]
    
    def perform_sleep_cycle(self):
        """执行睡眠周期 (记忆巩固过程)"""
        print("\n[睡眠] 开始记忆巩固周期...")
        print("-" * 50)
        
        # 1. 清理瞬时记忆
        print("[阶段1] 清理瞬时记忆...")
        expired = self.ultra_short_term.cleanup()
        print(f"    清理了 {len(expired)} 条过期瞬时记忆")
        
        # 2. 检查工作记忆中的巩固候选
        print("[阶段2] 检查工作记忆巩固候选...")
        candidates = self.working_memory.find_consolidation_candidates()
        print(f"    找到 {len(candidates)} 个巩固候选")
        
        # 3. 执行巩固
        print("[阶段3] 执行记忆巩固...")
        if candidates:
            consolidated = self.consolidator.consolidate_memories(candidates)
            print(f"    成功巩固 {len(consolidated)} 条记忆到长期存储")
            
            # 从工作记忆中移除已巩固的记忆
            for memory in candidates:
                if memory.id in self.working_memory.buffer:
                    del self.working_memory.buffer[memory.id]
                    self.working_memory.stats["transfer_to_long_term"] += 1
        else:
            print("    没有需要巩固的记忆")
        
        # 4. 修剪长期记忆
        print("[阶段4] 修剪长期记忆...")
        before_prune = len(self.consolidator.long_term_memories)
        self.consolidator.prune_long_term_memories()
        after_prune = len(self.consolidator.long_term_memories)
        pruned_count = before_prune - after_prune
        print(f"    修剪了 {pruned_count} 条长期记忆")
        
        # 5. 更新状态
        self.last_sleep_cycle = datetime.now()
        
        print("-" * 50)
        print("[完成] 睡眠周期完成!")
        
        # 返回统计信息
        return self.get_system_stats()
    
    def get_system_stats(self) -> Dict[str, Any]:
        """获取系统统计信息"""
        ultra_stats = self.ultra_short_term.get_stats()
        working_stats = self.working_memory.get_stats()
        long_term_stats = self.consolidator.get_stats()
        
        # 计算系统运行时间
        uptime = (datetime.now() - self.system_start_time).total_seconds()
        
        return {
            "system_uptime_seconds": uptime,
            "total_memories_processed": self.total_memories_processed,
            "last_sleep_cycle": self.last_sleep_cycle.isoformat() if self.last_sleep_cycle else None,
            "ultra_short_term": ultra_stats,
            "working_memory": working_stats,
            "long_term": long_term_stats
        }
    
    def debug_dump(self):
        """调试信息转储"""
        stats = self.get_system_stats()
        print("\n" + "=" * 70)
        print("增强记忆系统 - 调试信息")
        print("=" * 70)
        
        print(f"\n系统概览:")
        print(f"  运行时间: {stats['system_uptime_seconds']:.0f} 秒")
        print(f"  总处理记忆: {stats['total_memories_processed']}")
        print(f"  上次睡眠周期: {stats['last_sleep_cycle'] or '从未'}")

        print(f"\n瞬时记忆 ({stats['ultra_short_term']['current_size']}/{stats['ultra_short_term']['capacity']}):")
        for mem_id, (memory, access_time) in self.ultra_short_term.buffer.items():
            age = (datetime.now() - access_time).total_seconds()
            print(f"  - {mem_id[:8]}: {memory.content[:40]}... (已存 {age:.1f}秒)")

        print(f"\n工作记忆 ({stats['working_memory']['current_size']}/{stats['working_memory']['capacity']}):")
        for mem_id, memory in self.working_memory.buffer.items():
            activation = memory.calculate_decay()
            print(f"  - {mem_id[:8]}: {memory.type.value} - {memory.content[:40]}... (激活: {activation:.2f})")

        print(f"\n长期记忆 ({stats['long_term']['total_memories']}/{stats['long_term']['max_capacity']}):")
        latest = self.consolidator.long_term_memories[-5:] if self.consolidator.long_term_memories else []
        for memory in latest:
            print(f"  - {memory.id[:8]}: [{memory.type.value}] {memory.content[:40]}...")

        print("\n" + "=" * 70)


def test_enhanced_memory_system():
    """测试增强记忆系统"""
    print("=" * 70)
    print("增强记忆系统 - 测试运行")
    print("=" * 70)
    
    # 1. 初始化系统
    config = {
        "ultra_short_term": {
            "max_items": 5  # 减少以便测试
        },
        "working_memory": {
            "capacity": 10
        },
        "long_term": {
            "storage_path": "memory/test_long_term.json",
            "max_memories": 20
        }
    }
    
    memory_system = EnhancedMemorySystem(config)
    
    # 2. 创建测试记忆
    print("\n[测试] 创建测试记忆...")
    
    test_memories = [
        ("量子计算是未来的关键技术，使用量子比特进行并行计算", 0.9, MemoryType.FACT, "学习笔记", ["量子", "技术"], 0.8),
        ("我决定主要学习Qiskit，因为它有最好的文档", 0.8, MemoryType.DECISION, "个人选择", ["决策", "学习"], 0.5),
        ("今天编写了一个量子随机数生成器，非常有趣", 0.7, MemoryType.EXPERIENCE, "日常记录", ["编程", "量子"], 0.9),
        ("错误：Python环境缺少qiskit模块，需要安装", 0.5, MemoryType.LOG, "开发日志", ["错误", "python"], -0.3),
        ("GitHub项目需要更好的文档和测试", 0.6, MemoryType.OPINION, "项目反馈", ["github", "开发"], 0.2),
        ("def quantum_circuit(): qc = QuantumCircuit(2)", 0.8, MemoryType.CODE, "代码片段", ["python", "代码"], 0.4),
        ("下周三下午3点有量子算法课", 0.9, MemoryType.FACT, "日程提醒", ["课程", "时间"], 0.7),
        ("我认为Python比Java更适合量子编程", 0.5, MemoryType.OPINION, "技术观点", ["编程", "语言"], 0.1),
    ]
    
    for content, importance, mem_type, source, tags, emotion in test_memories:
        mem_id = memory_system.encode_memory(content, importance, mem_type, source, tags, emotion)
        print(f"  编码: {mem_id[:8]} - {content[:40]}...")
    
    # 3. 显示初始状态
    print("\n[状态] 初始系统状态:")
    memory_system.debug_dump()
    
    # 4. 等待并模拟时间流逝
    print("\n[模拟] 等待5秒模拟时间流逝...")
    import time
    time.sleep(5)
    
    # 手动更新一些记忆的访问时间以便测试
    ultra_ids = list(memory_system.ultra_short_term.buffer.keys())
    if ultra_ids:
        memory_system.ultra_short_term.get(ultra_ids[0])
    
    # 5. 执行查询测试
    print("\n[查询] 测试记忆检索...")
    
    queries = [
        "量子",
        "编程",
        "错误",
        "Python"
    ]
    
    for query in queries:
        print(f"\n  查询: '{query}'")
        results = memory_system.query(query, top_k=3)
        for mem, score in results:
            print(f"    - 分数 {score:.3f}: {mem.content[:50]}... [{mem.type.value}]")
    
    # 6. 执行睡眠周期 (记忆巩固)
    print("\n" + "=" * 50)
    memory_system.perform_sleep_cycle()
    
    # 7. 显示最终状态
    print("\n[状态] 睡眠周期后系统状态:")
    final_stats = memory_system.get_system_stats()
    print(f"  瞬时记忆: {final_stats['ultra_short_term']['current_size']}")
    print(f"  工作记忆: {final_stats['working_memory']['current_size']}")
    print(f"  长期记忆: {final_stats['long_term']['total_memories']}")
    print(f"  总处理: {final_stats['total_memories_processed']}")
    
    print("\n" + "=" * 70)
    print("测试完成!")
    print("=" * 70)
    
    # 清理测试文件
    test_file = "memory/test_long_term.json"
    if os.path.exists(test_file):
        os.remove(test_file)
        print(f"[清理] 已删除测试文件: {test_file}")


if __name__ == "__main__":
    test_enhanced_memory_system()