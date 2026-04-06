#!/usr/bin/env python3
"""
测试Faiss向量索引集成到长期存储模块
"""

import sys
import os
import tempfile
import numpy as np
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_faiss_availability():
    """测试Faiss库是否可用"""
    try:
        import faiss
        print("[OK] Faiss 导入成功")
        print(f"   Faiss版本: {faiss.__version__ if hasattr(faiss, '__version__') else '未知'}")
        
        # 创建一个简单的Faiss索引
        dimension = 768
        index = faiss.IndexFlatL2(dimension)
        print(f"   Faiss索引创建成功，维度: {dimension}")
        
        # 测试添加向量
        vectors = np.random.rand(10, dimension).astype('float32')
        index.add(vectors)
        print(f"   成功添加 {vectors.shape[0]} 个向量")
        
        # 测试搜索
        query_vector = np.random.rand(1, dimension).astype('float32')
        distances, indices = index.search(query_vector, k=3)
        print(f"   最近邻搜索成功，返回 {len(indices[0])} 个结果")
        
        return True
    except ImportError as e:
        print(f"[ERROR] Faiss导入失败: {e}")
        return False
    except Exception as e:
        print(f"[ERROR] Faiss测试异常: {e}")
        return False

def test_long_term_storage_faiss():
    """测试长期存储模块的Faiss集成"""
    try:
        from long_term_storage import LongTermStorage
        
        # 创建临时目录
        temp_dir = tempfile.mkdtemp(prefix="faiss_test_")
        print(f"\n[INFO] 使用临时目录: {temp_dir}")
        
        # 初始化长期存储
        storage = LongTermStorage(
            storage_dir=temp_dir,
            embedding_dim=384,  # 测试使用较小维度
            enable_archive=False,
            enable_compression=False
        )
        
        print("[OK] 长期存储初始化成功")
        
        # 检查向量索引类型
        if hasattr(storage, 'vector_manager'):
            vector_manager = storage.vector_manager
            print(f"   向量索引类型: {getattr(vector_manager, 'index_type', '未知')}")
            print(f"   Faiss可用状态: {getattr(vector_manager, 'faiss_available', '未知')}")
        else:
            print("   注意: 未找到vector_manager属性")
        
        # 创建测试记忆
        test_memory = {
            "id": "test_001",
            "fact": "测试记忆",
            "content": "这是一个用于测试Faiss集成的记忆项",
            "vec": np.random.rand(384).tolist(),  # 384维向量
            "importance": 0.7,
            "type": "test",
            "timestamp": "2026-03-28T12:00:00",
            "confidence": 0.8,
            "source_count": 1,
            "metadata": {
                "emotion": "neutral",
                "keywords": ["测试", "Faiss"],
                "language": "zh"
            }
        }
        
        # 存储记忆
        print("\n[INFO] 存储测试记忆...")
        stored_id = storage.store_memory(
            memory_obj=test_memory,
            vector=test_memory["vec"]
        )
        
        if stored_id:
            print(f"   记忆存储成功，ID: {stored_id}")
        else:
            print("   记忆存储失败")
            
        # 测试相似性搜索
        print("\n[INFO] 测试相似性搜索...")
        query_vector = np.random.rand(384).astype('float32')
        results = storage.search_by_vector(query_vector, top_k=3)
        
        if results:
            print(f"   搜索返回 {len(results)} 个结果")
            for i, (score, memory_id) in enumerate(results):
                print(f"     {i+1}. ID: {memory_id}, 分数: {score:.4f}")
        else:
            print("   搜索无结果")
            
        # 获取统计信息
        stats = storage.get_stats()
        print(f"\n存储统计:")
        print(f"   记忆数量: {stats.get('memory_count', 0)}")
        print(f"   向量索引大小: {stats.get('vector_index_size', 0)}")
        
        # 清理
        import shutil
        shutil.rmtree(temp_dir)
        print(f"\n清理临时目录: {temp_dir}")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] 长期存储测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_faiss_in_biological_memory_engine():
    """测试生物学记忆引擎中的Faiss集成"""
    try:
        from biological_memory_engine import BiologicalMemoryEngine
        
        config = {
            "system_name": "Faiss测试引擎",
            "module_configs": {
                "long_term_storage": {
                    "storage_path": "./test_faiss_storage",
                    "enable_compression": False,
                    "enable_faiss": True  # 如果支持此选项
                }
            }
        }
        
        print("\n[INFO] 测试生物学记忆引擎...")
        engine = BiologicalMemoryEngine(config)
        
        # 检查存储模块是否使用Faiss
        if "long_term_storage" in engine.modules:
            storage_module = engine.modules["long_term_storage"]
            print(f"   长期存储模块加载: {storage_module}")
            
            # 尝试获取状态
            result = storage_module.get_stats()
            if result.success:
                stats = result.metadata
                print(f"   存储模块统计: {stats}")
                
                # 检查是否有向量索引信息
                if "vector_index" in stats:
                    print(f"   向量索引: {stats['vector_index']}")
        else:
            print("   警告: 未找到长期存储模块")
            
        # 清理
        import shutil
        if os.path.exists("./test_faiss_storage"):
            shutil.rmtree("./test_faiss_storage")
            print("\n清理测试存储目录")
            
        return True
        
    except Exception as e:
        print(f"[ERROR] 生物学记忆引擎测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    print("=" * 70)
    print("Faiss向量索引集成测试")
    print("=" * 70)
    
    # 测试1: Faiss库可用性
    print("\n1. 测试Faiss库可用性")
    faiss_available = test_faiss_availability()
    
    # 测试2: 长期存储模块集成
    print("\n2. 测试长期存储模块的Faiss集成")
    if faiss_available:
        storage_test = test_long_term_storage_faiss()
    else:
        print("   [SKIP] Faiss不可用，跳过存储测试")
        storage_test = False
    
    # 测试3: 生物学记忆引擎集成
    print("\n3. 测试生物学记忆引擎中的Faiss集成")
    if faiss_available:
        engine_test = test_faiss_in_biological_memory_engine()
    else:
        print("   [SKIP] Faiss不可用，跳过引擎测试")
        engine_test = False
    
    print("\n" + "=" * 70)
    print("测试总结:")
    print(f"   Faiss库可用: {'[OK]' if faiss_available else '[FAIL]'}")
    print(f"   长期存储集成: {'[OK]' if storage_test else '[FAIL]'}")
    print(f"   生物学引擎集成: {'[OK]' if engine_test else '[FAIL]'}")
    print("=" * 70)
    
    if faiss_available and storage_test and engine_test:
        print("\n[SUCCESS] Faiss集成测试全部通过!")
    else:
        print("\n[WARNING] 部分测试未通过，可能需要进一步集成")

if __name__ == "__main__":
    main()