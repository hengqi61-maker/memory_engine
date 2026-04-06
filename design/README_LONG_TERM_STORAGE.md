# 长期存储与持久化系统设计文档

## 概述
本系统为 OpenClaw 记忆引擎提供可靠的双重存储（JSON + 向量索引）和归档管理。它设计为可平滑迁移的替换方案，完全兼容现有的 `EnhancedStorageLayer` 和 `ArchivedMemoryManager` 接口。

## 核心特性

### 1. 双重存储引擎
- **JSON 存储**：完整保存记忆对象，包括所有元数据
- **向量索引**：使用 Faiss（或备选 numpy）存储 768 维向量，支持高效相似度检索
- **原子操作**：所有文件操作使用临时文件+替换机制，保证数据完整性

### 2. 归档管理系统
- **安全归档**：修剪的记忆被安全归档，而非删除
- **多维分类**：支持按日期、重要性、类型、主题自动分类
- **智能索引**：归档文件建立索引，便于快速检索

### 3. 元数据索引
- **二级索引**：类型、情绪标签、关键词等元数据建立索引
- **时间范围查询**：`load_by_time_range()` 接口支持时间范围检索
- **快速过滤**：检索时可按类型、重要性等条件过滤

## 系统架构

### 文件结构
```
long_term_storage/              # 主存储目录
├── memory_store.json           # JSON 存储文件（完整数据）
├── memory_store.json.bak       # 备份文件
├── vectors/                    # 向量索引目录
│   ├── vectors.faiss           # Faiss 索引文件
│   └── vector_mapping.json     # 向量-记忆ID映射表
└── archived/                   # 归档目录
    ├── by_date/                # 按日期归档
    │   └── 2026/03/28/normal_pruning/
    ├── by_importance/          # 按重要性归档
    │   ├── high/
    │   ├── medium/
    │   └── low/
    ├── by_type/                # 按类型归档
    │   ├── knowledge/
    │   ├── task/
    │   └── code/
    ├── by_theme/               # 按主题归档
    │   ├── quantum_computing/
    │   └── python_programming/
    └── archive_index.json      # 归档索引文件
```

### 数据模型（StoreSchema）
```python
{
    "version": "1.0.0",                    # 存储格式版本
    "created_at": "2026-03-28T10:00:00",   # 创建时间
    "updated_at": "2026-03-28T10:30:00",   # 更新时间
    "config": {...},                       # 存储配置
    "metadata": {...},                     # 元数据统计
    "memories": [                          # 记忆对象数组
        {
            "storage_id": "mem_20260328_001",  # 唯一存储ID
            "archived_path": null,             # 归档路径
            "vector_index": 0,                 # 向量索引位置
            "memory_obj": {...},               # 原始记忆对象
            "created_at": "...",               # 创建时间
            "updated_at": "...",               # 更新时间
            "access_count": 5,                 # 访问次数
            "last_accessed": "..."             # 最后访问时间
        }
    ],
    "indices": {...}                        # 索引信息
}
```

## 核心 API

### LongTermStorage 类
```python
# 初始化
storage = LongTermStorage(
    storage_dir="./long_term_storage",
    embedding_dim=768,
    enable_archive=True
)

# 存储记忆
storage_id = storage.store(memory_obj)

# 加载记忆
memory = storage.load(storage_id)

# 时间范围查询
memories = storage.load_by_time_range(start_date, end_date)

# 相似性检索
results = storage.retrieve(query_vector, top_k=5, filter_type="knowledge")

# 归档记忆
success = storage.archive([storage_id1, storage_id2], reason="manual_archive")

# 获取统计信息
stats = storage.get_stats()

# 保存到磁盘
storage.save()
```

### 适配器层（兼容现有代码）
```python
# 替换现有的 EnhancedStorageLayer
adapter = LongTermStorageAdapter(
    base_path="./memory/engine/openclaw_memory",
    archive_dir="./memory/engine/archived"
)

# 完全兼容现有接口
memories = adapter.load()                     # 加载记忆
adapter.save_atomic(data, summary_content)    # 原子保存
adapter.archive_pruned(pruned_memories, reason)  # 归档修剪记忆
```

## 迁移指南

### 1. 自动迁移工具
```python
from long_term_adapter import MigrationTool

# 从旧存储迁移到新系统
MigrationTool.migrate_from_old_storage(
    old_storage_dir="./memory/engine",
    new_storage_dir="./long_term_storage"
)
```

### 2. 渐进式迁移
1. 保持现有系统运行
2. 使用迁移工具复制数据到新系统
3. 测试新系统的功能和性能
4. 切换存储适配器到新系统
5. 验证数据一致性
6. 停用旧系统

## 性能优化

### 存储性能
- **批量存储**：使用 `store_batch()` 减少磁盘 I/O
- **延迟写入**：内存缓存，批量提交
- **向量优化**：Faiss 索引定期重建，使用量化减少内存

### 检索性能
- **多级缓存**：热点记忆内存缓存
- **索引优化**：使用 IVF/HNSW 索引加速大规模检索
- **并行查询**：支持并发检索操作

### 归档性能
- **异步归档**：后台线程执行归档操作
- **增量归档**：只归档变化的部分
- **压缩存储**：归档文件使用 gzip 压缩

### 可靠性
- **原子操作**：所有文件操作保证一致性
- **定期备份**：自动备份存储文件
- **完整性检查**：定期验证数据和索引一致性
- **恢复机制**：从备份文件恢复数据

## 向量索引方案

### 索引类型选择
| 数据规模 | 推荐索引 | 特点 |
|----------|----------|------|
| < 10K 条 | Faiss Flat | 精确检索，内存占用低 |
| 10K - 1M | Faiss IVF | 快速近似检索，支持量化 |
| > 1M 条 | Faiss HNSW | 超大规模，高性能检索 |

### 维度处理
- 固定 768 维向量（可配置）
- 支持 FP16 精度压缩（减少 50% 存储空间）
- 自动维度检查和修复

## 归档策略

### 自动分类规则
1. **按日期**：年/月/日/修剪原因 多级目录
2. **按重要性**：高 (>0.8)、中 (0.5-0.8)、低 (<0.5)
3. **按类型**：knowledge、task、code、log、emotion
4. **按主题**：基于关键词自动聚类

### 归档保留策略
- **短期归档**：保留最近 30 天的详细归档
- **中期归档**：超过 30 天按重要性压缩归档
- **长期归档**：超过 1 年的归档可迁移到冷存储

## 兼容性保证

### 接口兼容
- 完全实现 `EnhancedStorageLayer` 的 `load()`、`save_atomic()`、`archive_pruned()` 方法
- 保持相同的参数和返回值类型
- 支持现有的归档原因和日志格式

### 数据兼容
- 支持从旧 JSON 格式自动迁移
- 保持记忆 ID、内容和元数据的完整性
- 迁移后可回滚到旧系统

### 性能兼容
- 新系统的性能不低于旧系统
- 支持现有工作负载
- 可配置性能参数以适应不同场景

## 使用示例

### 示例 1：基本使用
```python
from long_term_storage import LongTermStorage
import numpy as np

# 初始化
storage = LongTermStorage("./my_storage")

# 创建记忆
memory = {
    "id": "memory_001",
    "content": "量子计算的基础概念",
    "vec": np.random.rand(768).tolist(),
    "importance": 0.9,
    "type": "knowledge",
    "timestamp": "2026-03-28T10:00:00"
}

# 存储
storage_id = storage.store(memory)

# 检索
query_vec = np.random.rand(768)
results = storage.retrieve(query_vec, top_k=3)

print(f"找到 {len(results)} 条相关记忆")
```

### 示例 2：替换现有存储层
```python
# 修改 OpenClawMemoryEngine 的初始化部分
from long_term_adapter import LongTermStorageAdapter

# 替换原来的 EnhancedStorageLayer
self.storage = LongTermStorageAdapter(
    base_path=os.path.join(self.base_dir, memory_name),
    archive_dir=os.path.join(self.base_dir, "archived")
)
```

### 示例 3：迁移现有数据
```python
from long_term_adapter import MigrationTool

# 一键迁移
MigrationTool.migrate_from_old_storage(
    old_storage_dir="./memory/engine",
    new_storage_dir="./long_term_storage"
)

# 验证迁移结果
from long_term_storage import LongTermStorage
storage = LongTermStorage("./long_term_storage")
stats = storage.get_stats()
print(f"迁移了 {stats['total_memories']} 条记忆")
```

## 基准测试

### 性能目标
| 操作 | 目标性能 | 备注 |
|------|----------|------|
| 单条存储 | < 10ms | 包括向量索引更新 |
| 批量存储 (100条) | < 0.5s | 批量优化 |
| 查询检索 (top-10) | < 50ms | 向量相似度检索 |
| 时间范围查询 | < 100ms | 使用日期索引 |
| 批量归档 (100条) | < 1s | 异步归档 |
| 内存使用 (10K条) | < 500MB | 包括向量索引 |

### 可靠性目标
- **数据持久性**：99.999% 数据不丢失
- **系统可用性**：99.9% 运行时间
- **恢复时间**：小于 5 分钟恢复完整服务

## 部署建议

### 开发环境
- 使用 numpy 作为向量索引（无外部依赖）
- 禁用归档功能以简化测试
- 使用内存存储加速测试

### 生产环境
- 使用 Faiss 作为向量索引（需要安装 faiss-cpu 或 faiss-gpu）
- 启用归档功能保证数据安全
- 配置定期备份和完整性检查
- 监控存储使用情况和性能指标

### 扩展建议
- **分布式存储**：支持多节点分布式向量索引
- **云存储集成**：归档文件可存储到云存储服务
- **增量备份**：支持增量备份减少带宽使用
- **数据加密**：敏感数据加密存储

## 故障排除

### 常见问题
1. **向量维度不匹配**：检查 embedding_dim 配置，确保所有向量维度一致
2. **Faiss 安装失败**：使用 `pip install faiss-cpu` 或使用 numpy 备用方案
3. **存储文件损坏**：使用备份文件恢复，或从 JSON 数据重建向量索引
4. **归档失败**：检查文件权限和磁盘空间

### 日志监控
- 启用 debug 模式查看详细操作日志
- 定期检查存储统计信息
- 监控磁盘使用情况和系统负载

## 未来发展

### 短期规划
1. 支持更多的向量索引算法
2. 优化归档压缩算法
3. 添加数据加密功能

### 长期规划
1. 支持分布式向量检索
2. 集成云存储服务
3. 实现智能记忆聚类
4. 支持多模态记忆存储

---

## 总结
长期存储与持久化系统提供了健壮、高效、可靠的双重存储方案，完全兼容现有 OpenClaw 记忆引擎，支持平滑迁移。通过 JSON 存储 + 向量索引的双重机制，既保证了数据的完整性和可读性，又提供了高效的检索能力。归档管理系统确保了修剪记忆的安全性和可追溯性，为记忆引擎的长期运行提供了坚实基础。