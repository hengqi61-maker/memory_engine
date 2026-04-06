# 情绪属性与价值评估模块设计

## 1. 理论基础

### 1.1 PAD模型 (Mehrabian & Russell, 1974)
PAD模型是三维情绪空间模型：
- **愉悦度 (Pleasure)**: 情绪的正负向，-1(不愉快)到+1(愉快)
- **唤醒度 (Arousal)**: 情绪的生理激活程度，-1(平静)到+1(兴奋)
- **支配度 (Dominance)**: 对情境的控制感，-1(受控)到+1(支配)

### 1.2 环状模型 (Valence-Arousal, Russell)
二维情绪空间：
- **效价 (Valence)**: 类似愉悦度，负到正
- **唤醒度 (Arousal)**: 低到高
与PAD的关系：Valence ≈ Pleasure, Arousal相同，支配度为附加维度。

### 1.3 情绪增强记忆效应 (Emotional Enhancement of Memory)
- 高唤醒度情绪增强记忆编码和巩固
- 情绪显著性影响记忆优先级
- 个人相关性调节情绪强度对记忆的影响

## 2. 多维情绪评估体系

### 2.1 基础情绪维度 (PAD)
1. **愉悦度 (pleasure)**: [-1, 1]
2. **唤醒度 (arousal)**: [-1, 1]
3. **支配度 (dominance)**: [-1, 1]

### 2.2 扩展重要性维度
4. **个人相关性 (personal_relevance)**: [0, 1]，信息与个人目标、身份、兴趣的相关程度
5. **任务效用 (task_utility)**: [0, 1]，对当前或未来任务的帮助程度
6. **社会价值 (social_value)**: [0, 1]，社交、道德、文化价值
7. **新颖性 (novelty)**: [0, 1]，信息的新颖程度
8. **复杂性 (complexity)**: [0, 1]，信息的复杂程度（过高可能降低记忆效率）

### 2.3 记忆类型分类
- **fact**: 事实性信息
- **decision**: 决策过程或选择
- **opinion**: 观点或评价
- **instruction**: 指令或步骤
- **experience**: 个人经历
- **relationship**: 关系或连接

## 3. 量化方案

### 3.1 情绪分析
- **轻量级方法**: TextBlob（情感极性） + VADER（情绪强度）
- **小型模型**: 微调BERT-like模型用于PAD维度预测
- **关键词匹配**: 情绪词典映射

### 3.2 重要性评分公式
```
emotional_intensity = sqrt(pleasure² + arousal² + dominance²) / sqrt(3)  # 归一化到[0,1]
weight_sum = w_rel + w_task + w_soc + w_nov + w_com
extended_score = (personal_relevance*w_rel + task_utility*w_task + social_value*w_soc + novelty*w_nov - complexity*w_com) / weight_sum

significance_score = α * emotional_intensity + β * extended_score + γ * context_factor
```
其中权重可配置，默认：w_rel=0.3, w_task=0.25, w_soc=0.2, w_nov=0.15, w_com=0.1
α=0.4, β=0.5, γ=0.1 (可调节)

### 3.3 上下文感知修正
- **对话历史**: 考虑近期话题相关性
- **用户状态**: 当前任务、情绪状态
- **环境因素**: 时间、地点、社交环境
- **记忆类型**: 不同类型记忆的权重差异

## 4. 系统架构

### 4.1 模块接口
输入: RawMemoryChunk (原始文本、元数据、时间戳、来源)
输出: AppraisedMemory (情绪维度、重要性评分、记忆类型、置信度)

### 4.2 处理流程
1. **文本预处理**: 清洗、分词、句法分析
2. **情绪分析**: 计算PAD维度和情绪强度
3. **重要性评估**: 计算扩展维度得分
4. **上下文修正**: 结合会话上下文调整评分
5. **记忆分类**: 确定记忆类型
6. **置信度估计**: 评估分析结果的可靠性

### 4.3 与上下游集成
- **上游 SensoryInput**: 接收原始记忆片段
- **下游 WorkingMemory**: 输出评估后的记忆，供后续压缩、存储、检索使用

## 5. 实现计划

### 5.1 依赖库
- textblob (情感分析)
- vaderSentiment (情绪强度)
- transformers (可选，用于微调模型)
- numpy, scipy

### 5.2 文件结构
```
emotional_appraisal/
├── __init__.py
├── emotion_analyzer.py     # 情绪分析核心
├── significance_scorer.py  # 重要性评分
├── context_awareness.py    # 上下文感知
├── memory_classifier.py    # 记忆分类
├── config.yaml             # 权重配置
└── tests/
    ├── test_analyzer.py
    └── test_integration.py
```

### 5.3 集成步骤
1. 替换现有 `_evaluate_signal` 方法
2. 添加情绪维度到记忆数据结构
3. 更新睡眠周期中的筛选逻辑，考虑情绪重要性
4. 扩展检索功能，支持情绪维度查询

## 6. 测试方案

### 6.1 单元测试
- 情绪分析精度测试
- 评分公式一致性测试
- 分类准确性测试

### 6.2 集成测试
- 端到端记忆处理流程
- 与现有记忆引擎的兼容性

### 6.3 评估指标
- 情绪标注一致性 (与人工标注对比)
- 记忆留存预测准确性
- 系统性能 (处理速度、内存占用)