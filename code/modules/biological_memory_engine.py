# 这一行代码是常见的 shebang 用法（#!/usr/bin/env python3），用于声明脚本由 Python 3 解释器运行。优点是可以在类 Unix 系统下让脚本直接以可执行文件方式运行，增加了兼容性和可移植性。缺点是对于 Windows 系统，这一行不会被实际执行，没有直接作用，而且如果项目主要运行在 Windows 环境里可以省略。不过，保持一致性和良好的跨平台习惯，建议保留该行，对整个工程风格和平台适应性都有正面作用。
"""
OpenClaw生物学启发记忆引擎 - 核心框架

整合6个记忆模块的统一实现：
1. SensoryRegistration (感觉登记)
2. WorkingMemory (工作记忆) 
3. EmotionalAppraisal (情绪评估)
4. ConsolidationPruning (巩固修剪)
5. LongTermStorage (长期存储)
6. RecallAssociation (关联检索)

基于生物学记忆理论构建的智能记忆系统。
"""

import json
import logging
import uuid
import time
import warnings
from abc import ABC, abstractmethod
from collections import defaultdict
from dataclasses import dataclass, field, asdict, fields
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union, Callable
from pathlib import Path

import numpy as np

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================================
# 数据类型定义
# ============================================================================

class MemoryStatus(str, Enum):
    """记忆状态枚举"""
    RAW = "raw"                     # 原始输入
    REGISTERED = "registered"       # 感觉登记完成
    ENCODED = "encoded"            # 工作记忆编码完成
    APPRAISED = "appraised"        # 情绪评估完成
    CONSOLIDATED = "consolidated"  # 巩固修剪完成
    STORED = "stored"              # 长期存储完成
    ARCHIVED = "archived"          # 已归档

class MemoryType(str, Enum):
    """记忆类型枚举"""
    FACT = "fact"                   # 事实信息
    DECISION = "decision"          # 决策过程
    OPINION = "opinion"            # 主观观点
    INSTRUCTION = "instruction"    # 操作指令
    EMOTIONAL = "emotional"        # 情感记忆
    EPISODIC = "episodic"          # 情景记忆
    SEMANTIC = "semantic"          # 语义记忆


@dataclass
class MemoryItem:
    """统一记忆数据单元"""
    
    # 核心标识
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    content: str = ""               # 原始内容文本
    content_type: str = "text"     # 内容类型
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    # 处理状态
    status: MemoryStatus = MemoryStatus.RAW
    confidence: float = 0.5        # 置信度 [0, 1]
    source: str = "unknown"        # 数据来源
    
    # 特征表示
    features: Dict[str, Any] = field(default_factory=dict)  # 原始特征
    embedding: Optional[List[float]] = None  # 语义向量
    embedding_model: str = "default"
    
    # 模块处理数据
    sensory_tags: List[str] = field(default_factory=list)      # 感觉标记
    working_metadata: Dict[str, Any] = field(default_factory=dict)  # 工作记忆元数据
    emotional_scores: Dict[str, float] = field(default_factory=dict)  # 情绪评分
    consolidation_info: Dict[str, Any] = field(default_factory=dict)  # 巩固信息
    storage_location: Dict[str, str] = field(default_factory=dict)    # 存储位置
    
    # 索引与检索
    memory_type: MemoryType = MemoryType.FACT  # 记忆类型
    importance: float = 0.5                    # 重要性 [0, 1]
    keywords: List[str] = field(default_factory=list)      # 关键词
    categories: List[str] = field(default_factory=list)    # 分类标签
    relations: List[str] = field(default_factory=list)     # 关联记忆ID
    
    # 生命周期管理
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    access_count: int = 0                      # 访问次数
    last_accessed: Optional[str] = None        # 最后访问时间
    
    # 遗忘曲线参数
    strength: float = 1.0                      # 记忆强度 [0, 1]
    decay_rate: float = 0.01                   # 衰减率
    last_strength_update: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典（可序列化）"""
        result = asdict(self)
        # 处理枚举类型
        result['status'] = self.status.value
        result['memory_type'] = self.memory_type.value
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MemoryItem':
        """从字典创建实例"""
        # 处理枚举类型
        if 'status' in data and isinstance(data['status'], str):
            data['status'] = MemoryStatus(data['status'])
        if 'memory_type' in data and isinstance(data['memory_type'], str):
            data['memory_type'] = MemoryType(data['memory_type'])
        return cls(**data)
    
    def update_timestamp(self):
        """更新时间戳"""
        self.updated_at = datetime.now().isoformat()
        
    def increment_access(self):
        """增加访问计数"""
        self.access_count += 1
        self.last_accessed = datetime.now().isoformat()
        self.update_timestamp()


@dataclass
class MemoryContext:
    """记忆处理上下文"""
    
    # 环境上下文
    processing_time: str = field(default_factory=lambda: datetime.now().isoformat())
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: Optional[str] = None
    
    # 认知状态
    attention_focus: List[str] = field(default_factory=list)
    emotional_state: Dict[str, float] = field(default_factory=dict)
    working_memory_load: float = 0.0  # [0, 1]
    
    # 处理历史
    processing_path: List[str] = field(default_factory=list)
    module_stats: Dict[str, Dict] = field(default_factory=dict)
    
    def update_path(self, module_name: str):
        """更新处理路径"""
        self.processing_path.append(module_name)
        
    def get_current_emotion(self) -> Dict[str, float]:
        """获取当前情绪状态"""
        default = {"valence": 0.0, "arousal": 0.0, "dominance": 0.0}
        default.update(self.emotional_state)
        return default


@dataclass  
class MemoryQuery:
    """记忆检索查询"""
    
    query_text: Optional[str] = None
    query_vector: Optional[List[float]] = None
    query_context: Optional[MemoryContext] = None
    
    # 过滤条件
    content_types: List[str] = field(default_factory=list)
    time_range: Optional[Tuple[str, str]] = None  # ISO格式时间范围
    categories: List[str] = field(default_factory=list)
    min_confidence: float = 0.0
    min_importance: float = 0.0
    
    # 检索配置
    max_results: int = 10
    similarity_threshold: float = 0.0
    retrieval_mode: str = "hybrid"  # semantic, temporal, causal, emotional, hybrid
    
    # 混合权重
    weights: Dict[str, float] = field(default_factory=lambda: {
        "semantic": 0.4,
        "temporal": 0.3, 
        "causal": 0.2,
        "emotional": 0.1
    })
    
    def validate(self) -> bool:
        """验证查询有效性"""
        if not self.query_text and self.query_vector is None:
            return False
        return True


@dataclass
class MemoryResult:
    """处理结果"""
    
    success: bool = True
    status_code: int = 200
    message: str = ""
    
    data: Optional[Union[MemoryItem, List[MemoryItem], Dict[str, Any]]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    processing_time_ms: float = 0.0
    memory_used_mb: float = 0.0
    
    total_count: int = 0
    offset: int = 0
    limit: int = 0
    
    def with_data(self, data: Any) -> 'MemoryResult':
        """链式设置数据"""
        self.data = data
        return self
    
    def with_metadata(self, key: str, value: Any) -> 'MemoryResult':
        """链式添加元数据"""
        self.metadata[key] = value
        return self


# ============================================================================
# 基础模块接口
# ============================================================================

class MemoryModule(ABC):
    """记忆模块基类"""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        self.name = name
        self.config = config
        self.stats = {"process_count": 0, "error_count": 0, "avg_time_ms": 0.0}
        logger.info(f"模块初始化: {name}")
    
    @abstractmethod
    def process(self, memory_item: MemoryItem, context: Optional[MemoryContext] = None) -> MemoryResult:
        """处理记忆项"""
        pass
    
    def batch_process(self, memory_items: List[MemoryItem], 
                     context: Optional[MemoryContext] = None) -> MemoryResult:
        """批量处理默认实现（顺序处理）"""
        results = []
        start_time = time.time()
        
        for item in memory_items:
            result = self.process(item, context)
            if result.success and result.data:
                results.append(result.data)
        
        elapsed_ms = (time.time() - start_time) * 1000
        return MemoryResult(
            success=True,
            message=f"批量处理完成，成功 {len(results)}/{len(memory_items)}",
            data=results,
            metadata={
                "total_processed": len(memory_items),
                "successful": len(results),
                "elapsed_ms": elapsed_ms
            }
        )
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return self.stats.copy()
    
    def reset_stats(self):
        """重置统计"""
        self.stats = {"process_count": 0, "error_count": 0, "avg_time_ms": 0.0}
    
    def update_config(self, new_config: Dict[str, Any]) -> MemoryResult:
        """更新配置"""
        old_config = self.config.copy()
        self.config.update(new_config)
        logger.info(f"模块 {self.name} 配置已更新")
        return MemoryResult(
            success=True,
            message="配置更新成功",
            metadata={"old_config": old_config, "new_config": self.config}
        )
    
    def _record_process(self, elapsed_ms: float, success: bool = True):
        """记录处理统计"""
        self.stats["process_count"] += 1
        if not success:
            self.stats["error_count"] += 1
        
        # 更新平均时间（指数移动平均）
        old_avg = self.stats.get("avg_time_ms", 0.0)
        self.stats["avg_time_ms"] = old_avg * 0.7 + elapsed_ms * 0.3


class SensoryRegistration(MemoryModule):
    """感觉登记模块"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__("sensory_registration", config)
        
        # 缓冲区配置
        self.buffer_size = config.get("buffer_size", 1000)
        self.retention_ms = config.get("retention_ms", {
            "visual": 500,
            "auditory": 4000,
            "text": 2000
        })
        
        self.channels = config.get("channels", ["text"])
        self.buffers = {channel: [] for channel in self.channels}
        
        # 特征提取器
        self.feature_extractors = config.get("feature_extractors", {})
        
        # 注意规则
        self.attention_rules = config.get("attention_rules", [])
        
        logger.info(f"感觉登记模块初始化，支持通道: {self.channels}")
    
    def process(self, memory_item: MemoryItem, context: Optional[MemoryContext] = None) -> MemoryResult:
        """处理感觉输入"""
        start_time = time.time()
        
        try:
            # 确定通道类型
            channel = self._detect_channel(memory_item)
            
            # 特征提取
            features = self._extract_features(memory_item.content, channel)
            memory_item.features = features
            
            # 注意过滤
            attention_score = self._apply_attention_rules(memory_item, channel)
            
            # 添加到缓冲区
            timestamp = datetime.now()
            buffered_item = {
                "item": memory_item,
                "channel": channel,
                "timestamp": timestamp,
                "attention_score": attention_score
            }
            
            self.buffers[channel].append(buffered_item)
            
            # 维护缓冲区大小
            if len(self.buffers[channel]) > self.buffer_size:
                self.buffers[channel] = self.buffers[channel][-self.buffer_size:]
            
            # 更新记忆项状态
            memory_item.status = MemoryStatus.REGISTERED
            memory_item.sensory_tags = [f"channel:{channel}", f"attention:{attention_score:.2f}"]
            memory_item.update_timestamp()
            
            elapsed_ms = (time.time() - start_time) * 1000
            self._record_process(elapsed_ms, True)
            
            return MemoryResult(
                success=True,
                message=f"感觉登记完成（通道: {channel}, 注意力: {attention_score:.2f}）",
                data=memory_item,
                metadata={
                    "channel": channel,
                    "attention_score": attention_score,
                    "buffer_size": len(self.buffers[channel])
                }
            )
            
        except Exception as e:
            elapsed_ms = (time.time() - start_time) * 1000
            self._record_process(elapsed_ms, False)
            logger.error(f"感觉登记失败: {e}")
            return MemoryResult(
                success=False,
                status_code=500,
                message=f"感觉登记失败: {str(e)}"
            )
    
    def _detect_channel(self, memory_item: MemoryItem) -> str:
        """检测输入通道"""
        for channel in self.channels:
            if channel.lower() in memory_item.content_type.lower():
                return channel
        return "text"  # 默认文本通道
    
    def _extract_features(self, content: str, channel: str) -> Dict[str, Any]:
        """提取特征"""
        features = {}
        
        # 基础特征
        features["length"] = len(content)
        features["word_count"] = len(content.split())
        
        # 通道特定特征
        if channel == "text":
            # 文本特征
            features["has_questions"] = "?" in content
            features["has_exclamations"] = "!" in content
            # 简单关键词检测
            keywords = ["错误", "警告", "重要", "紧急"]
            features["keyword_matches"] = sum(1 for kw in keywords if kw in content)
        
        return features
    
    def _apply_attention_rules(self, memory_item: MemoryItem, channel: str) -> float:
        """应用注意力规则"""
        base_score = 0.5
        
        for rule in self.attention_rules:
            pattern = rule.get("pattern", "")
            priority = rule.get("priority", 1.0)
            
            if pattern and pattern in memory_item.content:
                base_score *= priority
        
        # 通道权重
        channel_weights = {"text": 1.0, "audio": 1.2, "visual": 1.5}
        base_score *= channel_weights.get(channel, 1.0)
        
        return min(2.0, max(0.0, base_score))  # 限制在[0, 2]范围内
    
    def flush_buffer(self, channel: Optional[str] = None) -> List[MemoryItem]:
        """刷新缓冲区"""
        if channel:
            items = [buf["item"] for buf in self.buffers[channel]]
            self.buffers[channel] = []
            return items
        else:
            all_items = []
            for ch in self.buffers:
                all_items.extend([buf["item"] for buf in self.buffers[ch]])
                self.buffers[ch] = []
            return all_items


# ============================================================================
# 适配现有模块（简化接口）
# ============================================================================

class WorkingMemoryAdapter(MemoryModule):
    """工作记忆模块适配器"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__("working_memory", config)
        
        # 尝试导入现有work_memory模块
        try:
            from working_memory_enhanced import EnhancedWorkingMemory as WorkingMemory
            self.backend = WorkingMemory(
                capacity=config.get("capacity", 20),
                embedding_backend=config.get("embedding_backend", "ollama")
            )
            self.has_backend = True
        except ImportError:
            logger.warning("未能导入working_memory_fixed，使用简化实现")
            self.backend = None
            self.has_backend = False
            
        # 本地缓冲区
        self.buffer = []
        self.capacity = config.get("capacity", 20)
        
    def process(self, memory_item: MemoryItem, context: Optional[MemoryContext] = None) -> MemoryResult:
        """工作记忆编码"""
        start_time = time.time()
        
        try:
            # 如果有后端，使用后端编码
            if self.has_backend and self.backend:
                # 转换为后端需要的格式
                encoded = self.backend.encode(
                    content=memory_item.content[:500],
                    importance=memory_item.importance,
                    source=memory_item.source
                )
                
                # 更新记忆项
                memory_item.working_metadata = {
                    "encoded_id": encoded.id,
                    "chunk_type": encoded.chunk_type.value if hasattr(encoded, 'chunk_type') else "unknown",
                    "features": encoded.semantic_features if hasattr(encoded, 'semantic_features') else []
                }
                
                if hasattr(encoded, 'embedding_vector') and encoded.embedding_vector is not None:
                    memory_item.embedding = encoded.embedding_vector.tolist()
                    memory_item.embedding_model = "working_memory"
            
            # 添加到缓冲区（LRU管理）
            memory_item.status = MemoryStatus.ENCODED
            memory_item.update_timestamp()
            
            self.buffer.append(memory_item)
            if len(self.buffer) > self.capacity:
                self.buffer = self.buffer[-self.capacity:]
            
            elapsed_ms = (time.time() - start_time) * 1000
            self._record_process(elapsed_ms, True)
            
            return MemoryResult(
                success=True,
                message="工作记忆编码完成",
                data=memory_item,
                metadata={
                    "buffer_size": len(self.buffer),
                    "capacity": self.capacity,
                    "has_backend": self.has_backend
                }
            )
            
        except Exception as e:
            elapsed_ms = (time.time() - start_time) * 1000
            self._record_process(elapsed_ms, False)
            logger.error(f"工作记忆编码失败: {e}")
            return MemoryResult(
                success=False,
                status_code=500,
                message=f"工作记忆编码失败: {str(e)}"
            )


class EmotionalAppraisalAdapter(MemoryModule):
    """情绪评估模块适配器"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__("emotional_appraisal", config)
        
        # 尝试导入现有情绪模块
        try:
            from emotional_appraisal import EmotionAnalyzer
            self.analyzer = EmotionAnalyzer()
            self.has_analyzer = True
        except ImportError:
            logger.warning("未能导入emotion_analyzer，使用简化实现")
            self.analyzer = None
            self.has_analyzer = False
            
        # 简化情绪分析规则
        self.rules = config.get("rules", {})
        
    def process(self, memory_item: MemoryItem, context: Optional[MemoryContext] = None) -> MemoryResult:
        """情绪评估"""
        start_time = time.time()
        
        try:
            # 如果有分析器，使用分析器
            if self.has_analyzer and self.analyzer:
                # 假设analyzer有analyze方法
                emotion_result = self.analyzer.analyze(memory_item.content)
                memory_item.emotional_scores = emotion_result
            else:
                # 简化情绪分析
                memory_item.emotional_scores = self._simple_emotion_analysis(memory_item.content)
            
            # 计算基于情绪的重要性
            emotional_importance = self._calculate_emotional_importance(memory_item.emotional_scores)
            memory_item.importance = (memory_item.importance + emotional_importance) / 2
            
            # 情绪分类
            memory_type = self._classify_by_emotion(memory_item.emotional_scores)
            memory_item.memory_type = memory_type
            
            memory_item.status = MemoryStatus.APPRAISED
            memory_item.update_timestamp()
            
            elapsed_ms = (time.time() - start_time) * 1000
            self._record_process(elapsed_ms, True)
            
            return MemoryResult(
                success=True,
                message=f"情绪评估完成（类型: {memory_type.value}）",
                data=memory_item,
                metadata={
                    "emotional_scores": memory_item.emotional_scores,
                    "adjusted_importance": memory_item.importance,
                    "has_analyzer": self.has_analyzer
                }
            )
            
        except Exception as e:
            elapsed_ms = (time.time() - start_time) * 1000
            self._record_process(elapsed_ms, False)
            logger.error(f"情绪评估失败: {e}")
            return MemoryResult(
                success=False,
                status_code=500,
                message=f"情绪评估失败: {str(e)}"
            )
    
    def _simple_emotion_analysis(self, text: str) -> Dict[str, float]:
        """简化情绪分析"""
        # 基本情绪关键词
        positive_words = ["好", "成功", "快乐", "高兴", "满意", "喜欢"]
        negative_words = ["坏", "失败", "悲伤", "生气", "不满", "讨厌"]
        arousal_words = ["紧急", "重要", "立刻", "马上", "危险"]
        
        text_lower = text.lower()
        
        positive_score = sum(1 for word in positive_words if word in text_lower) / max(len(positive_words), 1)
        negative_score = sum(1 for word in negative_words if word in text_lower) / max(len(negative_words), 1)
        arousal_score = sum(1 for word in arousal_words if word in text_lower) / max(len(arousal_words), 1)
        
        # PAD模型简化
        valence = positive_score - negative_score  # 愉悦度 [-1, 1]
        arousal = arousal_score  # 激活度 [0, 1]
        dominance = 0.5  # 支配度（默认）
        
        return {
            "valence": max(-1.0, min(1.0, valence)),
            "arousal": max(0.0, min(1.0, arousal)),
            "dominance": dominance,
            "positive_score": positive_score,
            "negative_score": negative_score,
            "overall_emotion": "positive" if valence > 0 else "negative" if valence < 0 else "neutral"
        }
    
    def _calculate_emotional_importance(self, scores: Dict[str, float]) -> float:
        """基于情绪计算重要性"""
        # 高唤醒度或极端效价增加重要性
        arousal = scores.get("arousal", 0.0)
        valence_abs = abs(scores.get("valence", 0.0))
        
        importance = 0.5 + (arousal * 0.3) + (valence_abs * 0.2)
        return min(1.0, max(0.0, importance))
    
    def _classify_by_emotion(self, scores: Dict[str, float]) -> MemoryType:
        """基于情绪分类记忆类型"""
        if scores.get("overall_emotion") == "positive" and scores.get("arousal", 0.0) > 0.7:
            return MemoryType.EMOTIONAL
        elif "事实" in scores.get("keywords", ""):
            return MemoryType.FACT
        elif "决定" in scores.get("keywords", ""):
            return MemoryType.DECISION
        else:
            return MemoryType.FACT


class ConsolidationPruningAdapter(MemoryModule):
    """巩固修剪模块适配器"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__("consolidation_pruning", config)
        
        # 尝试导入现有consolidation模块
        try:
            from memory_engine.modules.consolidation_pruning.consolidation_pruning import ConsolidationPruning
            self.consolidator = ConsolidationPruning(config)
            self.has_consolidator = True
        except ImportError:
            logger.warning("未能导入consolidation_pruning，使用简化实现")
            self.consolidator = None
            self.has_consolidator = False
            
        # 遗忘曲线参数
        self.decay_rates = config.get("decay_rates", {
            "fact": 0.01,
            "decision": 0.03,
            "opinion": 0.05,
            "instruction": 0.02,
            "emotional": 0.04
        })
        
    def process(self, memory_item: MemoryItem, context: Optional[MemoryContext] = None) -> MemoryResult:
        """记忆巩固"""
        start_time = time.time()
        
        try:
            # 更新记忆强度（遗忘曲线）
            strength_before = memory_item.strength
            memory_item = self._update_strength(memory_item)
            strength_after = memory_item.strength
            
            # 计算重要性分数
            importance_score = self._calculate_importance_score(memory_item)
            memory_item.importance = importance_score
            
            # 应用巩固效果
            memory_item.consolidation_info = {
                "strength_before": strength_before,
                "strength_after": strength_after,
                "importance_score": importance_score,
                "decay_rate": memory_item.decay_rate,
                "consolidated_at": datetime.now().isoformat()
            }
            
            memory_item.status = MemoryStatus.CONSOLIDATED
            memory_item.update_timestamp()
            
            elapsed_ms = (time.time() - start_time) * 1000
            self._record_process(elapsed_ms, True)
            
            return MemoryResult(
                success=True,
                message=f"记忆巩固完成（强度: {memory_item.strength:.3f}, 重要性: {importance_score:.3f}）",
                data=memory_item,
                metadata={
                    "strength": memory_item.strength,
                    "importance": importance_score,
                    "decay_rate": memory_item.decay_rate,
                    "has_consolidator": self.has_consolidator
                }
            )
            
        except Exception as e:
            elapsed_ms = (time.time() - start_time) * 1000
            self._record_process(elapsed_ms, False)
            logger.error(f"记忆巩固失败: {e}")
            return MemoryResult(
                success=False,
                status_code=500,
                message=f"记忆巩固失败: {str(e)}"
            )
    
    def _update_strength(self, memory_item: MemoryItem) -> MemoryItem:
        """更新记忆强度（基于遗忘曲线）"""
        # 计算时间差（小时）
        try:
            created = datetime.fromisoformat(memory_item.created_at)
            now = datetime.now()
            hours_passed = (now - created).total_seconds() / 3600
        except:
            hours_passed = 24.0  # 默认24小时
        
        # 获取衰减率
        decay_rate = self.decay_rates.get(memory_item.memory_type.value, 0.03)
        memory_item.decay_rate = decay_rate
        
        # 应用指数衰减：R(t) = R₀ * exp(-λ*t)
        initial_strength = 1.0  # 假设初始强度为1.0
        current_strength = initial_strength * np.exp(-decay_rate * hours_passed)
        
        # 考虑访问次数的影响（每次访问略微增加强度）
        access_boost = 1.0 + (memory_item.access_count * 0.05)
        current_strength = min(1.0, current_strength * access_boost)
        
        memory_item.strength = current_strength
        memory_item.last_strength_update = datetime.now().isoformat()
        
        return memory_item
    
    def _calculate_importance_score(self, memory_item: MemoryItem) -> float:
        """计算重要性分数"""
        base_score = memory_item.importance
        
        # 情绪因素
        emotional_factor = 1.0
        if memory_item.emotional_scores:
            arousal = memory_item.emotional_scores.get("arousal", 0.0)
            valence_abs = abs(memory_item.emotional_scores.get("valence", 0.0))
            emotional_factor = 0.7 + (arousal * 0.2) + (valence_abs * 0.1)
        
        # 强度因素
        strength_factor = 0.5 + (memory_item.strength * 0.5)
        
        # 访问频率因素
        access_factor = 1.0 + np.log1p(memory_item.access_count) * 0.1
        
        # 综合分数
        importance = base_score * emotional_factor * strength_factor * access_factor
        
        return min(1.0, max(0.0, importance))


class LongTermStorageAdapter(MemoryModule):
    """长期存储模块适配器"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__("long_term_storage", config)
        
        # 存储后端配置
        self.storage_backend = config.get("storage_backend", "json")
        self.storage_path = Path(config.get("storage_path", "./memory_storage"))
        self.max_size_gb = config.get("max_size_gb", 10.0)
        
        # 创建存储目录
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # 初始化存储
        self.memories = {}
        self._load_existing_memories()
        
    def process(self, memory_item: MemoryItem, context: Optional[MemoryContext] = None) -> MemoryResult:
        """长期存储"""
        start_time = time.time()
        
        try:
            # 检查存储限制
            if len(self.memories) >= 10000:  # 简单限制
                logger.warning("存储接近上限，可能需要修剪")
            
            # 分配存储位置
            storage_id = memory_item.id
            storage_path = self.storage_path / f"{storage_id}.json"
            memory_item.storage_location = {
                "id": storage_id,
                "path": str(storage_path),
                "backend": self.storage_backend,
                "stored_at": datetime.now().isoformat()
            }
            
            # 存储到内存和磁盘
            self.memories[storage_id] = memory_item.to_dict()
            
            # 异步写入磁盘（简化实现：同步写入）
            with open(storage_path, 'w', encoding='utf-8') as f:
                json.dump(memory_item.to_dict(), f, ensure_ascii=False, indent=2)
            
            memory_item.status = MemoryStatus.STORED
            memory_item.update_timestamp()
            
            elapsed_ms = (time.time() - start_time) * 1000
            self._record_process(elapsed_ms, True)
            
            return MemoryResult(
                success=True,
                message=f"长期存储完成（ID: {storage_id}）",
                data=memory_item,
                metadata={
                    "storage_id": storage_id,
                    "storage_path": str(storage_path),
                    "total_stored": len(self.memories),
                    "backend": self.storage_backend
                }
            )
            
        except Exception as e:
            elapsed_ms = (time.time() - start_time) * 1000
            self._record_process(elapsed_ms, False)
            logger.error(f"长期存储失败: {e}")
            return MemoryResult(
                success=False,
                status_code=500,
                message=f"长期存储失败: {str(e)}"
            )
    
    def _load_existing_memories(self):
        """加载已存在的记忆"""
        try:
            for file_path in self.storage_path.glob("*.json"):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    memory_id = data.get("id", file_path.stem)
                    self.memories[memory_id] = data
                except Exception as e:
                    logger.warning(f"加载记忆文件失败 {file_path}: {e}")
            
            logger.info(f"从磁盘加载了 {len(self.memories)} 条记忆")
        except Exception as e:
            logger.error(f"加载记忆失败: {e}")
    
    def retrieve(self, query: MemoryQuery) -> MemoryResult:
        """检索记忆（简单实现）"""
        # 这里是简化实现，实际应该用向量索引
        results = []
        
        for memory_data in self.memories.values():
            # 转换为MemoryItem
            memory_item = MemoryItem.from_dict(memory_data)
            
            # 基础过滤
            if query.min_confidence > memory_item.confidence:
                continue
            if query.min_importance > memory_item.importance:
                continue
            
            results.append(memory_item)
        
        # 限制结果数量
        results = results[:query.max_results]
        
        return MemoryResult(
            success=True,
            message=f"找到 {len(results)} 条记忆",
            data=results,
            metadata={"total_found": len(results)}
        )


class RecallAssociationAdapter(MemoryModule):
    """关联检索模块适配器"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__("recall_association", config)
        
        # 尝试导入现有recall模块
        try:
            from recall_association import RecallAssociation
            self.recaller = RecallAssociation(config)
            self.has_recaller = True
        except ImportError:
            logger.warning("未能导入recall_association，使用简化实现")
            self.recaller = None
            self.has_recaller = False
            
        # 检索模式
        self.retrieval_modes = config.get("retrieval_modes", ["semantic", "temporal", "hybrid"])
        self.default_weights = config.get("default_weights", {
            "semantic": 0.4,
            "temporal": 0.3,
            "causal": 0.2,
            "emotional": 0.1
        })
        
    def process(self, memory_item: MemoryItem, context: Optional[MemoryContext] = None) -> MemoryResult:
        """处理查询（用于检索）"""
        # 此模块主要处理查询，但为统一接口实现process
        return MemoryResult(
            success=True,
            message="RecallAssociation模块准备好接收查询",
            data=memory_item
        )
    
    def retrieve(self, query: MemoryQuery, storage_adapter: LongTermStorageAdapter) -> MemoryResult:
        """关联检索"""
        start_time = time.time()
        
        try:
            # 如果有后端，使用后端检索
            if self.has_recaller and self.recaller:
                # 使用混合检索（recall_association模块使用RetrievalQuery接口）
                try:
                    from recall_association import RetrievalQuery
                    # 构建RetrievalQuery对象
                    retrieval_query = RetrievalQuery(
                        query_text=query.query_text if query.query_text else "",
                        query_type=None,
                        max_results=query.max_results,
                        weights=query.weights,
                        time_decay_alpha=self.config.get("time_decay_alpha", 0.01)
                    )
                    # 执行混合检索
                    hybrid_results = self.recaller.retrieve_hybrid(retrieval_query)
                    
                    # 将RetrievalResult转换为MemoryItem（简化转换）
                    memory_items = []
                    for result in hybrid_results[:query.max_results]:
                        # 创建简单的MemoryItem表示
                        memory = MemoryItem(
                            content=result.memory.content,
                            memory_type=MemoryType.FACT,
                            importance=result.total_score,
                            timestamp=result.memory.timestamp,
                            confidence=result.memory.confidence,
                            emotional_scores={"overall": result.memory.emotional_weight}
                        )
                        memory_items.append(memory)
                    
                    elapsed_ms = (time.time() - start_time) * 1000
                    self._record_process(elapsed_ms, True)
                    
                    return MemoryResult(
                        success=True,
                        message=f"关联检索完成，找到 {len(memory_items)} 条相关记忆",
                        data=memory_items,
                        metadata={
                            "total_found": len(memory_items),
                            "top_score": memory_items[0].importance if memory_items else 0.0,
                            "retrieval_mode": "hybrid",
                            "elapsed_ms": elapsed_ms
                        }
                    )
                except Exception as recall_error:
                    logger.warning(f"高级关联检索失败，使用简化实现: {recall_error}")
                    # 回退到简化实现
                    pass
            
            # 简化检索实现
            
            # 1. 从存储获取所有记忆
            all_memories = []
            for memory_data in storage_adapter.memories.values():
                all_memories.append(MemoryItem.from_dict(memory_data))
            
            print(f"[DEBUG RecallAssociation] 从存储加载记忆数量: {len(all_memories)}")
            
            if not all_memories:
                return MemoryResult(
                    success=True,
                    message="没有存储的记忆",
                    data=[],
                    metadata={"total_found": 0}
                )
            
            # 2. 应用基础过滤（暂时禁用）
            filtered = all_memories
            print(f"[DEBUG RecallAssociation] 过滤后记忆数量: {len(filtered)}")
            
            # 3. 计算相似度得分（简化）
            scored_results = []
            query_text = query.query_text or ""
            
            for memory in filtered:
                score = self._calculate_similarity(query_text, memory.content)
                # 调试：如果分数 > 0，则记录
                if score > 0:
                    print(f"[DEBUG RecallAssociation] 相似度分数 > 0: 查询='{query_text[:20]}'，内容='{memory.content[:30]}'，分数={score}")
                
                # 时间衰减因子
                time_decay = self._calculate_time_decay(memory.timestamp)
                
                # 情绪重要性因子
                emotion_factor = memory.emotional_scores.get("arousal", 0.5) * 0.5 + 0.5
                
                # 综合得分
                final_score = (score * 0.5) + (time_decay * 0.3) + (emotion_factor * 0.2)
                
                scored_results.append((memory, final_score))
            
            # 4. 排序和限制
            scored_results.sort(key=lambda x: x[1], reverse=True)
            results = [item[0] for item in scored_results[:query.max_results]]
            
            elapsed_ms = (time.time() - start_time) * 1000
            self._record_process(elapsed_ms, True)
            
            return MemoryResult(
                success=True,
                message=f"检索完成，找到 {len(results)} 条相关记忆",
                data=results,
                metadata={
                    "total_scored": len(scored_results),
                    "top_score": scored_results[0][1] if scored_results else 0.0,
                    "retrieval_mode": query.retrieval_mode,
                    "elapsed_ms": elapsed_ms
                }
            )
            
        except Exception as e:
            elapsed_ms = (time.time() - start_time) * 1000
            self._record_process(elapsed_ms, False)
            logger.error(f"关联检索失败: {e}")
            return MemoryResult(
                success=False,
                status_code=500,
                message=f"关联检索失败: {str(e)}"
            )
    
    def _calculate_similarity(self, query: str, content: str) -> float:
        """计算文本相似度（支持中文、英文）"""
        if not query or not content:
            return 0.0
        
        # 方法1：如果查询和内容都是英文（包含空格），使用单词级 Jaccard 相似度
        if ' ' in query or ' ' in content:
            query_words = set(query.lower().split())
            content_words = set(content.lower().split())
            if query_words and content_words:
                intersection = len(query_words & content_words)
                union = len(query_words | content_words)
                if union > 0:
                    return intersection / union
        
        # 方法2：字符级 n-gram 相似度（适用于中文或无空格文本）
        # 使用 bigram（2-gram）提高准确性
        def get_ngrams(text, n=2):
            return [text[i:i+n] for i in range(len(text)-n+1)] if len(text) >= n else [text]
        
        # 处理短文本：如果文本很短，使用 unigram
        n = 2
        if len(query) < 2 or len(content) < 2:
            n = 1
        
        query_ngrams = set(get_ngrams(query.lower(), n))
        content_ngrams = set(get_ngrams(content.lower(), n))
        
        if not query_ngrams or not content_ngrams:
            return 0.0
        
        intersection = len(query_ngrams & content_ngrams)
        union = len(query_ngrams | content_ngrams)
        
        return intersection / union if union > 0 else 0.0
    
    def _calculate_time_decay(self, timestamp: str) -> float:
        """计算时间衰减因子（越近越大）"""
        try:
            memory_time = datetime.fromisoformat(timestamp)
            now = datetime.now()
            hours_diff = (now - memory_time).total_seconds() / 3600
            
            # 指数衰减：24小时内记忆保持较高权重
            decay_factor = np.exp(-hours_diff / 24.0)
            return decay_factor
        except:
            return 0.5  # 默认值


# ============================================================================
# 中央协调管理器
# ============================================================================

class CentralCoordinator:
    """中央协调管理器"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        
        # 模块注册表
        self.modules: Dict[str, MemoryModule] = {}
        
        # 处理管道顺序
        self.processing_pipeline = self.config.get("pipeline", [
            "sensory_registration",
            "working_memory",
            "emotional_appraisal", 
            "consolidation_pruning",
            "long_term_storage"
        ])
        
        # 事件系统
        self.event_handlers = defaultdict(list)
        
        # 初始化模块
        self._initialize_modules()
        
        logger.info(f"中央协调管理器初始化完成，管道: {self.processing_pipeline}")
    
    def _initialize_modules(self):
        """初始化所有模块"""
        module_configs = self.config.get("module_configs", {})
        
        # 感觉登记模块
        sensory_config = module_configs.get("sensory_registration", {
            "buffer_size": 1000,
            "channels": ["text"],
            "feature_extractors": {},
            "attention_rules": []
        })
        self.modules["sensory_registration"] = SensoryRegistration(sensory_config)
        
        # 工作记忆模块
        working_config = module_configs.get("working_memory", {
            "capacity": 20,
            "embedding_backend": "ollama"
        })
        self.modules["working_memory"] = WorkingMemoryAdapter(working_config)
        
        # 情绪评估模块
        emotional_config = module_configs.get("emotional_appraisal", {
            "rules": {}
        })
        self.modules["emotional_appraisal"] = EmotionalAppraisalAdapter(emotional_config)
        
        # 巩固修剪模块
        consolidation_config = module_configs.get("consolidation_pruning", {
            "decay_rates": {
                "fact": 0.01,
                "decision": 0.03,
                "opinion": 0.05,
                "instruction": 0.02,
                "emotional": 0.04
            }
        })
        self.modules["consolidation_pruning"] = ConsolidationPruningAdapter(consolidation_config)
        
        # 长期存储模块
        storage_config = module_configs.get("long_term_storage", {
            "storage_backend": "json",
            "storage_path": "./memory_storage",
            "max_size_gb": 10.0
        })
        self.modules["long_term_storage"] = LongTermStorageAdapter(storage_config)
        
        # 关联检索模块
        recall_config = module_configs.get("recall_association", {
            "retrieval_modes": ["semantic", "temporal", "hybrid"],
            "default_weights": {
                "semantic": 0.4,
                "temporal": 0.3,
                "causal": 0.2,
                "emotional": 0.1
            }
        })
        self.modules["recall_association"] = RecallAssociationAdapter(recall_config)
    
    def register_module(self, name: str, module: MemoryModule) -> bool:
        """注册新模块"""
        if name in self.modules:
            logger.warning(f"模块 {name} 已存在，将被替换")
        
        self.modules[name] = module
        
        # 如果不在管道中，添加到末尾
        if name not in self.processing_pipeline:
            self.processing_pipeline.append(name)
        
        logger.info(f"模块 {name} 注册成功")
        return True
    
    def unregister_module(self, name: str) -> bool:
        """注销模块"""
        if name not in self.modules:
            logger.warning(f"模块 {name} 不存在")
            return False
        
        del self.modules[name]
        
        # 从管道中移除
        if name in self.processing_pipeline:
            self.processing_pipeline.remove(name)
        
        logger.info(f"模块 {name} 注销成功")
        return True
    
    def process_memory(self, input_data: Any, context: Optional[MemoryContext] = None) -> MemoryResult:
        """处理记忆（完整管道）"""
        if context is None:
            context = MemoryContext()
        
        # 将输入转换为MemoryItem
        if isinstance(input_data, MemoryItem):
            memory_item = input_data
        elif isinstance(input_data, dict):
            memory_item = MemoryItem(**input_data)
        else:
            memory_item = MemoryItem(
                content=str(input_data),
                content_type="text",
                source="user_input"
            )
        
        # 记录开始处理
        context.update_path("start")
        self._publish_event("processing_start", {"memory_id": memory_item.id})
        
        # 执行管道
        current_item = memory_item
        for module_name in self.processing_pipeline:
            if module_name not in self.modules:
                logger.warning(f"模块 {module_name} 未注册，跳过")
                continue
            
            module = self.modules[module_name]
            
            # 特殊处理：跳过检索模块（只在查询时使用）
            if module_name == "recall_association":
                continue
            
            # 执行模块处理
            try:
                result = module.process(current_item, context)
                
                if not result.success:
                    logger.error(f"模块 {module_name} 处理失败: {result.message}")
                    # 继续管道，但记录错误
                    context.processing_path.append(f"{module_name}:error")
                    self._publish_event("module_error", {
                        "module": module_name,
                        "error": result.message,
                        "memory_id": current_item.id
                    })
                    continue
                
                if result.data and isinstance(result.data, MemoryItem):
                    current_item = result.data
                else:
                    # 如果模块返回了新的MemoryItem
                    current_item = result.data if isinstance(result.data, MemoryItem) else current_item
                
                context.update_path(module_name)
                self._publish_event(f"memory_{module_name}", {
                    "memory_id": current_item.id,
                    "module": module_name,
                    "status": current_item.status.value
                })
                
            except Exception as e:
                logger.error(f"模块 {module_name} 处理异常: {e}")
                context.processing_path.append(f"{module_name}:exception")
                self._publish_event("module_exception", {
                    "module": module_name,
                    "exception": str(e),
                    "memory_id": current_item.id
                })
        
        # 记录处理完成
        context.update_path("complete")
        self._publish_event("processing_complete", {
            "memory_id": current_item.id,
            "final_status": current_item.status.value,
            "processing_path": context.processing_path
        })
        
        return MemoryResult(
            success=True,
            message="记忆处理完成",
            data=current_item,
            metadata={
                "processing_path": context.processing_path,
                "final_status": current_item.status.value,
                "total_modules": len(self.processing_pipeline)
            }
        )
    
    def retrieve_memory(self, query: MemoryQuery, context: Optional[MemoryContext] = None) -> MemoryResult:
        """检索记忆"""
        if not query.validate():
            return MemoryResult(
                success=False,
                status_code=400,
                message="查询无效"
            )
        
        if context is None:
            context = MemoryContext()
        
        self._publish_event("retrieval_start", {"query": query.query_text})
        
        # 获取长期存储模块
        storage_module = self.modules.get("long_term_storage")
        if not storage_module:
            return MemoryResult(
                success=False,
                status_code=500,
                message="长期存储模块未找到"
            )
        
        # 获取关联检索模块
        recall_module = self.modules.get("recall_association")
        if not recall_module:
            # 如果没有检索模块，直接从存储检索
            if isinstance(storage_module, LongTermStorageAdapter):
                result = storage_module.retrieve(query)
            else:
                return MemoryResult(
                    success=False,
                    status_code=500,
                    message="检索模块不可用"
                )
        else:
            # 使用关联检索模块
            if isinstance(recall_module, RecallAssociationAdapter):
                result = recall_module.retrieve(query, storage_module)
            elif isinstance(storage_module, LongTermStorageAdapter):
                # 非 RecallAssociationAdapter 的检索模块：回退到长期存储的简单检索
                result = storage_module.retrieve(query)
            else:
                return MemoryResult(
                    success=False,
                    status_code=500,
                    message="检索模块类型不支持，且存储模块无法执行检索"
                )
        
        self._publish_event("retrieval_complete", {
            "query": query.query_text,
            "results_count": len(result.data) if isinstance(result.data, list) else 0,
            "success": result.success
        })
        
        return result
    
    def execute_pipeline(self, pipeline: List[str], memory_item: MemoryItem,
                        context: Optional[MemoryContext] = None) -> MemoryResult:
        """执行指定管道"""
        if context is None:
            context = MemoryContext()
        
        original_pipeline = self.processing_pipeline
        self.processing_pipeline = pipeline
        
        try:
            result = self.process_memory(memory_item, context)
        finally:
            self.processing_pipeline = original_pipeline
        
        return result
    
    def get_system_stats(self) -> Dict[str, Any]:
        """获取系统统计信息"""
        stats = {
            "modules": {},
            "total_processed": 0,
            "total_errors": 0,
            "avg_processing_time_ms": 0.0
        }
        
        total_time = 0.0
        for name, module in self.modules.items():
            module_stats = module.get_stats()
            stats["modules"][name] = module_stats
            
            stats["total_processed"] += module_stats.get("process_count", 0)
            stats["total_errors"] += module_stats.get("error_count", 0)
            total_time += module_stats.get("avg_time_ms", 0.0)
        
        if self.modules:
            stats["avg_processing_time_ms"] = total_time / len(self.modules)
        
        return stats
    
    def _publish_event(self, event_type: str, data: Dict[str, Any]):
        """发布事件"""
        event = {
            "type": event_type,
            "timestamp": datetime.now().isoformat(),
            "data": data
        }
        
        # 调用事件处理器
        for handler in self.event_handlers[event_type]:
            try:
                handler(event)
            except Exception as e:
                logger.error(f"事件处理器异常: {e}")


# ============================================================================
# 向后兼容引擎包装器
# ============================================================================

class BiologicalMemoryEngine:
    """生物学启发记忆引擎（主入口）"""
    
    def __init__(self, config: Dict[str, Any] = None):
        """初始化引擎"""
        default_config = {
            "system_name": "OpenClawBiologicalMemoryEngine",
            "version": "1.0.0",
            "max_concurrent_requests": 10,
            "enable_pipeline": True,
            "pipeline": [
                "sensory_registration",
                "working_memory", 
                "emotional_appraisal",
                "consolidation_pruning",
                "long_term_storage"
            ],
            "module_configs": {
                "sensory_registration": {"channels": ["text"]},
                "working_memory": {"capacity": 20},
                "emotional_appraisal": {},
                "consolidation_pruning": {},
                "long_term_storage": {"storage_path": "./memory_storage"},
                "recall_association": {}
            }
        }
        
        if config:
            default_config.update(config)
        
        self.config = default_config
        self.coordinator = CentralCoordinator(self.config)
        
        logger.info(f"生物学启发记忆引擎初始化完成 (v{self.config['version']})")
    
    def ingest(self, content: str, content_type: str = "text", source: str = "user") -> MemoryResult:
        """摄入记忆"""
        memory_item = MemoryItem(
            content=content,
            content_type=content_type,
            source=source
        )
        
        return self.coordinator.process_memory(memory_item)
    
    def retrieve(self, query: str, top_k: int = 10, mode: str = "hybrid") -> MemoryResult:
        """检索记忆"""
        memory_query = MemoryQuery(
            query_text=query,
            max_results=top_k,
            retrieval_mode=mode
        )
        
        return self.coordinator.retrieve_memory(memory_query)
    
    def get_stats(self) -> Dict[str, Any]:
        """获取引擎统计"""
        return self.coordinator.get_system_stats()
    
    def sleep_cycle(self) -> MemoryResult:
        """执行睡眠周期（巩固修剪）"""
        # 此功能需要与工作记忆模块交互
        # 这里实现一个简化版本
        
        logger.info("开始睡眠周期（记忆巩固）")
        
        # 获取工作记忆模块
        working_module = self.coordinator.modules.get("working_memory")
        if working_module and isinstance(working_module, WorkingMemoryAdapter):
            # 获取所有工作记忆
            working_memories = working_module.buffer
            
            if working_memories:
                logger.info(f"处理 {len(working_memories)} 条工作记忆")
                
                # 批量巩固
                consolidation_module = self.coordinator.modules.get("consolidation_pruning")
                if consolidation_module:
                    # 为每条工作记忆创建上下文
                    context = MemoryContext()
                    
                    for memory_item in working_memories:
                        # 更新访问计数
                        memory_item.increment_access()
                        
                        # 执行巩固
                        consolidation_module.process(memory_item, context)
                
                # 清空工作记忆（可选）
                # working_module.buffer = []
                
        return MemoryResult(
            success=True,
            message="睡眠周期完成"
        )


# ============================================================================
# 演示和测试
# ============================================================================

def demo():
    """演示引擎功能"""
    print("=" * 70)
    print("OpenClaw生物学启发记忆引擎演示")
    print("=" * 70)
    
    # 初始化引擎
    engine = BiologicalMemoryEngine({
        "module_configs": {
            "long_term_storage": {"storage_path": "./demo_storage"}
        }
    })
    
    print("1. 摄入记忆...")
    
    # 摄入几条示例记忆
    examples = [
        "今天学习了Python的记忆系统设计模式。",
        "情绪分析可以帮助记忆系统确定重要性。",
        "艾宾浩斯遗忘曲线描述了记忆随时间衰减的规律。",
        "工作记忆容量有限，大约只能保持4-7个项目。"
    ]
    
    for i, example in enumerate(examples):
        result = engine.ingest(example, source=f"demo_{i}")
        if result.success:
            memory_item = result.data
            print(f"   [OK] 记忆 {i+1}: {example[:40]}...")
            print(f"      状态: {memory_item.status.value}, 类型: {memory_item.memory_type.value}")
            print(f"      重要性: {memory_item.importance:.2f}, 强度: {memory_item.strength:.2f}")
        else:
            print(f"   [ERROR] 记忆 {i+1} 失败: {result.message}")
    
    print("\n2. 检索记忆...")
    
    # 检索测试
    queries = ["记忆系统", "工作记忆", "情绪"]
    
    for query in queries:
        result = engine.retrieve(query, top_k=2)
        if result.success and result.data:
            memories = result.data if isinstance(result.data, list) else [result.data]
            print(f"   [SEARCH] 查询: '{query}'")
            for j, memory in enumerate(memories[:2]):
                print(f"      结果 {j+1}: {memory.content[:60]}...")
                print(f"          相似度: {memory.importance:.2f}, 类型: {memory.memory_type.value}")
        else:
            print(f"   [ERROR] 查询 '{query}' 无结果: {result.message}")
    
    print("\n3. 系统统计...")
    stats = engine.get_stats()
    print(f"   总处理数: {stats.get('total_processed', 0)}")
    print(f"   模块统计:")
    for module, module_stats in stats.get("modules", {}).items():
        print(f"     {module}: {module_stats.get('process_count', 0)} 次处理")
    
    print("\n4. 睡眠周期（记忆巩固）...")
    sleep_result = engine.sleep_cycle()
    print(f"   {sleep_result.message}")
    
    print("\n" + "=" * 70)
    print("演示完成！")
    print("=" * 70)


if __name__ == "__main__":
    demo()