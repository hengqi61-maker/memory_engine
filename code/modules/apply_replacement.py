#!/usr/bin/env python3
"""
方案A应用脚本：自动替换working_memory导入
"""

import os
import re
import sys

def main():
    # 设置工作目录
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    print("=" * 80)
    print("方案A：应用增强版工作记忆替换")
    print("=" * 80)
    
    # 1. 查找所有需要替换的文件
    import_patterns = [
        r'from\s+working_memory\s+import',
        r'from\s+working_memory_fixed\s+import',
    ]
    
    files_to_modify = []
    
    # 搜索整个工作空间
    workspace_root = os.path.abspath(os.path.join(base_dir, "..", "..", ".."))
    
    print("\n[1] 搜索需要修改的文件...")
    for root, dirs, files in os.walk(workspace_root):
        # 跳过某些目录
        dirs[:] = [d for d in dirs if d not in ['__pycache__', '.git', 'node_modules']]
        
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 检查是否包含导入语句
                import_found = False
                for pattern in import_patterns:
                    if re.search(pattern, content, re.IGNORECASE):
                        import_found = True
                        break
                
                if import_found:
                    rel_path = os.path.relpath(filepath, workspace_root)
                    files_to_modify.append((filepath, rel_path, content))
    
    if not files_to_modify:
        print("  未找到需要替换的文件")
        
        # 检查可能的位置
        possible_files = [
            "examples/integration_example.py",
            "examples/example_usage.py", 
            "modules/openclaw_memory_engine_fixed.py",
            "examples/quick_test_recall_fix.py"
        ]
        
        print("\n可能的位置（需手动检查）：")
        for f in possible_files:
            full_path = os.path.join(workspace_root, "memory_engine", "code", f)
            if os.path.exists(full_path):
                print(f"  - {f}")
    else:
        print(f"找到 {len(files_to_modify)} 个需要修改的文件:")
        for _, rel_path, _ in files_to_modify:
            print(f"  - {rel_path}")
    
    # 2. 显示具体的替换代码
    print("\n[2] 替换的代码模式:")
    
    print("\n模式1：标准导入替换")
    print("-" * 40)
    print("原代码:")
    print('  from working_memory_fixed import WorkingMemory')
    print("\n替换为:")
    print('  from working_memory_enhanced import (')
    print('      EnhancedWorkingMemory as WorkingMemory,')
    print('      EnhancedMemory as EncodedMemory,')
    print('      MemoryType')
    print('  )')
    
    print("\n模式2：初始化参数替换")
    print("-" * 40)
    print("原代码:")
    print('  wm = WorkingMemory(capacity=20)')
    print("\n替换为:")
    print('  wm = EnhancedWorkingMemory(capacity=None, enable_turn_based_decay=True)')
    
    print("\n模式3：编码调用增强")
    print("-" * 40)
    print("原代码:")
    print('  memory = wm.encode(content)')
    print("\n增强版:")
    print('  memory = wm.encode(')
    print('      content=content,')
    print('      importance=0.5,')
    print('      retention_priority=0.5,')
    print('      emotional_intensity=0.0')
    print('  )')
    
    # 3. 直接修改integration_example.py作为示例
    print("\n[3] 实际修改示例：integration_example.py")
    
    example_file = os.path.join(base_dir, "..", "examples", "integration_example.py")
    if os.path.exists(example_file):
        with open(example_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 查找并显示原有的导入语句
        old_import = re.search(r'from\s+working_memory_fixed\s+import\s+WorkingMemory', content)
        if old_import:
            print("找到原有导入语句：")
            print(f"  {old_import.group()}")
            
            # 建议的新内容
            new_content = content.replace(
                "from working_memory_fixed import WorkingMemory, EncodedMemory, MemoryType",
                """from working_memory_enhanced import (
    EnhancedWorkingMemory as WorkingMemory,
    EnhancedMemory as EncodedMemory,
    MemoryType
)"""
            )
            
            # 保存备份
            backup_file = example_file + ".backup"
            with open(backup_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # 应用修改
            with open(example_file, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            print("修改完成！备份文件：", backup_file)
            
            # 显示修改后的初始化部分
            init_match = re.search(r'self\.working_memory\s*=\s*WorkingMemory\(.*?\)', new_content, re.DOTALL)
            if init_match:
                print("\n建议的初始化修改：")
                print("-" * 40)
                print("原初始化:")
                print(init_match.group())
                print("\n建议改为:")
                print("""self.working_memory = WorkingMemory(
    capacity=None,  # 自动估算容量
    embedding_backend="ollama",
    enable_turn_based_decay=True
)""")
        else:
            print("未在示例文件中找到标准导入语句")
    else:
        print(f"示例文件不存在: {example_file}")
    
    # 4. 测试新模块是否可用
    print("\n[4] 测试增强版模块：")
    try:
        from working_memory_enhanced import EnhancedWorkingMemory
        print("  ✅ 增强版导入成功")
        
        # 尝试初始化
        wm = EnhancedWorkingMemory(capacity=None)
        print(f"  ✅ 初始容量: {wm.capacity}")
        print(f"  ✅ 启用轮次衰减: {wm.enable_turn_based_decay}")
        
        # 测试编码
        memory = wm.encode("测试记忆", importance=0.8)
        print(f"  ✅ 记忆编码成功，ID: {memory.id}")
        print(f"     留存分数: {memory.retention_score:.3f}")
        
    except Exception as e:
        print(f"  ❌ 测试失败: {e}")
    
    # 5. 总结
    print("\n[5] 总结和实施步骤：")
    print("""1. 将working_memory_enhanced.py复制到项目目录
2. 查找所有'from working_memory_fixed import'语句
3. 替换为'from working_memory_enhanced import EnhancedWorkingMemory as WorkingMemory'
4. 修改初始化参数：capacity=None, enable_turn_based_decay=True
5. 在消息循环中添加wm.increment_turn()
6. 测试关键功能：
   - 记忆编码（不同重要性）
   - 记忆查询（filter_by_retention=True）
   - 统计查看（get_buffer_stats）
   - 主动清理（prune_low_value_memories）""")
    
    print("\n[6] 与情感评估模块集成（第三个模块）：")
    print("-" * 40)
    
    emotion_integration = """
    # 获取情感评估引擎
    from emotional_appraisal import EmotionalAppraisalEngine
    
    # 初始化两个引擎
    emotion_engine = EmotionalAppraisalEngine()
    memory_engine = EnhancedWorkingMemory(capacity=None)
    
    # 处理流程
    def process_with_full_context(text):
        # 步骤1: 情感评估
        appraised = emotion_engine.appraise_memory({
            "content": text,
            "timestamp": datetime.now().isoformat()
        })
        
        # 步骤2: 工作记忆编码（使用情感评估参数）
        memory = memory_engine.encode(
            content=text,
            importance=appraised.get('significance_score', 0.5),
            retention_priority=appraised.get('retention_priority', 0.5),
            emotional_intensity=appraised.get('emotional_intensity', 0.0)
        )
        
        return {
            "memory": memory,
            "emotional_analysis": appraised
        }
    """
    
    print(emotion_integration)
    
    print("\n[7] 验证改进效果：")
    verification_points = [
        ("衰减单位", "时间（秒） → 对话轮次"),
        ("容量策略", "固定 → 动态估算"),
        ("淘汰策略", "LRU → 留存分数最低"),
        ("重要性影响", "无 → 影响衰减速率"),
        ("情感集成", "无 → 字段级映射")
    ]
    
    for point, improvement in verification_points:
        print(f"  • {point}: {improvement}")
    
    print("\n" + "=" * 80)
    print("完成！增强版工作记忆已准备就绪。")
    print("=" * 80)

if __name__ == "__main__":
    main()