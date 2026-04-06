# 关联检索与回忆模块 (Recall & Association)

## 概述

这是 OpenClaw 记忆引擎的第六个核心模块，旨在提供增强的检索系统，支持时间邻近性、因果链推理、主题聚类和多模式检索。

## 数学公式推导

### 1. 时间衰减函数

记忆的时间权重基于指数衰减模型，模拟人类记忆的遗忘曲线：

```
weight_time = exp(-α × Δt)
```

其中：
- α: 衰减系数 (默认 0.01 小时⁻¹)
- Δt: 当前时间与记忆时间的差值 (小时)

**科学依据**：艾宾浩斯遗忘曲线表明记忆强度随时间呈指数衰减。

**参数调优建议**：
- α = 0.005 小时⁻¹: 缓慢衰减 (长期记忆)
- α = 0.01 小时⁻¹: 中等衰减 (默认)
- α = 0.02 小时⁻¹: 快速衰减 (短期记忆)

### 2. 因果关联评分

因果评分基于多因素综合模型：

```
causal_score = w₁ × pattern_match + w₂ × cooccurrence + w₃ × temporal_order
```

**各分量计算**：

1. **模式匹配 (pattern_match)**：
   - 使用正则表达式检测因果逻辑连接词
   - 权重：0.6（基于语言学研究表明逻辑连接词是因果关系的强指标）

2. **词语共现 (cooccurrence)**：
   - 记忆在同一上下文窗口共同出现的频率
   - 权重：0.3（基于分布式语义假说）

3. **时间顺序 (temporal_order)**：
   - 基于时间戳的顺序关系（原因在结果之前）
   - 权重：0.1（基于因果关系的时序约束）

### 3. 主题聚类算法

使用层次聚类与余弦相似度：

**相似度计算**：
```
similarity(m₁, m₂) = (cosine_sim(vec₁, vec₂) + 1) / 2
```

**聚类条件**：
- 记忆对相似度 ≥ 阈值 θ (默认 0.7)
- 聚类大小 ∈ [min_size, max_size] (默认 [2, 50])

**聚类中心**：
```
centroid = (1/n) × Σ vecᵢ
```

**聚类一致性**：
```
coherence = (2/(n(n-1))) × Σ similarity(vecᵢ, vecⱼ)
```

### 4. 混合检索评分

综合评分采用加权平均法：

```
total_score = Σ (wᵢ × scoreᵢ) / Σ wᵢ
```

**各维度评分标准化**：
- 语义相似度：余弦相似度映射到 [0,1]
- 时间邻近性：时间衰减函数的输出 ∈ [0,1]
- 因果关联：因果评分 ∈ [0,1]
- 情绪重要性：情绪权重归一化 ∈ [0,2]
- 主题聚类：二元评分（匹配=1, 不匹配=0）

**默认权重分配**：
- 语义相似度: 0.4（认知心理学研究表明语义相似性是主要检索线索）
- 时间邻近性: 0.3（基于记忆的时间组织理论）
- 因果关联: 0.2（基于联想记忆的因果推理）
- 情绪重要性: 0.1（基于情绪增强记忆效应）

## 算法性能分析

### 时间复杂度

1. **全量检索**：O(N × D)
   - N: 记忆数量
   - D: 维度数量（默认5个维度）

2. **缓存优化后**：O(N × (1 - h) × D)
   - h: 缓存命中率（预计 >70%）

3. **聚类加速检索**：O(C × M + N × D)
   - C: 聚类数量（远小于 N）
   - M: 最大聚类大小

### 空间复杂度

1. **向量存储**：O(N × 768 × 4 bytes) ≈ 3KB/记忆
2. **缓存系统**：O(K × L)
   - K: 缓存条目数（默认1000）
   - L: 相似度计算开销

3. **聚类结构**：O(C × (768 + M))
   - 存储聚类中心和成员关系

## 集成指南

### 步骤1：导入模块

```python
from recall_association import RecallAssociation, RetrievalQuery, ConsolidatedMemory
```

### 步骤2：初始化引擎

```python
# 基本初始化
recall_engine = RecallAssociation()

# 高级配置
recall_engine = RecallAssociation(config={
    "time_decay_alpha": 0.02,  # 更强的时间衰减
    "clustering_threshold": 0.6,  # 更宽松的聚类
    "enable_causal_detection": True,
    "enable_clustering": True,
})
```

### 步骤3：替换现有检索方法

**原代码（openclaw_memory_engine_fixed.py）**：
```python
def retrieve(self, query_text, top_k=5, query_type=None):
    # 现有简单检索逻辑
    ...
```

**新代码**：
```python
def retrieve(self, query_text, top_k=5, query_type=None):
    """增强检索方法"""
    if not hasattr(self, 'recall_engine'):
        # 初始化关联检索引擎
        self.recall_engine = RecallAssociation(
            long_term_storage=self.storage,
            emotional_appraisal=self.emotional_appraisal,
            config={
                "enable_caching": True,
                "max_cache_size": 1000
            }
        )
        self.recall_engine.load_from_long_term_storage()
    
    # 构建查询
    query = RetrievalQuery(
        query_text=query_text,
        query_type=query_type,
        max_results=top_k,
        weights={
            "semantic": 0.5,
            "temporal": 0.3,
            "causal": 0.1,
            "emotional": 0.1
        }
    )
    
    # 执行检索
    results = recall_engine.retrieve_hybrid(query)
    
    # 转换为原格式（保持兼容性）
    legacy_results = []
    for result in results:
        legacy_results.append({
            "fact": result.memory.content,
            "score": result.total_score,
            "type": result.memory.memory_type,
            "timestamp": result.memory.timestamp,
            "explanation": result.explanation
        })
    
    return legacy_results
```

### 步骤4：渐进增强策略

#### 阶段1：基本替换
仅替换检索逻辑，保持原有接口不变。

#### 阶段2：因果推理增强
启用因果检测，为记忆添加因果链接元数据：

```python
# 在睡眠周期中调用
causal_links = recall_engine.detect_causal_relationships(memories)
print(f"检测到 {len(causal_links)} 个因果关系")
```

#### 阶段3：主题聚类增强
启用主题聚类，加速检索并提供主题过滤：

```python
clusters = recall_engine.cluster_by_theme(memories)
print(f"创建了 {len(clusters)} 个主题聚类")
```

#### 阶段4：主题聚类集成

```python
# 定期运行主题聚类
clusters = recall_engine.cluster_by_theme(memories)
for cluster_id, cluster in clusters.items():
    print(f"聚类 {cluster_id}: {len(cluster.member_ids)} 个记忆, 主题: {cluster.theme_keywords}")
```

### 步骤5：情绪权重集成

```python
# 更新情绪权重
recall_engine.update_emotional_weights()

# 在检索中自动考虑情绪权重
query.weights["emotional"] = 0.2  # 提高情绪权重
```

## 性能优化策略

### 1. 缓存机制

- **向量缓存**：已计算的向量存储在内存中
- **相似度缓存**：频繁计算的相似度对进行缓存
- **结果缓存**：常见查询的结果缓存，设置TTL

### 2. 批量处理

```python
# 批量检索多个查询
queries = [
    RetrievalQuery(query_text="量子", query_type="knowledge"),
    RetrievalQuery(query_text="代码", query_type="task"),
    RetrievalQuery(query_text="学习", query_type="knowledge")
]
batch_results = recall_engine.batch_retrieve(queries)
```

### 3. 增量更新

- 新记忆增量添加到现有聚类
- 因果链接增量检测
- 缓存增量更新

## 实际可行性考量

### 硬件要求

1. **内存占用**：
   - 1000条记忆：memory_vectors.npy
- 聚类结构：clusters.json
- 因果链接：causal_links.json

### 3. 增量更新

- 新记忆：添加后更新相关聚类
- 删除记忆：标记删除，延迟清理
- 更新记忆：重新计算相关相似度

### 4. 配置调优

**针对不同规模记忆库的推荐配置：**

```python
# 小型记忆库 (<1000条)
config_small = {
    "enable_caching": False,  # 缓存开销不划算
    "clustering_threshold": ˚C以下或 40°C 以上性能下降)

## 评估指标

### 检索质量

1. **精度@K**：前K个结果中相关记忆的比例
2. **召回率@K**：前K个结果中覆盖的相关记忆比例
3. **平均精度 (MAP)**：考虑排序的精度
4. **归一化折扣累积增益 (nDCG)**：考虑排序位置的相关性

### 性能指标

1. **响应时间**：平均检索时间
2. **吞吐量**：每秒处理的查询数
3. **缓存命中率**：缓存减少的计算比例
4. **内存使用**：平均内存占用

### 认知合理性

1. **时间偏置验证**：近期记忆是否获得更高权重
2. **因果链完整性**：检测到的因果关系是否合理
3. **主题一致性

### 因果检测质量

1. **因果链接准确率**：检测到的正确因果关系比例
2. **因果方向准确率**：原因→结果方向正确率
3. **因果置信度校准**：置信度与实际正确率的一致性

### 聚类质量

1. **轮廓系数**：聚类内聚性与分离性 (-1到1, 越高越好)
2. **戴维森堡丁指数**：聚类紧密度与分离度的比值
3. **主题相关性**：人工评估聚类主题的一致性

## 科学依据

### 认知神经科学基础

1. **时间组织理论**：
   - 基于Tulving的时序记忆模型
   - 证据：fMRI显示海马体编码时间上下文
   - 实现：指数衰减函数模拟时间梯度

2. **联想记忆理论**：
   - 基于Hebbian学习规则
   - 证据：神经元同步激活增强连接
   - 实现：因果链接检测和主题聚类

3. **情绪增强效应**：
   - 基于杏仁核对记忆的调制作用
   - 证据：情绪事件记忆更深刻
   - 实现：情绪权重因子

### 计算模型参考

1. **向量空间模型**：
   - 基于Distributional Hypothesis
   - 实现：768维语义向量

2. **认知架构集成**：
   - ACT-R的declarative memory启发
   - SOAR的chunking机制参考
   - CLARION的隐式/显式记忆区分

## 故障排除

### 常见问题

1. **检索速度慢**：
   - 启用缓存：`config["enable_caching"] = True`
   - 减少聚类：`config["enable_clustering"] = False`
   - 限制检索数量：`max_results = 10`

2. **因果关系检测不准确**：
   - 调整阈值：`config["causal_patterns_weight"] = 0.5`
   - 增加窗口：`config["causal_window_size"] = 5`
   - 启用时间顺序：优先考虑时间先后

3. **聚类结果不理想**：
   - 调整阈值：`config["clustering_threshold"] = 0.6`
   - 增加最小聚类大小：`config["min_cluster_size"] = 3`
   - 清理低质量聚类：`coherence_score < 0.3`

4. **内存使用过高**：
   - 减少缓存大小：`config["max_cache_size"] = 500`
   - 清理向量缓存：`recall_engine.clear_cache()`
   - 使用磁盘缓存：启用持久化存储

### 调试模式

```python
# 启用详细日志
import logging
logging.basicConfig(level=logging.DEBUG)

# 检索时包含解释
for result in results:
    print(f"得分: {result.total_score:.3f}, 解释: {result.explanation}")
    print(f"评分组件: {result.score_components}")
```

## 未来扩展

### 计划中的增强功能

1. **神经符号集成**：
   - 结合符号逻辑推理
   - 支持规则引擎

2. **多模态检索**：
   - 支持图像、音频向量
   - 跨模态关联

3. **个性化适应**：
   - 学习用户检索模式
   - 自适应权重调整

4. **分布式检索**：
   - 支持多节点记忆存储
   - 联邦检索机制

### 研究前沿整合

1. **脉冲神经网络**：
   - 更生物可信的时间编码
   - 事件驱动检索

2. **注意力机制**：
   - Transformer-based检索
   - 自注意力记忆选择

3. **记忆重演**：
   - 离线记忆巩固
   - 生成性重演

## 结论

本模块提供了科学依据充分、实际可行的关联检索系统，平衡了认知合理性、计算效率和用户体验。通过渐进集成策略，可以平滑替换现有检索系统，逐步启用高级功能。