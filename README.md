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

