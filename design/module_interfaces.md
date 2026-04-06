# OpenClaw生物学启发记忆引擎 - 接口规范文档

## 1. 核心数据类型定义

### 1.1 MemoryItem - 基础记忆单元
```python
@dataclass
class MemoryItem:
    """记忆基础数据单元，贯穿所有模块"""
    
    # 核心标识
    id: str                   # 唯一标识符 (UUID v4)
    content: str              # 原始内容文本
    content_type: str        # 内容类型: "text", "image", "audio", "multimodal"
    timestamp: str           # ISO格式时间戳: "YYYY-MM-DDTHH:MM:SS"
    
    # 处理状态
    status: str             # 状态: "registered", "encoded", "appraised", "consolidated", "stored", "archived"
    confidence: float       # 置信度 [0, 1]
    source: str             # 数据来源: e.g., "file.txt", "api", "user_input"
    
    # 特征表示
    features: Dict[str, Any] = field(default_factory=dict)  # 原始特征
    embedding: Optional[np.ndarray] = None                 # 768维语义向量
    embedding_model: str = "default"                       # 使用的嵌入模型
    
    # 模块处理标记
    sensory_tags: List[str] = field(default_factory=list)   # 感觉标记
    working_metadata: Dict[str, Any] = field(default_factory=dict)  # 工作记忆元数据
    emotional_scores: Dict[str, float] = field(default_factory=dict)  # 情绪评分
    consolidation_info: Dict[str, Any] = field(default_factory=dict)  # 巩固信息
    storage_location: Dict[str, str] = field(default_factory=dict)    # 存储位置
    
    # 索引与检索
    keywords: List[str] = field(default_factory=list)      # 关键词提取
    categories: List[str] = field(default_factory=list)    # 分类标签
    relations: List[str] = field(default_factory=list)     # 关联记忆ID
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典（可序列化）"""
        # 处理numpy数组
        base = asdict(self)
        if self.embedding is not None:
            base['embedding'] = self.embedding.tolist()
        return base
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MemoryItem':
        """从字典创建实例"""
        if 'embedding' in data and isinstance(data['embedding'], list):
            data['embedding'] = np.array(data['embedding'])
        return cls(**data)
```

### 1.2 MemoryContext - 处理上下文
```python
@dataclass
class MemoryContext:
    """记忆处理上下文，包含环境和状态信息"""
    
    # 时间上下文
    processing_time: datetime              # 处理时间
    session_id: str                       # 会话标识
    user_id: Optional[str] = None         # 用户标识（可选）
    
    # 环境上下文
    device_info: Dict[str, str] = field(default_factory=dict)  # 设备信息
    location_info: Dict[str, str] = field(default_factory=dict)  # 位置信息
    app_context: Dict[str, Any] = field(default_factory=dict)  # 应用上下文
    
    # 认知状态
    attention_focus: List[str] = field(default_factory=list)  # 注意焦点
    emotional_state: Dict[str, float] = field(default_factory=dict)  # 当前情绪
    working_memory_load: float = 0.0      # 工作记忆负载 [0, 1]
    
    # 处理历史
    processing_path: List[str] = field(default_factory=list)  # 处理路径: ["sensory", "working", ...]
    module_stats: Dict[str, Dict] = field(default_factory=dict)  # 各模块统计
    
    def update_path(self, module_name: str) -> None:
        """更新处理路径"""
        self.processing_path.append(module_name)
```

### 1.3 MemoryQuery - 检索查询
```python
@dataclass
class MemoryQuery:
    """记忆检索查询对象"""
    
    # 查询内容
    query_text: Optional[str] = None      # 文本查询
    query_vector: Optional[np.ndarray] = None  # 查询向量
    query_context: Optional[MemoryContext] = None  # 查询上下文
    
    # 过滤条件
    content_types: List[str] = field(default_factory=list)  # 内容类型过滤
    time_range: Optional[Tuple[datetime, datetime]] = None  # 时间范围
    categories: List[str] = field(default_factory=list)     # 类别过滤
    min_confidence: float = 0.0            # 最小置信度
    min_importance: float = 0.0            # 最小重要性
    
    # 检索配置
    max_results: int = 10                  # 最大结果数
    similarity_threshold: float = 0.0      # 相似度阈值
    retrieval_mode: str = "hybrid"         # 检索模式: "semantic", "temporal", "causal", "hybrid"
    
    # 混合检索权重
    weights: Dict[str, float] = field(default_factory=lambda: {
        "semantic": 0.4,    # 语义相似度权重
        "temporal": 0.3,    # 时间邻近权重
        "causal": 0.2,      # 因果关联权重
        "emotional": 0.1    # 情绪重要性权重
    })
    
    # 高级选项
    enable_explanation: bool = True       # 启用结果解释
    enable_clustering: bool = False       # 启用结果聚类
    include_metadata: bool = True         # 包含元数据
    
    def validate(self) -> bool:
        """验证查询参数"""
        if not self.query_text and self.query_vector is None:
            return False
        return True
```

### 1.4 MemoryResult - 处理/检索结果
```python
@dataclass
class MemoryResult:
    """记忆处理或检索结果"""
    
    # 结果指标
    success: bool                         # 是否成功
    status_code: int = 200                # 状态码
    message: str = ""                     # 消息
    
    # 结果数据
    data: Union[MemoryItem, List[MemoryItem], Dict[str, Any], None] = None
    metadata: Dict[str, Any] = field(default_factory=dict)  # 元数据
    
    # 性能指标
    processing_time_ms: float = 0.0       # 处理耗时（毫秒）
    memory_used_mb: float = 0.0           # 内存使用（MB）
    
    # 分页信息（列表结果时）
    total_count: int = 0                  # 总数
    offset: int = 0                       # 偏移
    limit: int = 0                        # 限制
    
    def with_data(self, data: Any) -> 'MemoryResult':
        """链式设置数据"""
        self.data = data
        return self
    
    def with_metadata(self, key: str, value: Any) -> 'MemoryResult':
        """链式添加元数据"""
        self.metadata[key] = value
        return self
```

## 2. 模块接口规范

### 2.1 基础模块接口 (MemoryModule)
所有模块继承的基础接口：

```python
class MemoryModule(ABC):
    """记忆模块基础接口"""
    
    @abstractmethod
    def __init__(self, config: Dict[str, Any], context: Optional[MemoryContext] = None):
        """初始化模块
        
        Args:
            config: 模块配置
            context: 初始化上下文
        """
        pass
    
    @abstractmethod
    def process(self, memory_item: MemoryItem, context: Optional[MemoryContext] = None) -> MemoryResult:
        """处理单个记忆项
        
        Args:
            memory_item: 待处理的记忆项
            context: 处理上下文
            
        Returns:
            MemoryResult: 处理结果
        """
        pass
    
    @abstractmethod
    def batch_process(self, memory_items: List[MemoryItem], context: Optional[MemoryContext] = None) -> MemoryResult:
        """批量处理记忆项
        
        Args:
            memory_items: 待处理的记忆项列表
            context: 处理上下文
            
        Returns:
            MemoryResult: 批量处理结果
        """
        pass
    
    @abstractmethod
    def get_stats(self) -> Dict[str, Any]:
        """获取模块统计信息
        
        Returns:
            统计信息字典
        """
        pass
    
    @abstractmethod
    def reset_stats(self) -> None:
        """重置统计信息"""
        pass
    
    @abstractmethod
    def update_config(self, new_config: Dict[str, Any]) -> MemoryResult:
        """更新模块配置
        
        Args:
            new_config: 新配置
            
        Returns:
            更新结果
        """
        pass
    
    # 可选方法
    def preprocess(self, input_data: Any, context: Optional[MemoryContext] = None) -> MemoryItem:
        """预处理原始数据为MemoryItem（可选）"""
        if isinstance(input_data, MemoryItem):
            return input_data
        # 默认实现：转换文本
        return MemoryItem(
            id=str(uuid.uuid4()),
            content=str(input_data),
            content_type="text",
            timestamp=datetime.now().isoformat(),
            status="raw"
        )
    
    def postprocess(self, result: MemoryResult, context: Optional[MemoryContext] = None) -> Any:
        """后处理结果（可选）"""
        return result.data if result.success else None
```

### 2.2 感觉登记模块接口 (SensoryRegistration)
```python
class SensoryRegistration(MemoryModule):
    """感觉登记模块接口"""
    
    def __init__(self, config: Dict[str, Any], context: Optional[MemoryContext] = None):
        super().__init__(config, context)
        self.buffer_size = config.get("buffer_size", 1000)  # 缓冲区大小
        self.retention_ms = config.get("retention_ms", 2000)  # 保持时间（毫秒）
        self.channels = config.get("channels", ["text"])     # 支持通道
        
    def process(self, memory_item: MemoryItem, context: Optional[MemoryContext] = None) -> MemoryResult:
        """处理感觉输入
        
        功能：
        1. 多通道特征提取
        2. 注意力选择
        3. 缓冲管理
        """
        pass
    
    def register_sensory_input(self, 
                              input_data: Any, 
                              channel: str = "text",
                              timestamp: Optional[datetime] = None) -> MemoryResult:
        """注册感觉输入（扩展接口）
        
        Args:
            input_data: 原始输入数据
            channel: 输入通道 ("text", "audio", "image", etc.)
            timestamp: 输入时间戳
            
        Returns:
            注册结果
        """
        pass
    
    def get_buffer_status(self) -> Dict[str, Any]:
        """获取缓冲区状态
        
        Returns:
            各通道缓冲区状态
        """
        pass
    
    def flush_buffer(self, channel: Optional[str] = None) -> MemoryResult:
        """刷新缓冲区
        
        Args:
            channel: 指定通道，None表示所有通道
            
        Returns:
            刷新结果
        """
        pass
    
    def set_attention_filter(self, filter_rules: Dict[str, Any]) -> MemoryResult:
        """设置注意力过滤器
        
        Args:
            filter_rules: 过滤规则
            
        Returns:
            设置结果
        """
        pass
```

### 2.3 工作记忆模块接口 (WorkingMemory)
```python
class WorkingMemory(MemoryModule):
    """工作记忆模块接口"""
    
    def __init__(self, config: Dict[str, Any], context: Optional[MemoryContext] = None):
        super().__init__(config, context)
        self.capacity = config.get("capacity", 20)  # 容量限制
        self.expiration_sec = config.get("expiration_sec", 30)  # 过期时间（秒）
        
    def process(self, memory_item: MemoryItem, context: Optional[MemoryContext] = None) -> MemoryResult:
        """工作记忆编码
        
        功能：
        1. 容量管理（LRU替换）
        2. 多模态编码
        3. 组块化处理
        """
        pass
    
    def encode(self, 
               content: str, 
               importance: float = 0.5,
               source: Optional[str] = None,
               tags: Optional[List[str]] = None) -> MemoryResult:
        """编码记忆（扩展接口）
        
        Args:
            content: 内容文本
            importance: 重要性评分
            source: 来源
            tags: 标签
            
        Returns:
            编码结果（包含EncodedMemory）
        """
        pass
    
    def query_similar(self, 
                     query: Union[str, np.ndarray], 
                     top_k: int = 5, 
                     min_similarity: float = 0.3) -> MemoryResult:
        """查询相似记忆
        
        Args:
            query: 查询文本或向量
            top_k: 返回数量
            min_similarity: 最小相似度
            
        Returns:
            相似记忆结果
        """
        pass
    
    def get_buffer_stats(self) -> Dict[str, Any]:
        """获取缓冲区统计
        
        Returns:
            容量使用、命中率等信息
        """
        pass
    
    def clear(self) -> MemoryResult:
        """清空工作记忆缓冲区"""
        pass
    
    def chunk_items(self, items: List[MemoryItem], max_chunk_size: int = 5) -> MemoryResult:
        """组块化记忆项
        
        Args:
            items: 记忆项列表
            max_chunk_size: 最大组块大小
            
        Returns:
            组块化结果
        """
        pass
```

### 2.4 情绪评估模块接口 (EmotionalAppraisal)
```python
class EmotionalAppraisal(MemoryModule):
    """情绪评估模块接口"""
    
    def __init__(self, config: Dict[str, Any], context: Optional[MemoryContext] = None):
        super().__init__(config, context)
        self.model_type = config.get("model_type", "pad")  # 情绪模型类型
        self.min_confidence = config.get("min_confidence", 0.3)  # 最小置信度
        
    def process(self, memory_item: MemoryItem, context: Optional[MemoryContext] = None) -> MemoryResult:
        """情绪评估
        
        功能：
        1. PAD三维情绪评分（愉悦度、激活度、支配度）
        2. 重要性评分
        3. 上下文感知分类
        """
        pass
    
    def analyze_emotion(self, 
                       text: str, 
                       context: Optional[Dict[str, Any]] = None) -> MemoryResult:
        """分析文本情绪（扩展接口）
        
        Args:
            text: 待分析文本
            context: 上下文信息
            
        Returns:
            情绪分析结果
        """
        pass
    
    def get_emotional_weight(self, memory_id: str) -> Optional[float]:
        """获取记忆的情绪权重
        
        Args:
            memory_id: 记忆ID
            
        Returns:
            情绪权重（0-2之间），None表示不存在
        """
        pass
    
    def update_emotional_context(self, context_update: Dict[str, Any]) -> MemoryResult:
        """更新情绪上下文
        
        Args:
            context_update: 上下文更新
            
        Returns:
            更新结果
        """
        pass
    
    def classify_memory(self, memory_item: MemoryItem) -> Dict[str, Any]:
        """记忆分类
        
        Args:
            memory_item: 记忆项
            
        Returns:
            分类结果
        """
        pass
```

### 2.5 巩固修剪模块接口 (ConsolidationPruning)
```python
class ConsolidationPruning(MemoryModule):
    """巩固修剪模块接口"""
    
    def __init__(self, config: Dict[str, Any], context: Optional[MemoryContext] = None):
        super().__init__(config, context)
        self.lambda_base = config.get("lambda_base", {})  # 基准衰减率
        self.checkpoints = config.get("checkpoints", [0.083, 1, 9, 24, 48, 168, 720])  # 检查时间点（小时）
        self.pruning_percentile = config.get("pruning_percentile", 20)  # 修剪百分位
        
    def process(self, memory_item: MemoryItem, context: Optional[MemoryContext] = None) -> MemoryResult:
        """记忆巩固
        
        功能：
        1. 遗忘曲线强度更新
        2. 重要性重新计算
        3. 修剪决策
        """
        pass
    
    def consolidate_batch(self, 
                         memories: List[MemoryItem], 
                         current_time: Optional[float] = None) -> MemoryResult:
        """批量巩固（扩展接口）
        
        Args:
            memories: 记忆项列表
            current_time: 当前时间（小时）
            
        Returns:
            巩固结果
        """
        pass
    
    def prune(self, 
             memories: List[MemoryItem], 
             percentile: Optional[float] = None) -> MemoryResult:
        """修剪记忆
        
        Args:
            memories: 记忆项列表
            percentile: 修剪百分位
            
        Returns:
            修剪结果（保留和删除的记忆）
        """
        pass
    
    def detect_causal_relations(self, memories: List[MemoryItem]) -> MemoryResult:
        """检测因果关系
        
        Args:
            memories: 记忆项列表
            
        Returns:
            因果检测结果
        """
        pass
    
    def get_forgetting_curve(self, 
                            memory_type: str, 
                            days: int = 30) -> Dict[str, List[float]]:
        """获取遗忘曲线预测
        
        Args:
            memory_type: 记忆类型
            days: 预测天数
            
        Returns:
            遗忘曲线数据
        """
        pass
    
    def schedule_review(self, 
                       memory_item: MemoryItem, 
                       algorithm: str = "sm2") -> Dict[str, Any]:
        """安排复习计划
        
        Args:
            memory_item: 记忆项
            algorithm: 间隔重复算法（sm2, fsrs等）
            
        Returns:
            复习计划
        """
        pass
```

### 2.6 长期存储模块接口 (LongTermStorage)
```python
class LongTermStorage(MemoryModule):
    """长期存储模块接口"""
    
    def __init__(self, config: Dict[str, Any], context: Optional[MemoryContext] = None):
        super().__init__(config, context)
        self.storage_backend = config.get("storage_backend", "sqlite")  # 存储后端
        self.max_size_gb = config.get("max_size_gb", 10.0)  # 最大存储大小（GB）
        self.retention_days = config.get("retention_days", 365)  # 保留天数
        
    def process(self, memory_item: MemoryItem, context: Optional[MemoryContext] = None) -> MemoryResult:
        """存储记忆
        
        功能：
        1. 分层存储
        2. 索引建立
        3. 版本控制
        """
        pass
    
    def store(self, 
             memory_item: MemoryItem, 
             overwrite: bool = False) -> MemoryResult:
        """存储记忆（扩展接口）
        
        Args:
            memory_item: 记忆项
            overwrite: 是否覆盖
            
        Returns:
            存储结果
        """
        pass
    
    def retrieve(self, 
                query: MemoryQuery) -> MemoryResult:
        """检索记忆
        
        Args:
            query: 检索查询
            
        Returns:
            检索结果
        """
        pass
    
    def delete(self, 
              memory_id: str, 
              soft_delete: bool = True) -> MemoryResult:
        """删除记忆
        
        Args:
            memory_id: 记忆ID
            soft_delete: 软删除（可恢复）
            
        Returns:
            删除结果
        """
        pass
    
    def archive(self, 
               memory_ids: List[str], 
               archive_name: Optional[str] = None) -> MemoryResult:
        """归档记忆
        
        Args:
            memory_ids: 记忆ID列表
            archive_name: 归档名称
            
        Returns:
            归档结果
        """
        pass
    
    def export(self, 
              format_type: str = "json", 
              output_path: Optional[str] = None) -> MemoryResult:
        """导出记忆
        
        Args:
            format_type: 导出格式
            output_path: 输出路径
            
        Returns:
            导出结果
        """
        pass
    
    def rebuild_index(self) -> MemoryResult:
        """重建索引
        
        Returns:
            重建结果
        """
        pass
```

### 2.7 关联检索模块接口 (RecallAssociation)
```python
class RecallAssociation(MemoryModule):
    """关联检索引擎接口"""
    
    def __init__(self, config: Dict[str, Any], context: Optional[MemoryContext] = None):
        super().__init__(config, context)
        self.retrieval_modes = config.get("retrieval_modes", ["semantic", "temporal", "causal", "hybrid"])
        self.default_weights = config.get("default_weights", {
            "semantic": 0.4, "temporal": 0.3, "causal": 0.2, "emotional": 0.1
        })
        
    def process(self, memory_item: MemoryItem, context: Optional[MemoryContext] = None) -> MemoryResult:
        """处理查询（通常用于查询记忆）
        
        注意：此模块主要用于检索，process方法将query_text视为查询
        """
        pass
    
    def retrieve_hybrid(self, 
                       query: MemoryQuery) -> MemoryResult:
        """混合检索（扩展接口）
        
        Args:
            query: 检索查询
            
        Returns:
            检索结果，包含多维评分和解释
        """
        pass
    
    def retrieve_by_similarity(self, 
                              query_vector: np.ndarray, 
                              top_k: int = 10,
                              filter_type: Optional[str] = None) -> MemoryResult:
        """基于语义相似度检索
        
        Args:
            query_vector: 查询向量
            top_k: 返回数量
            filter_type: 类型过滤
            
        Returns:
            相似度检索结果
        """
        pass
    
    def retrieve_by_time(self,
                        time_reference: datetime,
                        time_window_hours: float = 24.0,
                        top_k: int = 10) -> MemoryResult:
        """基于时间邻近性检索
        
        Args:
            time_reference: 参考时间点
            time_window_hours: 时间窗口大小（小时）
            top_k: 返回数量
            
        Returns:
            时间邻近检索结果
        """
        pass
    
    def retrieve_by_causality(self,
                            source_memory_id: str,
                            max_depth: int = 3,
                            top_k: int = 10) -> MemoryResult:
        """基于因果关系检索
        
        Args:
            source_memory_id: 源记忆ID
            max_depth: 最大因果链深度
            top_k: 返回数量
            
        Returns:
            因果关联检索结果
        """
        pass
    
    def cluster_by_theme(self, 
                        memories: List[MemoryItem],
                        threshold: float = 0.7) -> MemoryResult:
        """主题聚类
        
        Args:
            memories: 记忆项列表
            threshold: 聚类阈值
            
        Returns:
            聚类结果
        """
        pass
    
    def detect_causal_relationships(self, 
                                   memories: List[MemoryItem]) -> MemoryResult:
        """检测因果关系
        
        Args:
            memories: 记忆项列表
            
        Returns:
            因果检测结果
        """
        pass
```

### 2.8 中央协调管理器接口 (CentralCoordinator)
```python
class CentralCoordinator:
    """中央协调管理器接口"""
    
    def __init__(self, config: Dict[str, Any]):
        """初始化协调器"""
        self.modules: Dict[str, MemoryModule] = {}
        self.processing_pipeline: List[str] = config.get("pipeline", [
            "sensory_registration",
            "working_memory", 
            "emotional_appraisal",
            "consolidation_pruning",
            "long_term_storage"
        ])
        self.event_system = EventSystem()
        
    def register_module(self, 
                       name: str, 
                       module: MemoryModule) -> MemoryResult:
        """注册模块
        
        Args:
            name: 模块名称
            module: 模块实例
            
        Returns:
            注册结果
        """
        pass
    
    def unregister_module(self, name: str) -> MemoryResult:
        """注销模块
        
        Args:
            name: 模块名称
            
        Returns:
            注销结果
        """
        pass
    
    def process_memory(self, 
                      input_data: Any, 
                      context: Optional[MemoryContext] = None) -> MemoryResult:
        """处理记忆（完整管道）
        
        Args:
            input_data: 输入数据（文本、MemoryItem等）
            context: 处理上下文
            
        Returns:
            处理结果
        """
        pass
    
    def retrieve_memory(self, 
                       query: MemoryQuery,
                       context: Optional[MemoryContext] = None) -> MemoryResult:
        """检索记忆
        
        Args:
            query: 检索查询
            context: 检索上下文
            
        Returns:
            检索结果
        """
        pass
    
    def execute_pipeline(self, 
                        pipeline: List[str], 
                        memory_item: MemoryItem,
                        context: Optional[MemoryContext] = None) -> MemoryResult:
        """执行指定管道
        
        Args:
            pipeline: 管道模块名列表
            memory_item: 记忆项
            context: 上下文
            
        Returns:
            管道执行结果
        """
        pass
    
    def get_system_stats(self) -> Dict[str, Any]:
        """获取系统统计信息
        
        Returns:
            系统统计
        """
        pass
    
    def export_state(self, 
                    output_path: str, 
                    include_data: bool = True) -> MemoryResult:
        """导出系统状态
        
        Args:
            output_path: 输出路径
            include_data: 是否包含数据
            
        Returns:
            导出结果
        """
        pass
    
    def import_state(self, input_path: str) -> MemoryResult:
        """导入系统状态
        
        Args:
            input_path: 输入路径
            
        Returns:
            导入结果
        """
        pass
```

## 3. 事件系统接口

### 3.1 事件类型定义
```python
class MemoryEvent:
    """记忆事件基类"""
    event_type: str
    timestamp: datetime
    memory_id: Optional[str]
    module_name: Optional[str]
    data: Dict[str, Any]

# 核心事件类型
EVENT_TYPES = {
    # 处理流程事件
    "MEMORY_REGISTERED": "memory.registered",
    "MEMORY_ENCODED": "memory.encoded", 
    "MEMORY_APPRAISED": "memory.appraised",
    "MEMORY_CONSOLIDATED": "memory.consolidated",
    "MEMORY_STORED": "memory.stored",
    "MEMORY_RETRIEVED": "memory.retrieved",
    "MEMORY_PRUNED": "memory.pruned",
    
    # 系统事件
    "MODULE_REGISTERED": "module.registered",
    "MODULE_ERROR": "module.error",
    "CONFIG_UPDATED": "config.updated",
    "STORAGE_FULL": "storage.full",
    
    # 性能事件
    "PROCESSING_START": "processing.start",
    "PROCESSING_END": "processing.end",
    "PERFORMANCE_ALERT": "performance.alert",
}
```

### 3.2 事件处理器接口
```python
class EventHandler(ABC):
    """事件处理器接口"""
    
    @abstractmethod
    def handle(self, event: MemoryEvent) -> None:
        """处理事件"""
        pass

class EventSystem:
    """事件系统"""
    
    def __init__(self):
        self.subscribers: Dict[str, List[EventHandler]] = defaultdict(list)
    
    def subscribe(self, event_type: str, handler: EventHandler) -> None:
        """订阅事件"""
        self.subscribers[event_type].append(handler)
    
    def unsubscribe(self, event_type: str, handler: EventHandler) -> None:
        """取消订阅"""
        if handler in self.subscribers[event_type]:
            self.subscribers[event_type].remove(handler)
    
    def publish(self, event: MemoryEvent) -> None:
        """发布事件"""
        for handler in self.subscribers.get(event.event_type, []):
            try:
                handler.handle(event)
            except Exception as e:
                logging.error(f"事件处理失败: {e}")
```

## 4. 配置系统

### 4.1 配置结构定义
```python
@dataclass
class SystemConfig:
    """系统级配置"""
    
    # 系统标识
    system_name: str = "OpenClawBiologicalMemoryEngine"
    version: str = "1.0.0"
    
    # 性能配置
    max_concurrent_requests: int = 10
    max_memory_usage_mb: int = 1024
    processing_timeout_sec: int = 30
    
    # 管道配置
    enable_pipeline: bool = True
    pipeline_order: List[str] = field(default_factory=lambda: [
        "sensory_registration",
        "working_memory", 
        "emotional_appraisal",
        "consolidation_pruning",
        "long_term_storage"
    ])
    
    # 模块配置覆盖
    module_configs: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    
    # 存储配置
    storage_path: str = "./memory_storage"
    backup_enabled: bool = True
    backup_interval_hours: int = 24
    
    # 日志配置
    log_level: str = "INFO"
    log_file: Optional[str] = "memory_engine.log"
    enable_audit_log: bool = True
    
    def validate(self) -> List[str]:
        """验证配置，返回错误列表"""
        errors = []
        if not self.system_name:
            errors.append("system_name不能为空")
        if self.max_concurrent_requests <= 0:
            errors.append("max_concurrent_requests必须大于0")
        return errors
```

### 4.2 模块配置示例
```python
# 感觉登记模块配置示例
SENSORY_CONFIG = {
    "buffer_size": 1000,
    "retention_ms": {
        "visual": 500,
        "auditory": 4000, 
        "text": 2000
    },
    "channels": ["text", "log", "api"],
    "feature_extractors": {
        "text": ["keywords", "entities", "sentiment"],
        "log": ["timestamp", "level", "source"]
    },
    "attention_rules": [
        {"pattern": "error", "priority": 1.5},
        {"pattern": "warning", "priority": 1.2}
    ]
}

# 工作记忆模块配置示例  
WORKING_MEMORY_CONFIG = {
    "capacity": 20,
    "expiration_sec": 30,
    "embedding_backend": "ollama",  # ollama, sentence-transformers, fake
    "chunking_enabled": True,
    "chunk_size": 5,
    "replacement_policy": "lru"
}

# 情绪评估模块配置示例
EMOTIONAL_APPRAISAL_CONFIG = {
    "model_type": "pad",  # pad, dimensional, categorical
    "min_confidence": 0.3,
    "importance_factors": {
        "emotional_arousal": 0.4,
        "personal_relevance": 0.3,
        "novelty": 0.2,
        "utility": 0.1
    },
    "classification_rules": {
        "fact": ["包含事实信息", "数据驱动"],
        "decision": ["做了决定", "选择了"],
        "opinion": ["我觉得", "我认为"],
        "instruction": ["步骤", "如何", "教程"]
    }
}

# 巩固修剪模块配置示例
CONSOLIDATION_CONFIG = {
    "lambda_base": {
        "fact": 0.01,
        "decision": 0.03, 
        "opinion": 0.05,
        "instruction": 0.02,
        "default": 0.03
    },
    "checkpoints": [0.083, 1, 9, 24, 48, 168, 720],
    "pruning_percentile": 20,
    "strength_weight": 0.6,
    "emotion_weight": 0.2,
    "causal_weight": 0.2,
    "min_strength_threshold": 0.01
}

# 长期存储模块配置示例
STORAGE_CONFIG = {
    "storage_backend": "sqlite",  # sqlite, json, postgresql
    "max_size_gb": 10.0,
    "retention_days": 365,
    "compression_enabled": True,
    "encryption_enabled": False,
    "index_types": ["vector", "fulltext", "temporal", "categorical"],
    "sharding_strategy": {"by_date": "monthly"}
}

# 关联检索模块配置示例
RECALL_CONFIG = {
    "retrieval_modes": ["semantic", "temporal", "causal", "hybrid"],
    "default_weights": {
        "semantic": 0.4,
        "temporal": 0.3,
        "causal": 0.2,
        "emotional": 0.1
    },
    "time_decay_alpha": 0.01,
    "clustering_threshold": 0.7,
    "causal_detection_enabled": True,
    "cache_enabled": True,
    "max_cache_size": 1000
}
```

## 5. 错误代码定义

### 5.1 错误代码表
```python
class ErrorCode:
    """错误代码常量"""
    
    # 成功
    SUCCESS = 0
    
    # 通用错误 (1-99)
    UNKNOWN_ERROR = 1
    INVALID_PARAMETER = 2
    RESOURCE_NOT_FOUND = 3
    PERMISSION_DENIED = 4
    TIMEOUT = 5
    # 模块错误 (100-199)
    MODULE_NOT_REGISTERED = 101
    MODULE_INIT_FAILED = 102
    MODULE_PROCESSING_ERROR = 103
    MODULE_CONFIG_INVALID = 104
    
    # 存储错误 (200-299)
    STORAGE_FULL = 201
    STORAGE_IO_ERROR = 202
    STORAGE_CORRUPTED = 203
    STORAGE_CONNECTION_FAILED = 204
    
    # 处理错误 (300-399)
    PROCESSING_TIMEOUT = 301
    MEMORY_OVERFLOW = 302
    INVALID_DATA_FORMAT = 303
    PROCESSING_PIPELINE_BROKEN = 304
    
    # 检索错误 (400-499)
    QUERY_INVALID = 401
    INDEX_NOT_READY = 402
    RETRIEVAL_FAILED = 403
    SIMILARITY_CALCULATION_ERROR = 404
    
    # 配置错误 (500-599)
    CONFIG_VALIDATION_FAILED = 501
    CONFIG_FILE_NOT_FOUND = 502
    CONFIG_PARSE_ERROR = 503
```

### 5.2 错误响应格式
```python
@dataclass
class ErrorResponse:
    """错误响应格式"""
    code: int
    message: str
    details: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    request_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
```

## 6. 接口版本控制

### 6.1 版本策略
- 主版本号：不兼容的API修改
- 次版本号：向后兼容的功能性新增
- 修订号：向后兼容的Bug修复

### 6.2 版本标识
- API版本通过HTTP头或URL路径标识
- 配置版本通过配置文件version字段
- 数据版本通过MemoryItem中的version字段

### 6.3 向后兼容保证
1. 配置文件向后兼容：新版本可读取旧配置
2. 数据格式向后兼容：新版本可读取旧数据
3. API向后兼容：v1.x API保持不变，新增v2

## 7. 集成测试接口

### 7.1 测试接口定义
```python
class TestInterface:
    """测试专用接口"""
    
    def reset_all_modules(self) -> MemoryResult:
        """重置所有模块状态（测试用）"""
        pass
    
    def inject_test_data(self, 
                        module_name: str, 
                        test_data: List[Dict[str, Any]]) -> MemoryResult:
        """注入测试数据（测试用）"""
        pass
    
    def simulate_pipeline(self, 
                         input_data: Any,
                         breakpoints: List[str] = []) -> MemoryResult:
        """模拟管道执行，支持断点（测试用）"""
        pass
    
    def validate_data_integrity(self) -> List[Dict[str, Any]]:
        """验证数据完整性（测试用）"""
        pass
    
    def performance_benchmark(self, 
                            test_cases: List[Dict[str, Any]],
                            iterations: int = 100) -> Dict[str, Any]:
        """性能基准测试（测试用）"""
        pass
```

---

**文档版本**：1.0  
**最后更新**：2026-03-28  
**作者**：OpenClaw架构设计子代理  
**状态**：接口草案，待实现