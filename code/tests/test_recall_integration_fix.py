#!/usr/bin/env python3
"""
测试关联检索模块集成修复
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """测试模块导入"""
    print("=" * 70)
    print("测试关联检索模块导入")
    print("=" * 70)
    
    try:
        from recall_association import RecallAssociation, RetrievalQuery
        print("[OK] recall_association 模块导入成功")
        
        # 测试创建实例
        recaller = RecallAssociation(config={"time_decay_alpha": 0.01})
        print("[OK] RecallAssociation 实例创建成功")
        
        # 测试 RetrievalQuery
        query = RetrievalQuery(query_text="测试", max_results=5)
        print("[OK] RetrievalQuery 创建成功")
        
        return recaller, query
    except Exception as e:
        print(f"[ERROR] 导入失败: {e}")
        import traceback
        traceback.print_exc()
        return None, None

def test_recall_association_methods(recaller):
    """测试 RecallAssociation 方法"""
    print("\n" + "="*70)
    print("测试 RecallAssociation 方法")
    print("="*70)
    
    if not recaller:
        return False
    
    try:
        # 检查是否增加了 retrieve 方法（可能需要）
        methods = [method for method in dir(recaller) if not method.startswith('_')]
        print(f"可用方法: {', '.join(methods[:10])}...")
        
        # 检查是否有 retrieve_hybrid
        if hasattr(recaller, 'retrieve_hybrid'):
            print("[OK] retrieve_hybrid 方法存在")
        else:
            print("[WARNING] retrieve_hybrid 方法不存在")
            
        # 检查是否有 retrieve（可能不存在）
        if hasattr(recaller, 'retrieve'):
            print("[OK] retrieve 方法存在")
        else:
            print("[INFO] retrieve 方法不存在（可能需要添加）")
            
        return True
    except Exception as e:
        print(f"[ERROR] 测试方法失败: {e}")
        return False

def test_biological_memory_engine_integration():
    """测试生物学记忆引擎集成"""
    print("\n" + "="*70)
    print("测试生物学记忆引擎集成")
    print("="*70)
    
    try:
        from biological_memory_engine import BiologicalMemoryEngine, MemoryQuery
        
        # 最小配置
        config = {
            "system_name": "RecallFixTest",
            "module_configs": {
                "working_memory": {"capacity": 3},
                "long_term_storage": {"storage_path": "./test_recall_fix_storage"},
                "recall_association": {
                    "enabled": True,
                    "default_weights": {
                        "semantic": 0.4,
                        "temporal": 0.3,
                        "causal": 0.2,
                        "emotional": 0.1
                    }
                }
            },
            "pipeline": ["sensory_registration", "working_memory", "long_term_storage", "recall_association"]
        }
        
        print("[INFO] 创建生物学记忆引擎...")
        engine = BiologicalMemoryEngine(config)
        print("[OK] 引擎创建成功")
        
        # 检查引擎模块
        print("[INFO] 检查加载的模块...")
        # 注意：引擎可能没有直接的 modules 属性，但我们可以尝试其他方式
        
        # 测试创建 MemoryQuery
        query = MemoryQuery(
            query_text="测试检索",
            max_results=5,
            min_importance=0.1
        )
        print("[OK] MemoryQuery 创建成功")
        
        # 注意：这里不能直接测试检索，因为需要存储的记忆
        # 但我们可以测试模块初始化
        
        return True
        
    except Exception as e:
        print(f"[ERROR] 集成测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def add_retrieve_method_to_recall_association():
    """在 RecallAssociation 类中添加 retrieve 方法（兼容性）"""
    print("\n" + "="*70)
    print("在 RecallAssociation 中添加 retrieve 方法")
    print("="*70)
    
    try:
        # 读取 recall_association.py 文件
        with open("recall_association.py", "r", encoding="utf-8") as f:
            content = f.read()
        
        # 检查是否已有 retrieve 方法
        if "def retrieve(" in content:
            print("[INFO] retrieve 方法已存在")
            return False
        
        # 查找 retrieve_hybrid 方法定义
        hybrid_pos = content.find("def retrieve_hybrid(")
        if hybrid_pos == -1:
            print("[ERROR] 找不到 retrieve_hybrid 方法")
            return False
        
        # 查找 retrieve_hybrid 方法的结束位置（通过缩进）
        lines = content.split('\n')
        hybrid_line = -1
        for i, line in enumerate(lines):
            if "def retrieve_hybrid(" in line:
                hybrid_line = i
                break
        
        if hybrid_line == -1:
            print("[ERROR] 找不到 retrieve_hybrid 方法行")
            return False
        
        # 找到下一个 def 方法开始
        method_start = -1
        for i in range(hybrid_line + 1, len(lines)):
            if lines[i].strip().startswith("def ") and not lines[i].strip().startswith("def _"):
                method_start = i
                break
        
        # 如果没有找到其他方法，则添加到文件末尾
        if method_start == -1:
            method_start = len(lines)
        
        # 构建 retrieve 方法
        retrieve_method = '''
    def retrieve(self, query_text: str, top_k: int = 10, query_type: Optional[str] = None):
        """
        简化检索接口（兼容性方法）
        
        Args:
            query_text: 查询文本
            top_k: 返回结果数量
            query_type: 记忆类型过滤
            
        Returns:
            检索结果列表（兼容格式）
        """
        try:
            from recall_association import RetrievalQuery
            query = RetrievalQuery(
                query_text=query_text,
                query_type=query_type,
                max_results=top_k,
                weights=self.config.get("default_weights", {
                    "semantic": 0.4,
                    "temporal": 0.3,
                    "causal": 0.2,
                    "emotional": 0.1
                }),
                time_decay_alpha=self.config.get("time_decay_alpha", 0.01)
            )
            
            results = self.retrieve_hybrid(query)
            
            # 转换为简化格式（列表 of tuples: (content, score)）
            simplified = []
            for result in results[:top_k]:
                simplified.append({
                    "content": result.memory.content,
                    "score": result.total_score,
                    "memory": result.memory
                })
            
            return simplified
            
        except Exception as e:
            import logging
            logging.warning(f"retrieve 方法执行失败: {e}")
            return []'''
        
        # 插入新方法
        lines.insert(method_start, retrieve_method)
        
        # 写回文件
        with open("recall_association.py", "w", encoding="utf-8") as f:
            f.write('\n'.join(lines))
        
        print("[OK] 成功添加 retrieve 方法")
        return True
        
    except Exception as e:
        print(f"[ERROR] 添加方法失败: {e}")
        return False

def main():
    """主测试函数"""
    print("关联检索模块集成修复测试")
    print("=" * 70)
    
    # 1. 测试基本导入
    recaller, query = test_imports()
    
    # 2. 测试方法存在性
    if recaller:
        test_recall_association_methods(recaller)
    
    # 3. 如果需要，添加 retrieve 方法
    # add_retrieve_method_to_recall_association()
    
    # 4. 测试引擎集成
    test_biological_memory_engine_integration()
    
    # 清理临时目录
    import shutil
    if os.path.exists("./test_recall_fix_storage"):
        shutil.rmtree("./test_recall_fix_storage")
        print("\n清理临时存储目录")
    
    print("\n" + "=" * 70)
    print("测试完成")
    print("=" * 70)

if __name__ == "__main__":
    main()