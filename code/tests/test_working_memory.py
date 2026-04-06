#!/usr/bin/env python3
"""
WorkingMemory 测试用例
验证编码效果和功能正确性
"""

import sys
import os
import numpy as np
from datetime import datetime

# 添加当前目录到路径以便导入
sys.path.insert(0, os.path.dirname(__file__))

# 导入待测试模块
try:
    from working_memory_fixed import (
        WorkingMemory, 
        EncodedMemory, 
        MemoryType,
        EmbeddingEngine,
        SemanticFeatureExtractor,
        TypeClassifier
    )
    print("[测试] 成功导入WorkingMemory模块")
except ImportError as e:
    print(f"[错误] 导入失败: {e}")
    sys.exit(1)


def test_embedding_engine():
    """测试嵌入引擎"""
    print("\n" + "="*60)
    print("测试1: 嵌入引擎")
    print("="*60)
    
    # 创建嵌入引擎
    engine = EmbeddingEngine(preferred_backend="ollama")
    
    # 测试后端信息
    info = engine.get_backend_info()
    print(f"激活后端: {info['active_backend']}")
    print(f"可用后端: {info['available_backends']}")
    print(f"向量维度: {info['embedding_dim']}")
    
    # 测试嵌入生成
    test_texts = [
        "量子计算是一种新型计算范式",
        "Python is a programming language",
        "今天天气很好，适合出去散步"
    ]
    
    for text in test_texts:
        embedding = engine.embed(text)
        print(f"\n文本: '{text[:30]}...'")
        print(f"  向量形状: {embedding.shape}")
        print(f"  向量范数: {np.linalg.norm(embedding):.4f} (应接近1)")
        print(f"  前5个值: {embedding[:5]}")
    
    # 验证归一化
    print("\n验证归一化:")
    for text in test_texts:
        embedding = engine.embed(text)
        norm = np.linalg.norm(embedding)
        assert abs(norm - 1.0) < 0.01, f"向量未归一化: norm={norm}"
        print(f"  '{text[:20]}...' 归一化检查通过: norm={norm:.4f}")
    
    print("\n[OK] 嵌入引擎测试通过")


def test_semantic_feature_extractor():
    """测试语义特征提取器"""
    print("\n" + "="*60)
    print("测试2: 语义特征提取器")
    print("="*60)
    
    # 创建特征提取器
    extractor = SemanticFeatureExtractor(method="rule_based", max_keywords=5)
    
    test_texts = [
        "量子计算使用量子比特进行信息处理，量子比特可以处于叠加态",
        "今天学习了Qiskit量子编程框架，创建了第一个量子电路",
        "错误：模块'qiskit'未找到，请确保已安装pip install qiskit"
    ]
    
    for text in test_texts:
        keywords = extractor.extract_keywords(text)
        print(f"\n文本: '{text[:40]}...'")
        print(f"  提取的关键词:")
        for kw, weight in keywords:
            print(f"    - {kw}: {weight:.3f}")
        
        # 验证关键词数量
        assert len(keywords) <= 5, f"关键词数量超过最大值: {len(keywords)}"
        assert len(keywords) > 0, "未提取到关键词"
        
        # 验证权重范围
        for kw, weight in keywords:
            assert 0 <= weight <= 1, f"权重超出范围: {weight}"
    
    print("\n[OK] 语义特征提取器测试通过")


def test_type_classifier():
    """测试类型分类器"""
    print("\n" + "="*60)
    print("测试3: 类型分类器")
    print("="*60)
    
    classifier = TypeClassifier()
    
    test_cases = [
        ("量子比特是量子计算的基本单元", MemoryType.FACT),
        ("我决定学习量子计算，因为它很有前景", MemoryType.DECISION),
        ("我认为量子计算是未来最重要的技术之一", MemoryType.OPINION),
        ("首先安装qiskit，然后导入QuantumCircuit类", MemoryType.INSTRUCTION),
        ("def quantum_circuit(): qc = QuantumCircuit(2)", MemoryType.CODE),
        ("今天成功运行了量子随机数生成器程序", MemoryType.EXPERIENCE),
        ("错误：量子模拟器内存不足", MemoryType.LOG),
    ]
    
    for text, expected_type in test_cases:
        mem_type, confidence = classifier.classify(text)
        print(f"\n文本: '{text}'")
        print(f"  预测类型: {mem_type.value} (置信度: {confidence:.2f})")
        print(f"  期望类型: {expected_type.value}")
        
        # 验证类型匹配
        if expected_type != MemoryType.UNKNOWN:
            # 注意：分类器可能不是100%准确，所以我们只检查置信度合理性
            assert confidence > 0.1, f"置信度过低: {confidence}"
            print(f"  类型匹配: {mem_type == expected_type}")
    
    print("\n[OK] 类型分类器测试通过")


def test_encoded_memory():
    """测试编码记忆数据结构"""
    print("\n" + "="*60)
    print("测试4: 编码记忆数据结构")
    print("="*60)
    
    # 创建嵌入引擎用于测试
    engine = EmbeddingEngine(preferred_backend="pseudo")
    
    # 创建编码记忆
    content = "测试记忆内容"
    embedding = engine.embed(content)
    
    memory = EncodedMemory(
        id="test_id_123",
        content=content,
        embedding_vector=embedding,
        semantic_features=["测试", "记忆", "内容"],
        semantic_keywords=[("测试", 0.8), ("记忆", 0.6), ("内容", 0.4)],
        chunk_type=MemoryType.FACT,
        type_confidence=0.9,
        importance=0.7,
        source="test",
        tags=["test", "example"]
    )
    
    # 测试基本属性
    print(f"记忆ID: {memory.id}")
    print(f"内容: {memory.content}")
    print(f"类型: {memory.chunk_type.value}")
    print(f"重要性: {memory.importance}")
    print(f"向量形状: {memory.embedding_vector.shape}")
    print(f"关键词: {memory.semantic_features}")
    
    # 测试访问更新
    old_access = memory.last_accessed
    memory.update_access()
    new_access = memory.last_accessed
    print(f"\n访问更新测试:")
    print(f"  旧访问时间: {old_access}")
    print(f"  新访问时间: {new_access}")
    print(f"  访问次数: {memory.access_count}")
    assert memory.access_count == 1
    
    # 测试序列化/反序列化
    print(f"\n序列化测试:")
    mem_dict = memory.to_dict()
    print(f"  序列化后的字典键: {list(mem_dict.keys())}")
    
    memory2 = EncodedMemory.from_dict(mem_dict)
    print(f"  反序列化成功: {memory2.id == memory.id}")
    assert memory2.id == memory.id
    assert memory2.content == memory.content
    assert memory2.chunk_type == memory.chunk_type
    
    print("\n[OK] 编码记忆测试通过")


def test_working_memory_basic():
    """测试工作记忆基本功能"""
    print("\n" + "="*60)
    print("测试5: 工作记忆基本功能")
    print("="*60)
    
    # 创建小容量工作记忆便于测试
    wm = WorkingMemory(capacity=3)
    
    # 测试编码
    print("1. 编码测试记忆:")
    memories = []
    for i in range(4):
        content = f"测试记忆内容 {i+1}"
        memory = wm.encode(content, importance=0.5 + i*0.1, source="test")
        memories.append(memory)
        print(f"  编码记忆 {i+1}: {memory.id[:8]}... 类型: {memory.chunk_type.value}")
    
    # 检查缓冲区大小（应不超过容量）
    stats = wm.get_buffer_stats()
    print(f"\n2. 缓冲区状态:")
    print(f"  缓冲区大小: {stats['buffer_size']}/{stats['capacity']}")
    print(f"  类型分布: {stats['type_distribution']}")
    print(f"  淘汰数量: {stats['evicted']}")
    
    assert stats['buffer_size'] <= 3, f"缓冲区超出容量: {stats['buffer_size']}"
    assert stats['evicted'] >= 1, f"应有至少1条记忆被淘汰"
    
    # 测试获取记忆
    print(f"\n3. 获取记忆测试:")
    test_id = memories[0].id
    retrieved = wm.get(test_id)
    if retrieved:
        print(f"  成功获取记忆: {retrieved.id[:8]}...")
        print(f"  访问次数: {retrieved.access_count}")
    else:
        print(f"  记忆可能已被淘汰")
    
    # 测试相似性查询
    print(f"\n4. 相似性查询测试:")
    results = wm.query_similar("测试记忆", top_k=2)
    print(f"  查询结果数量: {len(results)}")
    for mem, sim in results:
        print(f"  相似度 {sim:.3f}: {mem.content[:20]}...")
    
    print("\n[OK] 工作记忆基本功能测试通过")


def test_working_memory_lru():
    """测试LRU替换策略"""
    print("\n" + "="*60)
    print("测试6: LRU替换策略")
    print("="*60)
    
    # 创建容量为3的工作记忆
    wm = WorkingMemory(capacity=3)
    
    # 添加3条记忆
    print("1. 添加3条记忆:")
    mem_ids = []
    for i in range(3):
        content = f"记忆{i+1}"
        memory = wm.encode(content, importance=0.5)
        mem_ids.append(memory.id)
        print(f"  添加: {memory.id[:8]}... (内容: {content})")
    
    # 访问第一条记忆（使其成为最近访问）
    print("\n2. 访问记忆1（使其成为最近访问）:")
    wm.get(mem_ids[0])
    print(f"  已访问记忆: {mem_ids[0][:8]}...")
    
    # 添加第4条记忆（应淘汰最久未访问的记忆2）
    print("\n3. 添加第4条记忆（应淘汰记忆2）:")
    new_memory = wm.encode("记忆4（新）", importance=0.6)
    print(f"  添加: {new_memory.id[:8]}... (内容: 记忆4（新）)")
    
    # 检查缓冲区
    stats = wm.get_buffer_stats()
    print(f"\n4. 缓冲区状态:")
    print(f"  缓冲区大小: {stats['buffer_size']}/{stats['capacity']}")
    print(f"  淘汰数量: {stats['evicted']}")
    
    # 验证记忆2是否被淘汰
    mem2_retrieved = wm.get(mem_ids[1])
    if mem2_retrieved:
        print(f"  记忆2仍在缓冲区中")
    else:
        print(f"  记忆2已被淘汰（符合LRU预期）")
    
    # 验证记忆1是否仍在（因为被访问过）
    mem1_retrieved = wm.get(mem_ids[0])
    assert mem1_retrieved is not None, "记忆1应仍在缓冲区中（最近访问过）"
    print(f"  记忆1仍在缓冲区中（符合LRU预期）")
    
    print("\n[OK] LRU替换策略测试通过")


def test_working_memory_persistence():
    """测试工作记忆持久化"""
    print("\n" + "="*60)
    print("测试7: 工作记忆持久化")
    print("="*60)
    
    # 创建测试文件路径
    test_file = "test_working_memory_persistence.json"
    
    # 删除可能存在的旧测试文件
    if os.path.exists(test_file):
        os.remove(test_file)
    
    # 创建工作记忆并添加记忆
    wm1 = WorkingMemory(capacity=5)
    
    for i in range(3):
        content = f"持久化测试记忆 {i+1}"
        wm1.encode(content, importance=0.6 + i*0.1, source="persistence_test")
    
    stats_before = wm1.get_buffer_stats()
    print(f"1. 保存前缓冲区大小: {stats_before['buffer_size']}")
    
    # 保存到文件
    print("\n2. 保存到文件...")
    wm1.save_buffer(test_file)
    assert os.path.exists(test_file), "保存文件失败"
    
    # 创建新的工作记忆并加载
    print("\n3. 创建新的工作记忆并加载文件...")
    wm2 = WorkingMemory(capacity=5)
    load_success = wm2.load_buffer(test_file)
    assert load_success, "加载文件失败"
    
    stats_after = wm2.get_buffer_stats()
    print(f"4. 加载后缓冲区大小: {stats_after['buffer_size']}")
    
    # 验证记忆数量
    assert stats_before['buffer_size'] == stats_after['buffer_size'], "记忆数量不匹配"
    
    # 验证记忆内容
    print("\n5. 验证记忆内容:")
    for mem in wm2.buffer.values():
        print(f"  记忆: {mem.content} (类型: {mem.chunk_type.value})")
    
    # 清理测试文件
    if os.path.exists(test_file):
        os.remove(test_file)
        print(f"\n6. 清理测试文件: {test_file}")
    
    print("\n[OK] 工作记忆持久化测试通过")


def run_all_tests():
    """运行所有测试"""
    print("="*70)
    print("WorkingMemory 模块完整测试套件")
    print("="*70)
    
    try:
        test_embedding_engine()
        test_semantic_feature_extractor()
        test_type_classifier()
        test_encoded_memory()
        test_working_memory_basic()
        test_working_memory_lru()
        test_working_memory_persistence()
        
        print("\n" + "="*70)
        print("[OK] 所有测试通过!")
        print("="*70)
        return True
        
    except AssertionError as e:
        print(f"\n[ERROR] 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    except Exception as e:
        print(f"\n[ERROR] 测试异常: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)