#!/usr/bin/env python3
"""
工作记忆与特征编码模块 (Working Memory & Encoding)
负责短期缓冲区管理、特征编码和记忆类型分类。
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
import heapq

# 尝试导入可选依赖
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
class EncodedMemory:
    """编码后的记忆数据结构"""
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
    
    # 元数据
    importance: float = 0.5
    source: str = ""
    tags: List[str] = field(default_factory=list)
    
    # 访问记录 (用于LRU)
    last_accessed: datetime = field(default_factory=datetime.now)
    access_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为可序列化的字典"""
        data = asdict(self)
        # 处理特殊类型
        data['timestamp'] = self.timestamp.isoformat()
        data['last_accessed'] = self.last_accessed.isoformat()
        data['embedding_vector'] = self.embedding_vector.tolist() if self.embedding_vector is not None else None
        data['chunk_type'] = self.chunk_type.value
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EncodedMemory':
        """从字典还原"""
        # 转换特殊字段
        data = data.copy()
        data['timestamp'] = datetime.fromisoformat(data['timestamp']) if isinstance(data['timestamp'], str) else data['timestamp']
        data['last_accessed'] = datetime.fromisoformat(data['last_accessed']) if isinstance(data['last_accessed'], str) else data['last_accessed']
        data['embedding_vector'] = np.array(data['embedding_vector']) if data['embedding_vector'] else None
        data['chunk_type'] = MemoryType(data['chunk_type']) if isinstance(data['chunk_type'], str) else data['chunk_type']
        return cls(**data)
    
    def update_access(self):
        """更新访问记录"""
        self.last_accessed = datetime.now()
        self.access_count += 1


class EmbeddingBackend:
    """嵌入向量生成器，支持多种后端和降级策略"""
    
    def __init__(self, preferred_backend: str = "ollama"):
        """
        初始化嵌入后端
        
        Args:
            preferred_backend: 优先使用的后端，可选值: "ollama", "sentence_transformers", "tfidf", "pseudo"
        """
        self.preferred_backend = preferred_backend
        self.available_backends = self._detect_available_backends()
        self.active_backend = None
        self.embedding_dim = 768
        self._init_backend()
        
    def _detect_available_backends(self) -> List[str]:
        """检测可用的后端"""
        backends = []
        
        if OLLAMA_AVAILABLE:
            backends.append("ollama")
        
        if SENTENCE_TRANSFORMERS_AVAILABLE:
            backends.append("sentence_transformers")
        
        if SKLEARN_AVAILABLE:
            backends.append("tfidf")
        
        backends.append("pseudo")  # 伪嵌入总是可用
        return backends
    
    def _init_backend(self):
        """初始化后端，按照偏好顺序选择"""
        backend_order = ["ollama", "sentence_transformers", "tfidf", "pseudo"]
        
        # 确保偏好后端在列表中
        if self.preferred_backend not in backends and backends:
            print(f"[WARN] 优先后端 {self.preferred_backend} 不可用，使用 {backends[0]}")
        
        return backends
    
    def _init_backend(self):
        """初始化激活的后端"""
        if not self.available_backends:
            print("[WARN] 无可用嵌入后端，使用伪嵌入")
            self.active_backend = "pseudo"
            return
        
        # 尝试使用优先后端，否则使用第一个可用的
        if self.preferred_backend in self.available_backends:
            self.active_backend = self.preferred_backend
        else:
            self.active_backend = self.available_backends[0]
        
        print(f"[INFO] 使用嵌入后端: {self.active_backend}")
        
        # 加载模型（如果需要）
        if self.active_backend == "sentence_transformers":
            try:
                self.model = SentenceTransformer('paraphrase-MiniLM-L6-v2')
                self.embedding_dim = self.model.get_sentence_embedding_dimension()
            except Exception as e:
                print(f"[ERROR] 初始化后端 {self.active_backend} 失败: {e}")
                self.active_backend = "pseudo"
    
    def embed(self, text: str, max_length: int = icrosft嵌入生成")
        
        # 初始化特定后端
        if self.active_backend == "sentence_transformers":
            try:
                # 使用轻量级模型
                self._st_model = SentenceTransformer('paraphrase-MiniLM-L6-v2')
                self.embedding_dim = self._st_model.get_sentence_embedding_dimension()
            except Exception as e:
                print(f"[ERROR] 初始化sentence_transformers失败: {e}")
                self.active_backend = "pseudo"
    
    def embed(self, text: str) -> np.ndarray:
        """
        生成文本的向量嵌入
        
        Args:
            text: 输入文本
            
        Returns:
            归一化的嵌入向量
        """
        if not text.strip():
            return np.zeros(self.embedding_dim)
        
        # 截断超长文本
        MAX_LENGTH = 8192
        if len(text) > MAX_LENGTH:
            text = text[:MAX_LENGTH]
            print(f"[WARN] 文本过长，截断至 {MAX_LENGTH} 字符")
        
        # 根据激活的后端选择嵌入方法
        if self.active_backend == "ollama":
            return self._embed_ollama(text)
        elif self.active_backend == "sentence_transformers":
            return self._embed_sentence_transformers(text)
        elif self.active_backend == "tfidf":
            return self._embed_tfidf(text)
        else:
            return self._embed_pseudo(text)
    
    def _embed_ollama(self, text: str) -> np.ndarray:
        """使用Ollama生成嵌入"""
        try:
            response = ollama.embeddings(
                model="nomic-embed-text",
                prompt=text
            )
            vec = np.array(response["embedding"])
            
            # 归一化
            norm = np.linalg.norm(vec)
            if norm > 0:
                vec = vec / norm
            
            return vec
        except Exception as e:
            print(f"[WARN] Ollama嵌入失败: {e}，降级到伪嵌入")
            return self._embed_pseudo(text)
    
    def _embed_sentence_transformers(self, text: str) -> np.ndarray:
        """使用sentence-transformers生成嵌入"""
        try:
            vec = self._st_model.encode(text)
            # 归一化
            norm = np.linalg.norm(vec)
            if norm > 0:
                vec = vec / norm
            return vec
        except Exception as e:
            print(f"[WARN] sentence-transformers嵌入失败: {e}，降级到伪嵌入")
            return self._pseudo_embedding(text)
    
    def _embed_sentence_transformers(self, text: str) -> np.ndarray:
        """使用sentence-transformers生成嵌入"""
        try:
            vec = self._st_model.encode(text)
            # 归一化
            norm = np.linalg.norm(vec)
            if norm > 0:
                vec = vec / norm
            return vec
        except Exception as e:
            print(f"[WARN] sentence-transformers嵌入失败: {e}，降级到伪嵌入")
            return self._pseudo_embedding(text)
    
    def _pseudo_embedding(self, text: str) -> np.ndarray:
        """生成伪嵌入向量（基于哈希的确定性随机向量）"""
        # 使用SHA256生成确定性种子
        h = hashlib.sha256(text.encode()).hexdigest()
        seed = int(h[:8], 16) % 10000
        np.random.seed(seed)
        
        # 生成随机向量
        vec = np.random.randn(self.embedding_dim)
        
        # 归一化
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        
        return vec
    
    def get_backend_info(self) -> Dict[str, Any]:
        """获取后端信息"""
        return {
            "active_backend": self.active_backend,
            "available_backends": self.available_backends,
            "embedding_dim": self.embedding_dim,
            "preferred_backend": self.preferred_backend
        }


class SemanticFeatureExtractor:
    """语义特征提取器"""
    
    def __init__(self, method: str = "tfidf", max_keywords: int = 10):
        """
        初始化特征提取器
        
        Args:
            method: 特征提取方法，可选 "tfidf" 或 "rule_based"
            max_keywords: 最大关键词数量
        """
        self.method = method
        self.max_keywords = max_keywords
        
        if method == "tfidf" and SKLEARN_AVAILABLE:
            self.vectorizer = TfidfVectorizer(
                max_features=1000,
                stop_words='english',
                ngram_range=(1, 2)
            )
            self._fitted = False
        else:
            print(f"[INFO] 使用基于规则的关键词提取")
    
    def extract(self, text: str, corpus: List[str] = None) -> List[Tuple[str[]]TEMS_NOT_FOUND")
    
    def extract_keywords(self, text: str, corpus: List[str] = None) -> List[Tuple[str, float]]:
        """
        提取文本关键词
        
        Args:
            text: 输入文本
            corpus: 可选的语料库（用于TF-IDF）
            
        Returns:
            关键词及其权重列表
        """
        if self.method == "tfidf" and SKLEARN_AVAILABLE and corpus:
            return self._extract_tfidf_keywords(text, corpus)
        else:
            return self._extract_rule_based_keywords(text)
    
    def _extract_tfidf_keywords(self, text: str, corpus: List[str]) -> List[Tuple[str, float]]:
        """使用TF-IDF提取关键词"""
        try:
            # 确保语料库包含当前文本
            all_texts = corpus + [text] if corpus else [text]
            
            if not self._fitted:
                tfidf_matrix = self.vectorizer.fit_transform(all_texts)
                self._fitted = True
            else:
                tfidf_matrix = self.vectorizer.transform(all_texts)
            
            # 获取特征名
            feature_names = self.vectorizer.get_feature_names_out()
            
            # 获取当前文本的TF-IDF向量
            if corpus:
                text_idx = len(corpus)
            else:
                text_idx = 0
            text_vector = tfidf_matrix[text_idx].toarray()[0]
            
            # 获取非零权重的特征
            nonzero_indices = text_vector.nonzero()[0]
            keywords_with_scores = [(feature_names[i], text_vector[i]) for i in nonzero_indices]
            
            # 关键词数排序
                tfidf_scores = tfidf_matrix[-1].toarray()[0]
                sorted_indices = np.argsort(tfidf_scores)[::-1]
                
                keywords = []
                for idx in sorted_indices[:self.max_keywords]:
                    if tfidf_scores[idx] > 0:
                        keywords.append((feature_names[idx], float(tfidf_scores[idx])))
                
                return keywords
            else:
                return []
                
        except Exception as e:
            print(f"[WARN] TF-IDF关键词提取失败: {e}")
            return self._extract_rule_based_keywords(text)
    
    def _extract_rule_based_keywords(self, text: str) -> List[Tuple[str, float]]:
        """基于规则提取关键词"""
        # 简单的关键词提取规则
        keywords = []
        
        # 提取名词短语（简单实现）
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
        word_freq = defaultdict(int)
        for word in words:
            if len(word) > 2 and word not in ['the', 'and', 'for', 'that', 'this', 'with', 'have', 'from']:
                word_freq[word] += 1
        
        # 按频率排序
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        
        for word, freq in sorted_words[:self.max_keywords]:
            # 简单权重计算
            weight = min(freq / 10, 1.0)
            keywords.append((word, weight))
        
        return keywords


class TypeClassifier:
    """记忆类型分类器"""
    
    def __init__(self):
        # 类型关键词映射
        self.type_keywords = {
            MemoryType.FACT: ["is", "was", "are", "were", "has", "have", "contain", "include", 
                            "number", "data", "statistic", "research", "study", "result"],
            MemoryType.DECISION: ["decide", "choose", "select", "option", "better", "best", 
                                "should", "will", "going to", "plan", "strategy", "goal"],
            MemoryType.OPINION: ["think", "believe", "feel", "opinion", "like", "dislike", 
                               "prefer", "awesome", "terrible", "good", "bad", "interesting"],
            MemoryType.INSTRUCTION: ["do", "run", "execute", "install", "configure", "set up",
                                   "command", "step", "first", "then", "next", "finally"],
            MemoryType.CODE: ["def ", "class ", "import ", "function", "variable", "loop",
                            "if ", "else", "for ", "while", "return", "python", "code"],
            MemoryType.EXPERIENCE: ["learned", "experienced", "tried", "worked", "built",
                                  "created", "solved", "fixed", "discovered", "found"],
            MemoryType.LOG: ["error", "warning", "info", "debug", "log", "failed", "success",
                           "started", "finished", "processed", "time", "date"]
        }
        
        # 类型权重
        self.type_weights = {
            MemoryType.FACT: 0.7,
            MemoryType.DECISION: 0.8,
            MemoryType.OPINION: 0.6,
            MemoryType.INSTRUCTION: 0.9,
            MemoryType.CODE: 0.95,
            MemoryType.EXPERIENCE: 0.75,
            MemoryType.LOG: 0.85
        }
    
    def classify(self, text: str, semantic_keywords: List[Tuple[str, float]] = None) -> Tuple[MemoryType, float]:
        """
        分类记忆类型
        
        Args:
            text: 输入文本
            semantic_keywords: 语义关键词列表（可选）
            
        Returns:
            (记忆类型, 置信度)
        """
        scores = defaultdict(float)
        text_lower = text.lower()
        
        # 基于关键词匹配
        for mem_type, keywords in self.type_keywords.items():
            for keyword in keywords:
                if keyword in text_lower:
                    scores[mem_type] += self.type_weights.get(mem_type, 0.5)
        
        # 基于语义关键词
        if semantic_keywords:
            for keyword, weight in semantic_keywords:
                keyword_lower = keyword.lower()
                for mem_type, type_keywords in self.type_keywords.items():
                    if any(kw in keyword_lower for kw in type_keywords):
                        scores[mem_type] += weight * 0.5
        
        # 基于文本模式
        if text_lower.startswith(("def ", "class ", "import ")):
            scores[MemoryType.CODE] += 2.0
        elif text_lower.startswith(("# ", "## ", "### ")):
            scores[MemoryType.FACT] += 0.5
        elif "error" in text_lower or "warning" in text_lower:
            scores[MemoryType.LOG] += 1.0
        elif any(word in text_lower for word in ["you should", "you must", "please do"]):
            scores[MemoryType.INSTRUCTION] += 1.5
        
        # 如果没有匹配，使用默认类型
        if not scores:
            return MemoryType.UNKNOWN, 0.3
        
        # 找到最高分
        best_type = max(scores.items(), key=lambda x: x[1])
        
        # 计算置信度（归一化到0-1）
        total_score = sum(scores.values())
        confidence = best_type[1] / total_score if total_score > 0 else 0.5
        
        return best_type[0], min(confidence, 1.0)


class WorkingMemory:
    """工作记忆管理器"""
    
    def __init__(self, capacity: int = 20, embedding_backend: str = "ollama"):
        """
        初始化工作记忆
        
        Args:
            capacity: 缓冲区容量
            embedding_backend: 嵌入后端偏好
        """
        self.capacity = capacity
        self.buffer = OrderedDict()  # id -> EncodedMemory
        self.embedding_engine = EmbeddingEngine(preferred_backend=embedding_backend)
        self.feature_extractor = SemanticFeatureExtractor(method="tfidf")
        self.type_classifier = TypeClassifier()
        
        # 统计信息
        self.stats = {
            "total_encoded": 0,
            "evicted": 0,
            "hits": 0,
            "misses": 0
        }
    
    def encode(self, content: str, importance: float = 0.5, source: str = "", 
               tags: List[str] = None) -> EncodedMemory:
        """
        编码新记忆并添加到缓冲区
        
        Args:
            content: 记忆内容
            importance: 重要性分数 (0-1)
            source: 来源
            tags: 标签列表
            
        Returns:
            编码后的记忆对象
        """
        # 生成唯一ID
        mem_id = self._generate_id(content)
        
        # 如果已存在，更新访问记录
        if mem_id in self.buffer:
            memory = self.buffer[mem_id]
            memory.last_accessed = datetime.now()
            memory.access_count += 1
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
        
        # 4. 创建编码记忆
        memory = EncodedMemory(
            id=mem_id,
            content=content,
            embedding_vector=embedding_vector,
            semantic_features=semantic_features,
            semantic_keywords=semantic_keywords,
            chunk_type=chunk_type,
            type_confidence=type_confidence,
            importance=importance,
            source=source,
            tags=tags or [],
            access_count=1
        )
        
        # 5. 添加到缓冲区（应用LRU策略）
        self._add_to_buffer(mem_id, memory)
        
        self.stats["total_encoded"] += 1
        return memory
    
    def _generate_id(self, content: str) -> str:
        """生成记忆ID"""
        # 使用内容和时间戳的哈希
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        unique_str = f"{content[:100]}_{timestamp}"
        return hashlib.md5(unique_str.encode()).hexdigest()[:12]
    
    def _add_to_buffer(self, mem_id: str, memory: EncodedMemory):
        """添加记忆到缓冲区，应用LRU策略"""
        # 如果缓冲区已满，淘汰最久未访问的
        if len(self.buffer) >= self.capacity:
            # LRU淘汰：移除第一个（最久未访问）
            lru_id = next(iter(self.buffer))
            del self.buffer[lru_id]
            self.stats["evicted"] += 1
            print(f"[LRU] 淘汰记忆: {lru_id}")
        
        # 添加到缓冲区（最近访问）
        self.buffer[mem_id] = memory
    
    def get(self, mem_id: str) -> Optional[EncodedMemory]:
        """获取记忆（更新访问记录）"""
        if mem_id in self.buffer:
            memory = self.buffer[mem_id]
            # 更新访问记录
            memory.last_accessed = datetime.now()
            memory.access_count += 1
            
            # 移动到最近位置（LRU）
            self.buffer.move_to_end(mem_id)
            
            self.stats["hits"] += 1
            return memory
        
        self.stats["misses"] += 1
        return None
    
    def query_similar(self, query_text: str, top_k: int = 5, 
                      min_similarity: float = 0.3) -> List[Tuple[EncodedMemory, float]]:
        """
        查询相似记忆
        
        Args:
            query_text: 查询文本
            top_k: 返回结果数量
            min_similarity: 最小相似度阈值
            
        Returns:
            (记忆, 相似度) 列表
        """
        if not self.buffer:
            return []
        
        # 生成查询向量
        query_vec = self.embedding_engine.embed(query_text)
        
        # 计算相似度
        results = []
        for memory in self.buffer.values():
            if memory.embedding_vector is None:
                continue
            
            # 余弦相似度
            similarity = np.dot(query_vec, memory.embedding_vector) / (
                np.linalg.norm(query_vec) * np.linalg.norm(memory.embedding_vector) + 1e-8
            )
            
            if similarity >= min_similarity:
                results.append((memory, similarity))
        
        # 按相似度排序
        results.sort(key=lambda x: x[1], reverse=True)
        
        return results[:top_k]
    
    def get_buffer_stats(self) -> Dict[str, Any]:
        """获取缓冲区统计信息"""
        type_distribution = defaultdict(int)
        total_importance = 0.0
        
        for memory in self.buffer.values():
            type_distribution[memory.chunk_type.value] += 1
            total_importance += memory.importance
        
        avg_importance = total_importance / len(self.buffer) if self.buffer else 0
        
        return {
            "buffer_size": len(self.buffer),
            "capacity": self.capacity,
            "type_distribution": dict(type_distribution),
            "average_importance": avg_importance,
            "total_encoded": self.stats["total_encoded"],
            "evicted": self.stats["evicted"],
            "hit_rate": self.stats["hits"] / (self.stats["hits"] + self.stats["misses"]) 
                if (self.stats["hits"] + self.stats["misses"]) > 0 else 0
        }
    
    def clear(self):
        """清空缓冲区"""
        self.buffer.clear()
        print("[INFO] 工作记忆缓冲区已清空")
    
    def save_buffer(self, filepath: str):
        """保存缓冲区到文件"""
        buffer_data = {
            "metadata": {
                "capacity": self.capacity,
                "saved_at": datetime.now().isoformat(),
                "stats": self.stats
            },
            "memories": [memory.to_dict() for memory in self.buffer.values()]
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(buffer_data, f, indent=2, ensure_ascii=False)
        
        print(f"[INFO] 工作记忆缓冲区已保存到 {filepath}")
    
    def load_buffer(self, filepath: str):
        """从文件加载缓冲区"""
        if not os.path.exists(filepath):
            print(f"[WARN] 文件不存在: {filepath}")
            return False
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                buffer_data = json.load(f)
            
            # 恢复统计信息
            self.stats.update(buffer_data.get("metadata", {}).get("stats", {}))
            
            # 恢复记忆
            self.buffer.clear()
            for mem_dict in buffer_data.get("memories", []):
                memory = EncodedMemory.from_dict(mem_dict)
                self.buffer[memory.id] = memory
            
            print(f"[INFO] 从 {filepath} 加载了 {len(self.buffer)} 条记忆")
            return True
        
        except Exception as e:
            print(f"[ERROR] 加载缓冲区失败: {e}")
            return False


class EmbeddingEngine:
    """统一的嵌入引擎（包装之前的EmbeddingEngine功能）"""
    
    def __init__(self, preferred_backend: str = "ollama"):
        self.backend = EmbeddingBackend(preferred_backend=preferred_backend)
    
    def embed(self, text: str) -> np.ndarray:
        return self.backend.embed(text)
    
    def get_backend_info(self) -> Dict[str, Any]:
        return self.backend.get_backend_info()


# 为了保持向后兼容性，保留旧的类名
EmbeddingBackend = EmbeddingEngine


def test_working_memory():
    """测试工作记忆功能"""
    print("=" * 70)
    print("工作记忆模块测试")
    print("=" * 70)
    
    # 1. 初始化工作记忆
    print("\n1. 初始化工作记忆 (容量=5)")
    wm = WorkingMemory(capacity=5)
    
    # 2. 编码测试记忆
    print("\n2. 编码测试记忆")
    test_memories = [
        ("量子计算使用量子比特而不是经典比特进行信息处理。", 0.9, "fact"),
        ("我决定学习Qiskit，因为它有很好的文档和社区支持。", 0.8, "decision"),
        ("我认为Python是量子编程的最佳语言之一。", 0.6, "opinion"),
        ("首先安装qiskit：pip install qiskit，然后导入库。", 0.95, "instruction"),
        ("今天编写了一个量子随机数生成器，运行成功。", 0.7, "experience"),
        ("错误：模块'qiskit'未找到，请确保已安装。", 0.5, "log"),
        ("def quantum_circuit(): qc = QuantumCircuit(2)", 0.9, "code"),
        ("量子纠缠是量子力学中的重要现象。", 0.85, "fact"),
        ("我计划下周完成量子算法实验报告。", 0.75, "decision"),
        ("Linux比Windows更适合开发环境。", 0.4, "opinion"),
    ]
    
    for i, (content, importance, expected_type) in enumerate(test_memories):
        print(f"\n  记忆 {i+1}: {content[:50]}...")
        memory = wm.encode(content, importance=importance, source="test")
        print(f"    类型: {memory.chunk_type.value} (置信度: {memory.type_confidence:.2f})")
        print(f"    关键词: {', '.join(memory.semantic_features[:3])}")
        print(f"    向量维度: {len(memory.embedding_vector) if memory.embedding_vector is not None else 0}")
    
    # 3. 测试缓冲区状态
    print("\n3. 缓冲区状态")
    stats = wm.get_buffer_stats()
    print(f"   缓冲区大小: {stats['buffer_size']}/{stats['capacity']}")
    print(f"   类型分布: {stats['type_distribution']}")
    print(f"   平均重要性: {stats['average_importance']:.2f}")
    print(f"   命中率: {stats['hit_rate']:.2f}")
    
    # 4. 测试相似性查询
    print("\n4. 相似性查询测试")
    queries = ["量子计算", "编程错误", "安装步骤"]
    
    for query in queries:
        print(f"\n  查询: '{query}'")
        results = wm.query_similar(query, top_k=2)
        for mem, sim in results:
            print(f"    - 相似度 {sim:.3f}: {mem.content[:60]}... [{mem.chunk_type.value}]")
    
    # 5. 测试LRU淘汰
    print("\n5. 测试LRU淘汰")
    print("   添加第6条记忆（应触发淘汰）...")
    extra_memory = wm.encode("这是额外的测试记忆，用于触发LRU淘汰。", importance=0.5)
    print(f"   当前缓冲区大小: {len(wm.buffer)}/5")
    
    # 6. 测试保存/加载
    print("\n6. 测试保存和加载")
    test_file = "test_working_memory.json"
    wm.save_buffer(test_file)
    
    # 创建新的工作记忆并加载
    wm2 = WorkingMemory(capacity=5)
    wm2.load_buffer(test_file)
    print(f"   加载后缓冲区大小: {len(wm2.buffer)}")
    
    # 清理测试文件
    if os.path.exists(test_file):
        os.remove(test_file)
    
    print("\n" + "=" * 70)
    print("测试完成!")
    print("=" * 70)


if __name__ == "__main__":
    test_working_memory()