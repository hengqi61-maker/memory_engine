# 感觉登记与初步加工模块设计 (Sensory Input & Perception)

## 1. 概述

本模块是人脑记忆流程的起点，负责处理OpenClaw的会话数据，将其转换为结构化的RawMemoryChunk列表。主要功能包括：

1. **会话边界处理**：基于「每次开启新对话后处理上一个完整会话」的策略
2. **文本预处理**：清洗、切分、实体提取
3. **事件检测**：识别OpenClaw的会话开始/结束事件

## 2. 设计目标

- **实时性**：支持实时会话流处理，而非仅日志文件
- **结构化**：将非结构化对话转换为结构化表示
- **可扩展**：易于集成到OpenClaw事件系统

## 3. 数据模型

### 3.1 RawMemoryChunk

```python
from dataclasses import dataclass
from typing import List, Dict, Optional, Any
from datetime import datetime

@dataclass
class RawMemoryChunk:
    """原始记忆块"""
    id: str  # 唯一标识符，格式: session_{session_id}_chunk_{index}_{timestamp}
    raw_text: str  # 原始文本
    cleaned_text: str  # 清洗后文本
    entities: List[Entity]  # 命名实体列表
    speakers: List[str]  # 发言者列表
    timestamp_start: datetime  # 块开始时间
    timestamp_end: datetime  # 块结束时间
    topic: Optional[str] = None  # 话题标签
    metadata: Dict[str, Any] = None  # 额外元数据
    session_id: Optional[str] = None  # 所属会话ID
    channel: Optional[str] = None  # 渠道信息
```

### 3.2 Entity

```python
@dataclass
class Entity:
    """命名实体"""
    text: str  # 实体文本
    type: str  # 实体类型: PERSON, LOCATION, ORGANIZATION, DATE, TIME, etc.
    start_pos: int  # 在cleaned_text中的起始位置
    end_pos: int  # 在cleaned_text中的结束位置
    confidence: float  # 置信度
```

### 3.3 SessionData

```python
@dataclass
class SessionData:
    """完整会话数据"""
    session_id: str
    messages: List[Message]  # 按时间排序的消息列表
    start_time: datetime
    end_time: datetime
    channel: str
    metadata: Dict[str, Any]

@dataclass
class Message:
    """单条消息"""
    timestamp: datetime
    speaker: str  # 发言者ID或名称
    content: str  # 原始消息内容
    message_id: str
    raw_data: Dict[str, Any]  # 原始数据（用于扩展）
```

## 4. 核心类设计

### 4.1 系统架构

```
OpenClaw事件系统 → SensoryInputProcessor → RawMemoryChunk列表 → 下游记忆引擎
```

### 4.2 核心类设计

```python
class SensoryInputProcessor:
    """感觉登记与初步加工处理器"""
    
    def __init__(self, config: Optional[Dict] = None):
        """
        初始化处理器
        
        Args:
            config: 配置字典，包含：
                - entity_extractor: 实体提取器类型（'spacy', 'jieba', 'regex'）
                - min_chunk_size: 最小块大小（字符数）
                - max_chunk_size: 最大块大小（字符数）
                - topic_detection: 话题检测开关
                - entity_extraction: 实体提取开关
        """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.session_buffer: Dict[str, SessionData] = {}
        self.current_session_id: Optional[str] = None
        
    def process_session(self, session_data: SessionData) -> List[RawMemoryChunk]:
        """
        处理完整会话，生成RawMemoryChunk列表
        流程：
        1. 文本清洗
        2. 发言者与时间线提取
        3. 话题转折点检测
        4. 智能切分
        5. 实体提取
        6. 生成RawMemoryChunk
        """
        pass
    
    def detect_session_boundaries(self, log_lines: List[str]) -> List[SessionData]:
        """
        从原始日志中检测会话边界
        基于OpenClaw日志格式识别会话开始/结束事件
        """
        pass
    
    def clean_text(self, text: str) -> str:
        """
        文本清洗：
        - 移除控制字符
        - 统一换行符
        - 去除多余空格
        - 标准化标点
        - 移除无关前缀（如时间戳、发言者标签）
        """
        pass
    
    def extract_speakers_and_timestamps(self, messages: List[Message]) -> Dict:
        """
        从消息列表中提取发言者和时间线
        返回结构化数据
        """
        pass
    
    def detect_topic_shifts(self, messages: List[Message], window_size: int = 5) -> List[int]:
        """
        基于文本相似度检测话题转折点
        返回转折点位置索引
        """
        pass
    
    def split_into_chunks(self, 
                         messages: List[Message],
                         topic_shift_points:
        """提取发言者和时间线，返回结构化对话"""
        pass
    
    def detect_topic_shifts(self, structured_dialog: List[Dict]) -> List[int]:
        """
        检测话题转折点
        基于语义相似度、关键词变化、发言者切换等
        返回切分点索引列表
        """
        pass
    
    def split_into_chunks(self, structured_dialog: List[Dict], 
                         split_points: List[int]) -> List[Dict]:
        """基于切分点将对话分成多个块"""
        pass
    
    def extract_entities(self, text: str) -> List[Entity]:
        """
        提取命名实体
        支持多种方式：
        1. 基于规则（正则表达式）
        2. 基于预训练模型（如spaCy, Stanford NER）
        3. 基于API（如OpenAI, DeepSeek）
        """
        pass
    
    def generate_chunk_id(self, session_id: str, chunk_index: int) -> str:
        """生成唯一块ID"""
        return f"session_{session_id}_chunk_{chunk_index}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
```

## 5. 处理流程

### 5.1 流程图

```
┌─────────────────┐
│  会话结束事件    │
├─────────────────┤
│ 提取完整会话记录 │
├─────────────────┤
│   文本清洗      │
├─────────────────┤
│ 发言者/时间提取 │
├─────────────────┤
│  话题转折检测   │
├─────────────────┤
│   智能切分     │
├────────────────┤
│   实体提取     │
├────────────────┤
│ 生成RawMemoryChunk │
└────────────────┘
```

### 5.2 详细步骤

1. **输入获取**：
   - 方式1：从OpenClaw日志文件读取完整会话
   - 方式2：通过API实时获取会话流
   - 方式3：监听OpenClaw事件系统

2. **会话边界检测**：
   - 识别 `[SESSION_START]` 和 `[SESSION_END]` 事件
   - 基于时间间隔（如超过30分钟无活动）
   - 基于渠道切换（如从webchat切换到discord）

3. **文本预处理**：
   - 清洗：移除日志前缀、时间戳、无关格式
   - 标准化：统一编码、换行符、空格
   - 结构化：提取发言者、消息内容、时间戳

4. **话题转折检测**：
   - 计算消息间的语义相似度
   - 检测关键词变化（TF-IDF差异）
   - 考虑发言者切换和长时间停顿

5. **智能切分**：
   - 在话题转折点处切分
   - 确保每个块有合理长度（如5-20条消息）
   - 保留上下文连贯性

6. **实体提取**：
   - 使用混合方法提取命名实体
   - 支持中文和英文
   - 保留发言者信息。

6. **实体提取**：
   - 人名、组织名、地点、时间、日期
   - 技术术语、项目名称、代码片段
   - 提取的实体需标注位置和类型

## 6. 集成建议

### 6.1 与OpenClaw事件系统集成

OpenClaw事件系统提供了以下可能的事件：

```python
# 事件类型
EVENT_SESSION_START = "session_start"
EVENT_MESSAGE_RECEIVED = "message_received"
EVENT_SESSION_END = "session_end"
EVENT_CHANNEL_SWITCH = "channel_switch"

# 集成方式
class OpenClawEventListener:
    def __init__(self, processor: SensoryInputProcessor):
        self.processor = processor
        self.register_handlers()
    
    def register_handlers(self):
        openclaw.events.subscribe(EVENT_SESSION_START, self.on_session_start)
        openclaw.events.subscribe(EVENT_MESSAGE_RECEIVED, self.on_message_received)
        openclaw.events.subscribe(EVENT_SESSION_END, self.on_session_end)
    
    def on_session_start(self, event_data):
        # 开始新会话，处理上一个会话（如果存在）
        if self.processor.current_session_id:
            self.process_previous_session()
        self.processor.current_session_id = event_data['session_id']
        self.processor.session_buffer[event_data['session_id']] = SessionData(...)
    
    def on_message_received(self, event_data):
        # 添加消息到当前会话
        session = self.processor.session_buffer.get(self.processor.current_session_id)
        if session:
            session.messages.append(Message(...))
    
    def on_session_end(self, event_data):
        # 标记会话结束，可立即处理或等待下个会话开始
        session = self.processor.session_buffer.get(event_data['session_id'])
        if session:
            session.end_time = event_data['timestamp']
```

### 6.2 配置选项

```python
config = {
    "session_timeout_minutes": 30,  # 会话超时时间
    "max_chunk_size": 1000,  # 最大块大小（字符）
    "min_chunk_size": 100,   # 最小块大小
    "entity_extractor": "rule_based",  # 实体提取器类型
    "topic_detection_method": "semantic_similarity",
    "clean_text_rules": {
        "remove_timestamps": True,
        "remove_speaker_prefix": True,
        "normalize_whitespace": True
    }
}
```

## 7. 与现有代码关系

### 7.1 参考 `openclaw_memory_engine_fixed.py` 中的 `_split_text` 方法

现有方法的局限性：
- 仅处理静态文本文件
- 按标题和段落分割，不考虑会话结构
- 缺乏实体提取和话题分析

改进方向：
- 支持实时会话流处理
- 结合发言者信息和时间线
- 集成实体提取和话题检测

### 7.2 扩展点

```python
# 扩展现有引擎
from sensory_input_perception import SensoryInputProcessor

class EnhancedOpenClawMemoryEngine(OpenClawMemoryEngine):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.sensory_processor = SensoryInputProcessor()
    
    def ingest_realtime_session(self, session_data):
        """实时摄入会话数据"""
        chunks = self.sensory_processor.process_session(session_data)
        for chunk in chunks:
            self._process_chunk(chunk)
    
    def _process_chunk(self, chunk):
        """处理单个RawMemoryChunk"""
        # 转换为引擎内部格式
        memory = {
            "id": chunk.id,
            "content": chunk.cleaned_text,
            "vec": self._embed(chunk.cleaned_text),
            "importance": self._evaluate_importance(chunk),
            "type": "conversation",
            "timestamp": chunk.timestamp_start.isoformat(),
            "metadata": {
                "speakers": chunk.speakers,
                "entities": [e.text for e in chunk.entities],
                "session_id": chunk.session_id
            }
        }
        self.short_term_buffer.append(memory)
```

## 8. 测试用例

### 8.1 单元测试

```python
def test_session_boundary_detection():
    processor = SensoryInputProcessor()
    log_lines = [
        "[2026-03-28 10:00:00] [SESSION_START] session_123 channel=webchat",
        "[2026-03-28 10:00:01] [USER] 齐恒: 你好",
        "[2026-03-28 10:00:05] [AGENT] Claw: 有什么可以帮助你的？",
        "[2026-03-28 10:05:00] [SESSION_END] session_123"
    ]
    sessions = processor.detect_session_boundaries(log_lines)
    assert len(sessions) == 1
    assert sessions[0].session_id == "session_123"

def test_entity_extraction():
    processor = SensoryInputProcessor()
    text = "齐恒来自东华大学，学习应用物理"
    entities = processor.extract_entities(text)
    assert any(e.text == "齐恒" and e.type == "PERSON" for e in entities)
    assert any(e.text == "东华大学" and e.type == "ORGANIZATION" for e in entities)
```

### 8.2 集成测试

```python
def test_end_to_end_processing():
    # 模拟完整会话
    session_data = SessionData(...)
    processor = SensoryInputProcessor()
    chunks = processor.process_session(session_data)
    
    assert len(chunks) > 0
    for chunk in chunks:
        assert chunk.cleaned_text
        assert chunk.timestamp_start <= chunk.timestamp_end
        assert chunk.session_id == session_data.session_id
```

## 9. 部署与性能考虑

1. **性能优化**：
   - 批量处理实体提取
   - 缓存预训练模型
   - 异步处理大型会话

2. **资源要求**：
   - 实体提取模型内存占用
   - 会话缓冲区大小限制
   - 磁盘I/O（日志读取）

3. **错误处理**：
   - 会话数据不完整的处理
   - 实体提取失败降级
   - 网络超时重试

## 10. 后续扩展

1. **多语言支持**：支持中英文混合会话
2. **情感分析**：分析发言者情感倾向
3. **意图识别**：识别用户意图类别
4. **关系提取**：提取实体间关系
5. **摘要生成**：为每个chunk生成摘要

---

## 附录A：OpenClaw日志格式示例

```
[2026-03-28 10:00:00] [SESSION_START] session_id=abc123 channel=webchat user_id=user_456
[2026-03-28 10:00:01] [MESSAGE] speaker=user_456 content=你好，我想了解量子计算
[2026-03-28 10:00:05] [MESSAGE] speaker=agent content=量子计算是一门新兴学科...
[2026-03-28 10:05:00] [SESSION_END] session_id=abc123 duration=300s
```

## 附录B：实体类型定义

```python
ENTITY_TYPES = {
    "PERSON": "人名",
    "LOCATION": "地点",
    "ORGANIZATION": "组织/机构",
    "DATE": "日期",
    "TIME": "时间",
    "QUANTITY": "数量",
    "TECHNICAL_TERM": "技术术语",
    "PROJECT": "项目名称",
    "CODE": "代码片段",
    "URL": "网址",
    "EMAIL": "邮箱"
}
```