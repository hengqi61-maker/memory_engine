#!/usr/bin/env python3
"""
方案A实施指南：简单直接替换
使用方法：
1. 复制此文件到你的项目目录
2. 执行：python simple_replacement_guide.py
3. 它将显示需要修改的文件和位置
"""

import os
import sys
import re

class ReplacementGuide:
    def __init__(self):
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
    
    def find_import_statements(self):
        """在所有Python文件中查找working_memory导入语句"""
        import_patterns = [
            r'from\s+working_memory\s+import',
            r'from\s+working_memory_fixed\s+import',
            r'import\s+working_memory',
            r'import\s+working_memory_fixed'
        ]
        
        results = {}
        for root, dirs, files in os.walk(self.base_dir):
            for file in files:
                if not file.endswith('.py'):
                    continue
                
                filepath = os.path.join(root, file)
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                for pattern in import_patterns:
                    matches = re.findall(pattern, content, re.IGNORECASE)
                    if matches:
                        rel_path = os.path.relpath(filepath, self.base_dir)
                        if rel_path not in results:
                            results[rel_path] = []
                        results[rel_path].extend(matches)
        
        return results
    
    def generate_replacement_snippets(self):
        """生成替换代码片段"""
        snippets = {
            # 示例1：简单导入替换
            "basic_import": """
# 原代码：
# from working_memory_fixed import WorkingMemory, EncodedMemory, MemoryType

# 替换为：
from working_memory_enhanced import (
    EnhancedWorkingMemory as WorkingMemory,
    EnhancedMemory as EncodedMemory,
    MemoryType
)
""",
            
            # 示例2：初始化替换
            "init_replacement": """
# 原代码：
# self.working_memory = WorkingMemory(
#     capacity=20,
#     embedding_backend="ollama"
# )

# 替换为：
self.working_memory = EnhancedWorkingMemory(
    capacity=None,  # None表示自动估算容量
    embedding_backend="ollama",
    enable_turn_based_decay=True
)
""",
            
            # 示例3：编码调用增强
            "encode_enhancement": """
# 原代码（可能缺少重要性参数）：
# encoded = self.working_memory.encode(content)

# 增强版（添加重要性、留存优先级等）：
encoded = self.working_memory.encode(
    content=content,
    importance=0.5,  # 重要性（0-1）
    retention_priority=0.5,  # 从情感评估模块获取
    source="user",  # 来源
    tags=["conversation"],  # 标签
    emotional_intensity=0.3  # 情绪强度
)
""",
            
            # 示例4：添加对话轮次跟踪
            "turn_tracking": """
# 在适当的地方添加对话轮次跟踪：

# 1. 在消息处理函数中：
def process_message(self, message):
    # 原有处理逻辑...
    
    # 增加工作记忆对话轮次
    if hasattr(self, 'working_memory') and self.working_memory:
        self.working_memory.increment_turn()
        print(f"对话轮次: {self.working_memory.total_turns}")
    
    # 继续处理...
""",
            
            # 示例5：定期清理低价值记忆
            "pruning_strategy": """
# 定期调用清理函数：
def periodic_maintenance(self):
    # 定期触发主动清理
    if hasattr(self, 'working_memory') and self.working_memory:
        before = len(self.working_memory.buffer)
        self.working_memory.prune_low_value_memories(threshold=0.1)
        after = len(self.working_memory.buffer)
        print(f"[清理] 移除了 {before - after} 条低价值记忆")
    
    # 查看统计信息
    stats = self.working_memory.get_buffer_stats()
    print(f"当前平均留存分数: {stats['average_retention_score']:.3f}")
"""
        }
        
        return snippets
    
    def check_compatibility(self):
        """检查兼容性问题"""
        issues = []
        
        # 检查必要的增强版文件
        enhanced_file = os.path.join(self.base_dir, "working_memory_enhanced.py")
        if not os.path.exists(enhanced_file):
            issues.append("缺少文件: working_memory_enhanced.py")
        
        # 检查可选依赖
        try:
            import ollama
            issues.append("✅ Ollama可用")
        except ImportError:
            issues.append("⚠️ Ollama不可用，将使用伪嵌入（功能受限）")
        
        try:
            import numpy as np
            issues.append("✅ NumPy可用")
        except ImportError:
            issues.append("❌ 缺少NumPy，必需依赖")
        
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            issues.append("✅ Scikit-learn可用")
        except ImportError:
            issues.append("⚠️ Scikit-learn不可用，部分功能降级")
        
        return issues
    
    def create_backup_instructions(self):
        """创建备份说明"""
        instructions = [
            "## 备份建议：",
            "1. 备份原有working_memory.py和working_memory_fixed.py",
            "2. 创建测试分支：git checkout -b enhanced-memory",
            "3. 运行测试套件验证兼容性",
            "",
            "## 回滚步骤：",
            "1. 恢复原import语句",
            "2. 删除working_memory_enhanced.py",
            "3. 恢复原有初始化参数",
            ""
        ]
        
        return "\n".join(instructions)

def main():
    guide = ReplacementGuide()
    
    print("=" * 80)
    print("方案A：直接替换实施指南")
    print("=" * 80)
    
    print("\n1️⃣ 查找需要修改的导入语句：")
    imports = guide.find_import_statements()
    
    if imports:
        for file, patterns in imports.items():
            print(f"   📄 {file}")
            for pattern in patterns:
                print(f"      • {pattern}")
    else:
        print("   未找到working_memory相关导入")
    
    print("\n2️⃣ 生成替换代码片段：")
    snippets = guide.generate_replacement_snippets()
    
    for key, snippet in snippets.items():
        print(f"\n【{key}】")
        print(snippet)
    
    print("\n3️⃣ 兼容性检查：")
    issues = guide.check_compatibility()
    for issue in issues:
        print(f"   {issue}")
    
    print("\n4️⃣ 具体实施步骤：")
    steps = [
        "STEP 1: 复制working_memory_enhanced.py到项目目录",
        "STEP 2: 修改所有导入语句（见上方列表）",
        "STEP 3: 修改WorkingMemory初始化（capacity=None启用自动估算）",
        "STEP 4: 添加`wm.encode()`的增强参数（importance, retention_priority等）",
        "STEP 5: 在消息循环中添加`working_memory.increment_turn()`",
        "STEP 6: 可选：添加定期清理`wm.prune_low_value_memories()`",
        "STEP 7: 运行测试验证功能正常"
    ]
    
    for i, step in enumerate(steps, 1):
        print(f"   {i}. {step}")
    
    print("\n5️⃣ 核心参数配置建议：")
    config_suggestions = {
        "capacity": "None（自动估算）或具体数字。建议用None让AI自动决定",
        "enable_turn_based_decay": "True（启用对话轮次基础衰减）",
        "base_decay_lambda": "0.1（每轮次基础衰减率）",
        "retention_threshold": "0.1（留存分数淘汰阈值）",
        "embedding_backend": "'ollama'（如果可用）或'pseudo'（降级）"
    }
    
    for param, desc in config_suggestions.items():
        print(f"   • {param}: {desc}")
    
    print("\n6️⃣ 与情感评估模块集成：")
    print("   " + "-" * 40)
    emotion_integration = """
    # 获取情感评估结果后
    appraised = emotion_engine.appraise_memory(content)
    
    # 编码到工作记忆（使用情感评估参数）
    memory = wm.encode(
        content=content,
        importance=appraised.significance_score,
        retention_priority=appraised.retention_priority,
        emotional_intensity=appraised.emotional_intensity
    )
    """
    print(emotion_integration.strip())
    
    print("\n7️⃣ 验证重构的关键API：")
    verification_methods = [
        "wm.increment_turn() - 对话轮次增加",
        "wm.encode(content, importance=0.8) - 重要性编码", 
        "wm.get_buffer_stats() - 获取统计信息",
        "wm.prune_low_value_memories(0.1) - 清理低价值记忆",
        "wm.query_similar(query, filter_by_retention=True) - 留存过滤查询"
    ]
    
    for method in verification_methods:
        print(f"   ✓ {method}")
    
    print("\n8️⃣ 性能指标对比：")
    metrics = [
        ("记忆淘汰策略", "LRU（时间顺序）", "留存分数最低"),
        ("衰减单位", "绝对时间", "对话轮次"),
        ("容量策略", "固定（20条）", "动态估算（基于模型上下文）"),
        ("重要性影响", "无影响", "影响衰减速率"),
        ("情感集成", "无", "字段级映射")
    ]
    
    for metric, before, after in metrics:
        print(f"   {metric:12} | {before:20} → {after}")
    
    print("\n" + guide.create_backup_instructions())
    
    print("\n" + "=" * 80)
    print("✅ 方案A实施准备就绪")
    print("只需按上述步骤替换，即可获得所有增强功能")
    print("=" * 80)

if __name__ == "__main__":
    main()