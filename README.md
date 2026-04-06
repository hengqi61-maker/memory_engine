# Memory Engine

## Overview

This project implements a modular memory system with short-term processing, emotional appraisal, long-term consolidation, and semantic recall association.

Primary storage path:

`C:\Users\Lenovo\.openclaw\workspace\memory_engine\memory_storage\`

Each memory item is stored as a UUID-named JSON document. Typical fields include:

- `id`
- `content`
- `content_type`
- `timestamp`
- `status`
- `embedding` (768 dimensions)

## Project Structure

```text
memory_engine/
├── code/
│   └── modules/
│       ├── emotional_appraisal.py
│       ├── enhanced_working_memory.py
│       ├── long_term_storage.py
│       ├── recall_association.py
│       ├── biological_memory_engine.py
│       ├── openclaw_memory_engine_fixed.py
│       └── working_memory.py
├── memory_storage/
├── compatibility_storage/
├── design/
├── example_storage/
├── legacy_archive/
├── literature/
├── summary/
├── redesign_plan.md
├── test_enhanced_memory.py
├── quick_test.py
├── test_emotion.py
└── replace_all_unicode.py
```
memory_engine/
├── 📁 code/                       # 核心代码实现
│   └── 📁 modules/                # 模块化组件
│       ├── emotional_appraisal.py           # 情感评估
│       ├── enhanced_working_memory.py       # 增强工作记忆
│       ├── long_term_storage.py             # 长期存储
│       ├── recall_association.py            # 回忆关联
│       ├── biological_memory_engine.py      # 生物记忆引擎
│       ├── openclaw_memory_engine_fixed.py  # 主引擎
│       └── working_memory.py                # 基础工作记忆
├── 📁 memory_storage/             # 主存储目录
│   ├── 📄 {uuid1}.json            # 个人记忆文件
│   ├── 📄 {uuid2}.json            # 单个记忆项
│   └── ...                        # 其余24+个记忆文件
├── 📁 compatibility_storage/      # 兼容性存储
│   └── (旧版本格式备份)
├── 📁 design/                     # 设计文档
│   └── (架构图、流程图等)
├── 📁 example_storage/            # 示例数据
│   └── (演示用的样例记忆)
├── 📁 legacy_archive/             # 遗留归档
│   └── (废弃代码、历史版本)
├── 📁 literature/                 # 研究文献
│   └── (认知科学、心理学参考文献)
├── 📁 summary/                    # 记忆摘要
│   └── (总结性分析报告)
├── 📄 redesign_plan.md            # 三层模型设计方案
├── 📄 test_enhanced_memory.py     # 增强系统测试
├── 📄 quick_test.py               # 快速测试脚本
├── 📄 test_emotion.py             # 情感模块测试
└── 📄 replace_all_unicode.py      # 编码处理工具

## Memory Lifecycle

1. Input enters short-lived sensory/working memory.
2. Working memory performs encoding and classification.
3. Emotional appraisal enriches memory with PAD-like signals and importance.
4. Consolidation determines long-term retention.
5. Long-term storage persists data to JSON and vector index.
6. Recall combines vector retrieval and semantic association.

## Storage Configuration

`long_term_storage.py` contains configurable options such as:

- `embedding_dim`: 768
- `archive_enabled`: true
- `archive_dir`: archived/
- `compression`: false
- `vector_index_type`: faiss

## Notes

- `memory_storage/` is the main persistence directory.
- `compatibility_storage/` is intended for legacy format compatibility.
- `legacy_archive/` stores deprecated or historical artifacts.

