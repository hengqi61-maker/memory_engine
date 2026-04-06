#!/usr/bin/env python3
"""
长期存储与持久化 (Long-term Storage) 模块
为 OpenClaw 记忆引擎提供可靠的双重存储系统

设计原则：
1. 双重存储：JSON存储完整记忆对象 + 向量索引快速检索
2. 原子操作：保存时先写临时文件再替换，保证数据完整性
3. 版本管理：存储格式版本号，支持向后兼容
4. 归档机制：修剪的记忆安全归档，而非删除
5. 元数据索引：类型、情绪标签、关键词等二级索引

与现有代码关系：
- 复用 `openclaw_memory_engine_fixed.py` 中的 EnhancedStorageLayer 和 ArchivedMemoryManager
- 保持与原代码的兼容性，可平滑迁移
"""

import os
import json
import shutil
import hashlib
import tempfile
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Union
import numpy as np

# 尝试导入 Faiss，如果不可用则使用替代方案
try:
    import faiss
    FAISS_AVAILABLE = True
    print("[INFO] Faiss 向量数据库可用")
except ImportError:
    FAISS_AVAILABLE = False
    print("[WARN] Faiss 不可用，将使用 numpy 内存索引作为备用方案")

# ==================== StoreSchema 设计 ====================
"""
JSON 存储的完整字段定义

存储文件格式：
{
    "version": "1.0.0",           # 存储格式版本号
    "created_at": "2026-03-28T10:00:00",  # 创建时间
    "updated_at": "2026-03-28T10:30:00",  # 最后更新时间
    "config": {                   # 存储配置
        "embedding_dim": 768,      # 向量维度
        "archive_enabled": true,   # 是否启用归档
        "archive_dir": "./archived",  # 归档目录
        "compression": false       # 是否启用压缩
    },
    "metadata": {                 # 元数据索引
        "memory_count": 100,
        "type_distribution": {"knowledge": 50, "task": 30, "code": 20},
        "emotion_tags": [...],
        "keywords": [...]
    },
    "memories": [                 # 记忆对象数组
        {
            "storage_id": "mem_20260328_001",  # 唯一存储ID
            "archived_path": null,             # 归档路径（如果已归档）
            "vector_index": 0,                  # 在向量索引中的位置
            "memory_obj": {                     # 原始记忆对象（ConsolidatedMemory）
                "id": "20260328_001",          # 原始ID
                "fact": "关于量子计算的基础概念",
                "content": "完整的记忆内容...",
                "vec": [0.1, 0.2, ...],        # 768维向量
                "importance": 0.8,
                "type": "knowledge",
                "timestamp": "2026-03-28T10:00:00",
                "confidence": 0.9,
                "source_count": 1,
                "metadata": {                  # 扩展元数据
                    "emotion": "neutral",
                    "keywords": ["量子", "计算"],
                    "entities": [],
                    "language": "zh"
                }
            },
            "created_at": "2026-03-28T10:00:00",
            "updated_at": "2026-03-28T10:00:00",
            "access_count": 5,                 # 访问次数
            "last_accessed": "2026-03-28T10:25:00"
        }
    ],
    "indices": {                 # 索引信息
        "vector_index": {        # 向量索引状态
            "type": "faiss" or "numpy",
            "dimension": 768,
            "size": 100,
            "file": "vectors.faiss"  # 向量索引文件路径
        },
        "metadata_indices": {    # 元数据索引
            "by_type": {"knowledge": [0, 1, 2], "task": [3, 4]},
            "by_date": {"2026-03-28": [0, 1, 2, 3]},
            "by_emotion": {},
            "by_keyword": {}
        }
    }
}
"""

class StoreSchema:
    """存储模式定义和验证"""
    
    CURRENT_VERSION = "1.0.0"
    
    @staticmethod
    def create_empty_store(embedding_dim=768, archive_dir="./archived"):
        """创建空的存储结构"""
        return {
            "version": StoreSchema.CURRENT_VERSION,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "config": {
                "embedding_dim": embedding_dim,
                "archive_enabled": True,
                "archive_dir": archive_dir,
                "compression": False,
                "vector_index_type": "faiss" if FAISS_AVAILABLE else "numpy"
            },
            "metadata": {
                "memory_count": 0,
                "type_distribution": {},
                "emotion_tags": [],
                "keywords": [],
                "date_range": {"start": None, "end": None}
            },
            "memories": [],
            "indices": {
                "vector_index": {
                    "type": "faiss" if FAISS_AVAILABLE else "numpy",
                    "dimension": embedding_dim,
                    "size": 0,
                    "file": "vectors.faiss"
                },
                "metadata_indices": {
                    "by_type": {},
                    "by_date": {},
                    "by_emotion": {},
                    "by_keyword": {},
                    "by_importance": {}
                }
            }
        }
    
    @staticmethod
    def validate_store(store_data: Dict) -> Tuple[bool, str]:
        """验证存储数据的结构"""
        required_top = ["version", "created_at", "config", "metadata", "memories", "indices"]
        for field in required_top:
            if field not in store_data:
                return False, f"缺少顶级字段: {field}"
        
        # 检查配置
        config = store_data["config"]
        required_config = ["embedding_dim", "archive_enabled"]
        for field in required_config:
            if field not in config:
                return False, f"配置缺少字段: {field}"
        
        # 检查记忆列表格式
        for i, mem in enumerate(store_data["memories"]):
            required_mem = ["storage_id", "memory_obj", "created_at"]
            for field in required_mem:
                if field not in mem:
                    return False, f"记忆 {i} 缺少字段: {field}"
            
            # 检查 memory_obj
            mem_obj = mem["memory_obj"]
            required_obj = ["id", "content", "vec", "timestamp"]
            for field in required_obj:
                if field not in mem_obj:
                    return False, f"记忆 {i} 的 memory_obj 缺少字段: {field}"
        
        return True, "验证通过"


# ==================== 向量索引方案 ====================
"""
如何组织768维向量并支持高效检索

方案选择：
1. 主选：Faiss (Facebook AI Similarity Search)
   - 支持高维向量快速相似度搜索
   - 支持多种索引类型（Flat, IVF, HNSW）
   - 支持GPU加速
   - 支持增量索引

2. 备选：Numpy 内存索引
   - 简单实现，无需外部依赖
   - 适用于小规模数据
   - 支持余弦相似度和欧氏距离

设计要点：
1. 索引与数据分离：向量索引文件单独存储，JSON存储引用索引位置
2. 增量更新：支持添加、删除向量
3. 持久化：索引定期保存到磁盘
4. 恢复机制：索引损坏时从JSON数据重建
"""

class VectorIndexManager:
    """向量索引管理器"""
    
    def __init__(self, dimension=768, index_type="faiss", storage_dir="./storage"):
        """
        初始化向量索引管理器
        
        Args:
            dimension: 向量维度
            index_type: 索引类型 ("faiss" 或 "numpy")
            storage_dir: 存储目录
        """
        self.dimension = dimension
        self.index_type = index_type if FAISS_AVAILABLE else "numpy"
        self.storage_dir = storage_dir
        os.makedirs(storage_dir, exist_ok=True)
        
        self.index = None
        self.vectors = []  # 用于numpy模式的向量列表
        self.id_to_index = {}  # storage_id 到索引位置的映射
        self.index_to_id = {}  # 索引位置到storage_id的映射
        
        self.index_file = os.path.join(storage_dir, "vectors.faiss")
        
        # 初始化索引
        self._init_index()
    
    def _init_index(self):
        """初始化索引"""
        if self.index_type == "faiss" and FAISS_AVAILABLE:
            # 使用Faiss的Flat索引（L2距离）
            self.index = faiss.IndexFlatL2(self.dimension)
            print(f"[向量] 已初始化 Faiss FlatL2 索引，维度: {self.dimension}")
        else:
            # 使用numpy内存索引
            self.index = "numpy"
            self.vectors = []
            print(f"[向量] 已初始化 Numpy 内存索引，维度: {self.dimension}")
    
    def add_vector(self, vector: np.ndarray, storage_id: str) -> int:
        """
        添加向量到索引
        
        Args:
            vector: 768维向量
            storage_id: 对应的记忆ID
        
        Returns:
            向量在索引中的位置
        """
        if len(vector) != self.dimension:
            raise ValueError(f"向量维度应为 {self.dimension}，实际为 {len(vector)}")
        
        vector = vector.astype(np.float32).reshape(1, -1)
        
        if self.index_type == "faiss" and FAISS_AVAILABLE:
            position = self.index.ntotal
            self.index.add(vector)
        else:
            position = len(self.vectors)
            self.vectors.append(vector.flatten())
        
        # 更新映射
        self.id_to_index[storage_id] = position
        self.index_to_id[position] = storage_id
        
        return position
    
    def remove_vector(self, storage_id: str) -> bool:
        """
        从索引中移除向量（标记为删除）
        注意：Faiss不支持直接删除，我们通过映射表标记
        
        Args:
            storage_id: 要移除的记忆ID
        
        Returns:
            是否成功标记
        """
        if storage_id not in self.id_to_index:
            return False
        
        position = self.id_to_index[storage_id]
        
        # 在Faiss中，我们无法真正删除，但可以标记
        # 在实际检索时跳过标记的向量
        if hasattr(self, 'deleted_positions'):
            self.deleted_positions.add(position)
        else:
            self.deleted_positions = {position}
        
        # 更新映射
        del self.id_to_index[storage_id]
        if position in self.index_to_id:
            del self.index_to_id[position]
        
        return True
    
    def search_similar(self, query_vector: np.ndarray, top_k: int = 5) -> List[Tuple[str, float]]:
        """
        搜索相似向量
        
        Args:
            query_vector: 查询向量
            top_k: 返回最相似的k个结果
        
        Returns:
            [(storage_id, similarity_score), ...]
        """
        query_vector = query_vector.astype(np.float32).reshape(1, -1)
        
        if self.index_type == "faiss" and FAISS_AVAILABLE:
            if self.index.ntotal == 0:
                return []
            
            # 搜索
            distances, indices = self.index.search(query_vector, min(top_k * 2, self.index.ntotal))
            
            # 转换为相似度分数（1/(1+distance)）
            results = []
            for i, (dist, idx) in enumerate(zip(distances[0], indices[0])):
                if idx == -1 or (hasattr(self, 'deleted_positions') and idx in self.deleted_positions):
                    continue
                
                storage_id = self.index_to_id.get(idx)
                if storage_id:
                    similarity = 1.0 / (1.0 + dist)  # 距离转相似度
                    results.append((storage_id, similarity))
                
                if len(results) >= top_k:
                    break
            
            return results
        
        else:
            # Numpy模式
            if not self.vectors:
                return []
            
            vectors_np = np.array(self.vectors, dtype=np.float32)
            
            # 计算余弦相似度
            query_norm = np.linalg.norm(query_vector)
            if query_norm == 0:
                return []
            
            norms = np.linalg.norm(vectors_np, axis=1)
            valid_mask = norms > 0
            
            if not np.any(valid_mask):
                return []
            
            # 计算相似度
            similarities = np.zeros(len(self.vectors))
            similarities[valid_mask] = np.dot(vectors_np[valid_mask], query_vector.T).flatten() / (norms[valid_mask] * query_norm)
            
            # 获取top_k
            top_indices = np.argsort(similarities)[::-1][:top_k]
            
            results = []
            for idx in top_indices:
                if hasattr(self, 'deleted_positions') and idx in self.deleted_positions:
                    continue
                
                # 找到对应的storage_id
                storage_id = None
                for sid, pos in self.id_to_index.items():
                    if pos == idx:
                        storage_id = sid
                        break
                
                if storage_id:
                    results.append((storage_id, float(similarities[idx])))
            
            return results
    
    def save_index(self):
        """保存索引到文件"""
        if self.index_type == "faiss" and FAISS_AVAILABLE:
            faiss.write_index(self.index, self.index_file)
            print(f"[向量] Faiss索引已保存: {self.index_file}")
        
        # 保存映射表
        mapping_file = os.path.join(self.storage_dir, "vector_mapping.json")
        mapping_data = {
            "id_to_index": self.id_to_index,
            "index_to_id": self.index_to_id,
            "deleted_positions": list(getattr(self, 'deleted_positions', [])),
            "dimension": self.dimension,
            "index_type": self.index_type,
            "saved_at": datetime.now().isoformat()
        }
        
        with open(mapping_file, "w", encoding="utf-8") as f:
            json.dump(mapping_data, f, indent=2, ensure_ascii=False)
        
        print(f"[向量] 向量映射已保存: {mapping_file}")
    
    def load_index(self):
        """从文件加载索引"""
        mapping_file = os.path.join(self.storage_dir, "vector_mapping.json")
        
        if not os.path.exists(mapping_file):
            print("[向量] 没有找到索引映射文件，重新初始化索引")
            return False
        
        try:
            with open(mapping_file, "r", encoding="utf-8") as f:
                mapping_data = json.load(f)
            
            self.id_to_index = {str(k): v for k, v in mapping_data.get("id_to_index", {}).items()}
            self.index_to_id = {int(k): str(v) for k, v in mapping_data.get("index_to_id", {}).items()}
            self.deleted_positions = set(mapping_data.get("deleted_positions", []))
            
            # 加载Faiss索引
            if self.index_type == "faiss" and FAISS_AVAILABLE and os.path.exists(self.index_file):
                self.index = faiss.read_index(self.index_file)
                print(f"[向量] Faiss索引已加载: {self.index_file}")
            
            print(f"[向量] 索引映射已加载，包含 {len(self.id_to_index)} 个向量")
            return True
            
        except Exception as e:
            print(f"[WARN] 加载索引失败: {e}")
            self._init_index()
            return False


# ==================== 归档目录结构 ====================
"""
如何组织归档文件（按日期/重要性/主题）

归档目录结构：

archived/
├── 2026/                          # 按年份
│   ├── 03/                       # 按月份
│   │   ├── 28/                   # 按日期
│   │   │   ├── normal_pruning/   # 按修剪原因
│   │   │   │   ├── pruned_2026-03-28_10-30_normal_pruning.json
│   │   │   │   ├── pruned_2026-03-28_10-30_normal_pruning.md
│   │   │   │   └── prune_log_2026-03-28_10-30.txt
│   │   │   └── low_confidence/
│   │   │       └── ...
│   │   └── 29/
│   │       └── ...
│   └── 04/
│       └── ...
├── by_importance/                 # 按重要性归档
│   ├── high/                     # 重要性 > 0.8
│   ├── medium/                   # 0.5 <= 重要性 <= 0.8
│   └── low/                      # 重要性 < 0.5
├── by_type/                      # 按类型归档
│   ├── knowledge/
│   ├── task/
│   ├── code/
│   └── log/
└── by_theme/                     # 按主题归档（自动聚类）
    ├── quantum_computing/
    ├── python_programming/
    └── ...

设计原则：
1. 多维度组织：支持按日期、重要性、类型、主题等多维归档
2. 自动化归档：修剪时自动分类归档
3. 索引文件：每个归档目录包含索引文件，便于快速检索
4. 软链接：原始文件保存在日期目录，其他目录使用软链接或引用
"""

class ArchiveDirectoryManager:
    """归档目录管理器"""
    
    def __init__(self, base_archive_dir="./archived"):
        """
        初始化归档目录管理器
        
        Args:
            base_archive_dir: 归档基础目录
        """
        self.base_dir = base_archive_dir
        os.makedirs(base_archive_dir, exist_ok=True)
        
        # 创建标准子目录结构
        self._init_directory_structure()
    
    def _init_directory_structure(self):
        """初始化目录结构"""
        # 按日期
        self.date_dir = os.path.join(self.base_dir, "by_date")
        
        # 按重要性
        self.importance_dir = os.path.join(self.base_dir, "by_importance")
        for level in ["high", "medium", "low"]:
            os.makedirs(os.path.join(self.importance_dir, level), exist_ok=True)
        
        # 按类型
        self.type_dir = os.path.join(self.base_dir, "by_type")
        for mem_type in ["knowledge", "task", "code", "log", "emotion"]:
            os.makedirs(os.path.join(self.type_dir, mem_type), exist_ok=True)
        
        # 按主题（动态创建）
        self.theme_dir = os.path.join(self.base_dir, "by_theme")
        os.makedirs(self.theme_dir, exist_ok=True)
        
        print(f"[归档] 归档目录结构已初始化: {self.base_dir}")
    
    def _categorize_memory(self, memory_obj: Dict) -> Dict[str, List[str]]:
        """
        对记忆进行分类
        
        Returns:
            分类结果字典，键为分类维度，值为类别列表
        """
        categories = {
            "by_date": [],
            "by_importance": [],
            "by_type": [],
            "by_theme": []
        }
        
        # 按日期分类
        timestamp = memory_obj.get("timestamp")
        if timestamp:
            try:
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                date_str = dt.strftime("%Y-%m-%d")
                categories["by_date"].append(date_str)
            except:
                pass
        
        # 按重要性分类
        importance = memory_obj.get("importance", 0.5)
        if importance >= 0.8:
            categories["by_importance"].append("high")
        elif importance >= 0.5:
            categories["by_importance"].append("medium")
        else:
            categories["by_importance"].append("low")
        
        # 按类型分类
        mem_type = memory_obj.get("type", "log")
        categories["by_type"].append(mem_type)
        
        # 按主题分类（简单基于关键词）
        content = memory_obj.get("content", "")[:100].lower()
        themes = []
        theme_keywords = {
            "quantum": ["量子", "qiskit", "qubit", "quantum"],
            "programming": ["python", "代码", "程序", "编程"],
            "academic": ["学习", "研究", "论文", "学术"],
            "personal": ["简历", "工作", "任务", "项目"]
        }
        
        for theme, keywords in theme_keywords.items():
            if any(keyword in content for keyword in keywords):
                themes.append(theme)
        
        if not themes:
            themes.append("general")
        
        categories["by_theme"].extend(themes)
        
        return categories
    
    def create_archive_path(self, memory_obj: Dict, reason: str = "normal_pruning") -> str:
        """
        根据记忆属性和修剪原因创建归档路径
        
        Args:
            memory_obj: 记忆对象
            reason: 修剪原因
        
        Returns:
            归档文件路径
        """
        # 使用时间戳作为基础
        timestamp = datetime.now()
        date_path = timestamp.strftime("%Y/%m/%d")
        
        # 创建日期目录
        target_dir = os.path.join(self.date_dir, date_path, reason)
        os.makedirs(target_dir, exist_ok=True)
        
        # 生成文件名
        filename = f"pruned_{timestamp.strftime('%Y-%m-%d_%H-%M')}_{reason}.json"
        
        return os.path.join(target_dir, filename)
    
    def create_symlinks(self, source_path: str, memory_obj: Dict):
        """
        为归档文件创建符号链接到其他分类目录
        
        Args:
            source_path: 原始归档文件路径
            memory_obj: 记忆对象
        """
        if not os.path.exists(source_path):
            return
        
        categories = self._categorize_memory(memory_obj)
        
        # 为每个分类创建链接
        base_name = os.path.basename(source_path)
        
        for importance_level in categories.get("by_importance", []):
            link_dir = os.path.join(self.importance_dir, importance_level)
            link_path = os.path.join(link_dir, base_name)
            self._create_symlink(source_path, link_path)
        
        for mem_type in categories.get("by_type", []):
            link_dir = os.path.join(self.type_dir, mem_type)
            link_path = os.path.join(link_dir, base_name)
            self._create_symlink(source_path, link_path)
        
        for theme in categories.get("by_theme", []):
            link_dir = os.path.join(self.theme_dir, theme)
            link_path = os.path.join(link_dir, base_name)
            self._create_symlink(source_path, link_path)
    
    def _create_symlink(self, source: str, link_path: str):
        """创建符号链接（Windows使用复制）"""
        try:
            # 在Windows上，使用相对路径或复制文件
            if os.name == 'nt':
                # Windows不支持跨盘符的符号链接，使用复制
                if not os.path.exists(link_path):
                    shutil.copy2(source, link_path)
            else:
                # Unix系统使用符号链接
                if os.path.exists(link_path):
                    os.remove(link_path)
                rel_source = os.path.relpath(source, os.path.dirname(link_path))
                os.symlink(rel_source, link_path)
        except Exception as e:
            print(f"[WARN] 创建链接失败 {link_path}: {e}")

    def update_archive_index(self):
        """更新归档索引文件"""
        index_file = os.path.join(self.base_dir, "archive_index.json")
        
        index_data = {
            "last_updated": datetime.now().isoformat(),
            "total_archives": 0,
            "by_date": {},
            "by_importance": {},
            "by_type": {},
            "by_theme": {}
        }
        
        # 统计各目录文件数量
        for root, dirs, files in os.walk(self.base_dir):
            # 跳过索引文件本身
            if "archive_index.json" in files:
                continue
            
            # 统计JSON文件
            json_files = [f for f in files if f.endswith('.json')]
            if json_files:
                rel_path = os.path.relpath(root, self.base_dir)
                index_data["total_archives"] += len(json_files)
                
                # 根据路径分类统计
                if rel_path.startswith("by_date"):
                    index_data["by_date"][rel_path] = len(json_files)
                elif rel_path.startswith("by_importance"):
                    index_data["by_importance"][rel_path] = len(json_files)
                elif rel_path.startswith("by_type"):
                    index_data["by_type"][rel_path] = len(json_files)
                elif rel_path.startswith("by_theme"):
                    index_data["by_theme"][rel_path] = len(json_files)
        
        # 保存索引
        with open(index_file, "w", encoding="utf-8") as f:
            json.dump(index_data, f, indent=2, ensure_ascii=False)
        
        print(f"[归档] 归档索引已更新，总计 {index_data['total_archives']} 个归档文件")
        return index_data


# ==================== LongTermStorage 类 ====================
class LongTermStorage:
    """
    长期存储系统主类
    
    功能：
    1. store(): 存储记忆，包括JSON和向量索引
    2. load(): 加载记忆
    3. archive(): 归档记忆
    4. retrieve(): 检索记忆
    5. load_by_time_range(): 时间范围查询
    """
    
    def __init__(self, 
                 storage_dir="./long_term_storage",
                 embedding_dim=768,
                 enable_archive=True):
        """
        初始化长期存储系统
        
        Args:
            storage_dir: 存储目录路径
            embedding_dim: 向量维度
            enable_archive: 是否启用归档
        """
        self.storage_dir = os.path.abspath(storage_dir)
        os.makedirs(self.storage_dir, exist_ok=True)
        
        self.embedding_dim = embedding_dim
        self.enable_archive = enable_archive
        
        # 存储文件路径
        self.json_store_path = os.path.join(self.storage_dir, "memory_store.json")
        self.backup_path = os.path.join(self.storage_dir, "memory_store.json.bak")
        
        # 归档目录
        archive_dir = os.path.join(self.storage_dir, "archived")
        self.archive_manager = ArchiveDirectoryManager(archive_dir) if enable_archive else None
        
        # 向量索引管理器
        self.vector_manager = VectorIndexManager(
            dimension=embedding_dim,
            index_type="faiss" if FAISS_AVAILABLE else "numpy",
            storage_dir=os.path.join(self.storage_dir, "vectors")
        )
        
        # 存储数据缓存
        self.store_data = None
        
        # 初始化或加载存储
        self._init_or_load_store()
        
        print(f"[存储] 长期存储系统已初始化，目录: {self.storage_dir}")
        print(f"      - 向量索引: {self.vector_manager.index_type}")
        print(f"      - 归档功能: {'启用' if enable_archive else '禁用'}")
    
    def _init_or_load_store(self):
        """初始化或加载存储数据"""
        if os.path.exists(self.json_store_path):
            try:
                with open(self.json_store_path, "r", encoding="utf-8") as f:
                    self.store_data = json.load(f)
                
                # 验证版本兼容性
                version = self.store_data.get("version", "0.0.0")
                if version != StoreSchema.CURRENT_VERSION:
                    print(f"[WARN] 存储版本不匹配: {version} -> {StoreSchema.CURRENT_VERSION}")
                    self._migrate_store(version)
                
                print(f"[存储] 已加载存储文件，包含 {len(self.store_data['memories'])} 条记忆")
                
                # 加载向量索引
                self.vector_manager.load_index()
                
            except Exception as e:
                print(f"[ERROR] 加载存储失败: {e}")
                print("[存储] 创建新的存储文件")
                self.store_data = StoreSchema.create_empty_store(self.embedding_dim)
        else:
            self.store_data = StoreSchema.create_empty_store(self.embedding_dim)
            print("[存储] 创建新的存储文件")
    
    def _migrate_store(self, old_version: str):
        """迁移存储数据到新版本"""
        print(f"[迁移] 从版本 {old_version} 迁移到 {StoreSchema.CURRENT_VERSION}")
        
        # 这里可以实现版本迁移逻辑
        # 目前只是简单更新版本号
        self.store_data["version"] = StoreSchema.CURRENT_VERSION
        self.store_data["updated_at"] = datetime.now().isoformat()
        
        # 添加缺失的字段
        if "metadata" not in self.store_data:
            self.store_data["metadata"] = {
                "memory_count": len(self.store_data.get("memories", [])),
                "type_distribution": {},
                "emotion_tags": [],
                "keywords": []
            }
        
        # 更新元数据
        self._update_metadata()
    
    def _update_metadata(self):
        """更新存储的元数据"""
        memories = self.store_data["memories"]
        
        # 统计类型分布
        type_dist = {}
        emotion_tags = set()
        keywords = set()
        
        for mem in memories:
            mem_obj = mem.get("memory_obj", {})
            
            # 类型统计
            mem_type = mem_obj.get("type", "unknown")
            type_dist[mem_type] = type_dist.get(mem_type, 0) + 1
            
            # 情绪标签
            metadata = mem_obj.get("metadata", {})
            if "emotion" in metadata:
                emotion_tags.add(metadata["emotion"])
            
            # 关键词
            if "keywords" in metadata:
                keywords.update(metadata["keywords"])
        
        # 更新存储数据
        self.store_data["metadata"]["memory_count"] = len(memories)
        self.store_data["metadata"]["type_distribution"] = type_dist
        self.store_data["metadata"]["emotion_tags"] = list(emotion_tags)
        self.store_data["metadata"]["keywords"] = list(keywords)
        
        # 更新时间范围
        if memories:
            timestamps = []
            for mem in memories:
                mem_obj = mem.get("memory_obj", {})
                timestamp = mem_obj.get("timestamp")
                if timestamp:
                    try:
                        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                        timestamps.append(dt)
                    except:
                        pass
            
            if timestamps:
                min_date = min(timestamps).strftime("%Y-%m-%d")
                max_date = max(timestamps).strftime("%Y-%m-%d")
                self.store_data["metadata"]["date_range"] = {"start": min_date, "end": max_date}
    
    def _update_indices(self):
        """更新索引信息"""
        memories = self.store_data["memories"]
        
        # 元数据索引
        indices = self.store_data.setdefault("indices", {})
        meta_indices = indices.setdefault("metadata_indices", {})
        
        # 按类型索引
        by_type = {}
        by_date = {}
        by_importance = {"high": [], "medium": [], "low": []}
        
        for idx, mem in enumerate(memories):
            mem_obj = mem.get("memory_obj", {})
            
            # 按类型索引
            mem_type = mem_obj.get("type", "unknown")
            by_type.setdefault(mem_type, []).append(idx)
            
            # 按日期索引
            timestamp = mem_obj.get("timestamp")
            if timestamp:
                try:
                    dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    date_str = dt.strftime("%Y-%m-%d")
                    by_date.setdefault(date_str, []).append(idx)
                except:
                    pass
            
            # 按重要性索引
            importance = mem_obj.get("importance", 0.5)
            if importance >= 0.8:
                by_importance["high"].append(idx)
            elif importance >= 0.5:
                by_importance["medium"].append(idx)
            else:
                by_importance["low"].append(idx)
        
        meta_indices["by_type"] = by_type
        meta_indices["by_date"] = by_date
        meta_indices["by_importance"] = by_importance
        
        # 向量索引信息
        indices["vector_index"] = {
            "type": self.vector_manager.index_type,
            "dimension": self.vector_manager.dimension,
            "size": len(memories),
            "file": "vectors.faiss" if self.vector_manager.index_type == "faiss" else "numpy_memory"
        }
    
    def store(self, memory_obj: Dict) -> str:
        """
        存储记忆
        
        Args:
            memory_obj: ConsolidatedMemory对象，包含以下字段：
                - id: 原始ID
                - fact/content: 记忆内容
                - vec: 768维向量
                - importance: 重要性
                - type: 类型
                - timestamp: 时间戳
                - confidence: 置信度
                - metadata: 扩展元数据
        
        Returns:
            storage_id: 存储ID
        """
        # 生成存储ID
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        storage_id = f"mem_{timestamp}_{hashlib.md5(str(memory_obj['id']).encode()).hexdigest()[:8]}"
        
        # 添加到向量索引
        vector = np.array(memory_obj.get("vec", []), dtype=np.float32)
        if len(vector) != self.embedding_dim:
            print(f"[WARN] 向量维度不匹配: {len(vector)} != {self.embedding_dim}")
            # 如果向量不存在，生成伪向量
            if len(vector) == 0:
                vector = np.random.rand(self.embedding_dim).astype(np.float32)
                vector = vector / np.linalg.norm(vector) if np.linalg.norm(vector) > 0 else vector
                memory_obj["vec"] = vector.tolist()
        
        vector_index_pos = self.vector_manager.add_vector(vector, storage_id)
        
        # 创建存储记录
        store_record = {
            "storage_id": storage_id,
            "archived_path": None,
            "vector_index": vector_index_pos,
            "memory_obj": memory_obj,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "access_count": 0,
            "last_accessed": None
        }
        
        # 添加到存储数据
        self.store_data["memories"].append(store_record)
        
        # 更新元数据和索引
        self._update_metadata()
        self._update_indices()
        self.store_data["updated_at"] = datetime.now().isoformat()
        
        print(f"[存储] 已存储记忆: {storage_id} ({memory_obj.get('type', 'unknown')})")
        return storage_id
    
    def store_batch(self, memory_objs: List[Dict]) -> List[str]:
        """
        批量存储记忆
        
        Args:
            memory_objs: 记忆对象列表
        
        Returns:
            存储ID列表
        """
        storage_ids = []
        for mem in memory_objs:
            try:
                sid = self.store(mem)
                storage_ids.append(sid)
            except Exception as e:
                print(f"[WARN] 存储记忆失败: {e}")
        
        # 批量保存时延迟保存到磁盘
        self.save()
        return storage_ids
    
    def load(self, storage_id: str) -> Optional[Dict]:
        """
        加载记忆
        
        Args:
            storage_id: 存储ID
        
        Returns:
            记忆对象，如果未找到则返回None
        """
        for mem in self.store_data["memories"]:
            if mem["storage_id"] == storage_id:
                # 更新访问统计
                mem["access_count"] = mem.get("access_count", 0) + 1
                mem["last_accessed"] = datetime.now().isoformat()
                
                # 返回记忆对象
                return mem["memory_obj"]
        
        return None
    
    def load_by_time_range(self, start: datetime, end: datetime) -> List[Dict]:
        """
        按时间范围加载记忆
        
        Args:
            start: 开始时间
            end: 结束时间
        
        Returns:
            记忆对象列表
        """
        results = []
        
        for mem in self.store_data["memories"]:
            mem_obj = mem["memory_obj"]
            timestamp = mem_obj.get("timestamp")
            
            if not timestamp:
                continue
            
            try:
                mem_dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                if start <= mem_dt <= end:
                    results.append(mem_obj)
            except Exception as e:
                print(f"[WARN] 解析时间戳失败 {timestamp}: {e}")
        
        print(f"[时间] 时间范围 {start} 到 {end} 找到 {len(results)} 条记忆")
        return results
    
    def archive(self, storage_ids: List[str], reason: str = "manual_archive") -> bool:
        """
        归档记忆
        
        Args:
            storage_ids: 要归档的存储ID列表
            reason: 归档原因
        
        Returns:
            是否成功
        """
        if not self.enable_archive or not storage_ids:
            return False
        
        # 查找要归档的记忆
        memories_to_archive = []
        memory_objs_to_archive = []
        
        for mem in self.store_data["memories"][:]:  # 使用副本遍历
            if mem["storage_id"] in storage_ids:
                memories_to_archive.append(mem)
                memory_objs_to_archive.append(mem["memory_obj"])
        
        if not memories_to_archive:
            print("[归档] 未找到要归档的记忆")
            return False
        
        print(f"[归档] 准备归档 {len(memories_to_archive)} 条记忆，原因: {reason}")
        
        try:
            # 创建归档文件
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
            archive_filename = f"archive_{timestamp}_{reason}.json"
            
            # 使用归档管理器创建路径
            if self.archive_manager and len(memory_objs_to_archive) > 0:
                archive_path = self.archive_manager.create_archive_path(
                    memory_objs_to_archive[0], reason
                )
            else:
                archive_dir = os.path.join(self.storage_dir, "archived", "manual")
                os.makedirs(archive_dir, exist_ok=True)
                archive_path = os.path.join(archive_dir, archive_filename)
            
            # 保存归档数据
            archive_data = {
                "metadata": {
                    "archive_time": datetime.now().isoformat(),
                    "reason": reason,
                    "count": len(memories_to_archive),
                    "storage_ids": storage_ids
                },
                "memories": memories_to_archive
            }
            
            with open(archive_path, "w", encoding="utf-8") as f:
                json.dump(archive_data, f, indent=2, ensure_ascii=False)
            
            print(f"[归档] 已保存归档文件: {archive_path}")
            
            # 创建符号链接
            if self.archive_manager and len(memory_objs_to_archive) > 0:
                self.archive_manager.create_symlinks(archive_path, memory_objs_to_archive[0])
            
            # 从主存储中移除（标记为归档）
            for mem in memories_to_archive:
                # 标记为已归档
                mem["archived_path"] = archive_path
                mem["archived_at"] = datetime.now().isoformat()
                mem["archive_reason"] = reason
                
                # 从向量索引中移除（标记删除）
                self.vector_manager.remove_vector(mem["storage_id"])
            
            # 更新索引
            self._update_indices()
            
            # 更新归档索引
            if self.archive_manager:
                self.archive_manager.update_archive_index()
            
            return True
            
        except Exception as e:
            print(f"[ERROR] 归档失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def retrieve(self, query_vector: np.ndarray, top_k: int = 5, 
                 filter_type: Optional[str] = None) -> List[Tuple[Dict, float]]:
        """
        检索相似记忆
        
        Args:
            query_vector: 查询向量
            top_k: 返回结果数量
            filter_type: 过滤类型（只返回指定类型的记忆）
        
        Returns:
            [(记忆对象, 相似度分数), ...]
        """
        # 向量相似度搜索
        vector_results = self.vector_manager.search_similar(query_vector, top_k * 2)
        
        # 应用过滤
        filtered_results = []
        for storage_id, similarity in vector_results:
            mem_obj = self.load(storage_id)
            if not mem_obj:
                continue
            
            # 类型过滤
            if filter_type and mem_obj.get("type") != filter_type:
                continue
            
            filtered_results.append((mem_obj, similarity))
            
            if len(filtered_results) >= top_k:
                break
        
        # 按相似度排序
        filtered_results.sort(key=lambda x: x[1], reverse=True)
        return filtered_results[:top_k]
    
    def save(self):
        """保存存储数据到磁盘"""
        # 原子保存：先写临时文件再替换
        tmp_path = self.json_store_path + ".tmp"
        
        try:
            # 备份原文件
            if os.path.exists(self.json_store_path):
                shutil.copy2(self.json_store_path, self.backup_path)
            
            # 写入临时文件
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(self.store_data, f, indent=2, ensure_ascii=False)
            
            # 替换原文件
            os.replace(tmp_path, self.json_store_path)
            
            # 保存向量索引
            self.vector_manager.save_index()
            
            print(f"[保存] 存储数据已保存: {self.json_store_path}")
            return True
            
        except Exception as e:
            print(f"[ERROR] 保存存储失败: {e}")
            # 尝试恢复备份
            if os.path.exists(self.backup_path):
                shutil.copy2(self.backup_path, self.json_store_path)
                print("[恢复] 已从备份恢复存储文件")
            return False
    
    def get_stats(self) -> Dict:
        """获取存储统计信息"""
        memories = self.store_data["memories"]
        
        # 基本统计
        total = len(memories)
        archived = sum(1 for m in memories if m.get("archived_path"))
        active = total - archived
        
        # 访问统计
        access_counts = [m.get("access_count", 0) for m in memories]
        avg_access = sum(access_counts) / total if total > 0 else 0
        
        # 最近访问
        recent_accessed = sum(1 for m in memories if m.get("last_accessed"))
        
        # 类型分布
        type_dist = self.store_data["metadata"].get("type_distribution", {})
        
        # 时间范围
        date_range = self.store_data["metadata"].get("date_range", {})
        
        return {
            "total_memories": total,
            "active_memories": active,
            "archived_memories": archived,
            "memory_types": type_dist,
            "date_range": date_range,
            "access_stats": {
                "average_access": avg_access,
                "recently_accessed": recent_accessed,
                "total_accesses": sum(access_counts)
            },
            "storage_size": {
                "json_file": os.path.getsize(self.json_store_path) if os.path.exists(self.json_store_path) else 0,
                "vector_index": os.path.getsize(self.vector_manager.index_file) if os.path.exists(self.vector_manager.index_file) else 0
            },
            "vector_index": {
                "type": self.vector_manager.index_type,
                "dimension": self.vector_manager.dimension,
                "vector_count": len([m for m in memories if not m.get("archived_path")])
            }
        }


# ==================== 性能优化建议 ====================
"""
存储、检索、归档的性能基准和优化建议

性能基准目标：
1. 存储：单条记忆存储 < 10ms，批量存储 (100条) < 0.5s
2. 检索：查询检索 (top-10) < 50ms，支持并发查询
3. 归档：批量归档 (100条) < 1s
4. 内存使用：存储10000条记忆 < 500MB

优化建议：

一、存储优化：
1. 向量索引选择：
   - 小规模 (<10K): Faiss Flat 索引
   - 中规模 (10K-1M): Faiss IVF 索引
   - 大规模 (>1M): Faiss HNSW 索引
2. 数据压缩：
   - JSON 使用 gzip 压缩存储
   - 向量使用 FP16 精度存储（减少50%空间）
3. 批量操作：
   - 批量存储使用事务机制
   - 延迟写入磁盘，批量提交

二、检索优化：
1. 多级缓存：
   - 一级缓存：热点记忆内存缓存
   - 二级缓存：向量索引内存映射
2. 索引优化：
   - 定期重建索引（每10K次更新）
   - 使用量化减少内存使用
3. 查询优化：
   - 预处理查询向量
   - 并行检索多个索引

三、归档优化：
1. 异步归档：
   - 归档操作在后台线程执行
   - 支持增量归档
2. 压缩归档：
   - 归档文件使用 gzip 压缩
   - 删除重复数据
3. 智能分类：
   - 使用聚类算法自动分类
   - 建立归档索引加速查找

四、可靠性优化：
1. 原子操作：
   - 所有文件操作先写临时文件再替换
   - 支持回滚机制
2. 定期备份：
   - 自动备份存储文件
   - 支持时间点恢复
3. 完整性检查：
   - 定期验证数据和索引一致性
   - 自动修复损坏数据

具体实现建议：
1. 实现配置系统，允许用户调整性能参数
2. 添加监控和日志，跟踪性能指标
3. 定期维护任务（清理、优化、备份）
"""


# ==================== 使用示例 ====================
def example_usage():
    """使用示例"""
    print("=" * 70)
    print("长期存储系统 - 使用示例")
    print("=" * 70)
    
    # 1. 初始化存储
    storage = LongTermStorage(
        storage_dir="./example_storage",
        embedding_dim=768,
        enable_archive=True
    )
    
    # 2. 创建示例记忆
    example_memory = {
        "id": "test_memory_001",
        "fact": "关于量子计算的基础概念",
        "content": "量子比特是量子计算的基本单位，可以同时处于0和1的叠加态",
        "vec": np.random.rand(768).tolist(),  # 768维向量
        "importance": 0.9,
        "type": "knowledge",
        "timestamp": datetime.now().isoformat(),
        "confidence": 0.95,
        "metadata": {
            "emotion": "neutral",
            "keywords": ["量子", "计算", "qiskit"],
            "language": "zh"
        }
    }
    
    # 3. 存储记忆
    storage_id = storage.store(example_memory)
    print(f"[示例] 存储记忆完成，ID: {storage_id}")
    
    # 4. 加载记忆
    loaded_memory = storage.load(storage_id)
    if loaded_memory:
        print(f"[示例] 加载记忆成功: {loaded_memory['fact'][:50]}...")
    
    # 5. 时间范围查询
    start_time = datetime.now() - timedelta(days=1)
    end_time = datetime.now()
    time_based = storage.load_by_time_range(start_time, end_time)
    print(f"[示例] 时间范围查询找到 {len(time_based)} 条记忆")
    
    # 6. 相似性检索
    query_vec = np.random.rand(768)
    similar = storage.retrieve(query_vec, top_k=3)
    print(f"[示例] 相似性检索找到 {len(similar)} 条相似记忆")
    
    # 7. 归档记忆
    archive_success = storage.archive([storage_id], reason="example_archive")
    if archive_success:
        print(f"[示例] 归档记忆成功")
    
    # 8. 获取统计信息
    stats = storage.get_stats()
    print(f"[示例] 存储统计:")
    print(f"  总记忆数: {stats['total_memories']}")
    print(f"  活跃记忆: {stats['active_memories']}")
    print(f"  归档记忆: {stats['archived_memories']}")
    print(f"  类型分布: {stats['memory_types']}")
    
    # 9. 保存存储
    storage.save()
    
    print("\n" + "=" * 70)
    print("[完成] 示例执行完成")
    print("=" * 70)


if __name__ == "__main__":
    # 执行示例
    example_usage()