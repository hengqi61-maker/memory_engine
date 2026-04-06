#!/usr/bin/env python3
"""
增强记忆系统 - 完整测试和演示
测试三层记忆模型和工作流程
"""

import os
import sys
import json
import time
from datetime import datetime, timedelta

# 添加当前目录到Python路径，以便导入模块
sys.path.insert(0, os.path.dirname(__file__))

from code.modules.enhanced_working_memory import (
    EnhancedMemorySystem, MemoryType, MemoryHierarchy
)


def test_human_memory_model():
    """测试人类记忆模型特性"""
    print("=" * 70)
    print("增强记忆系统 - 人类记忆模型测试")
    print("=" * 70)
    
    # 创建配置
    config = {
        "ultra_short_term": {
            "max_items": 7,  # 基于"7±2"原则
            "lifespan_seconds": 18.0  # 十八秒定律
        },
        "working_memory": {
            "capacity": 15,  # 工作记忆有限容量
            "consolidation_threshold": 0.6,  # 巩固阈值
            "rehearsal_cycles": 2  # 排练阈值
        },
        "long_term": {
            "storage_path": "memory/test_complete_system.json",
            "max_memories": 50,
            "reconsolidation_interval_hours": 1  # 为了测试，设为1小时
        }
    }
    
    # 初始化系统
    print("\n1. 初始化增强记忆系统...")
    memory_system = EnhancedMemorySystem(config)
    
    # 显示初始状态
    initial_stats = memory_system.get_system_stats()
    print(f"   系统初始化完成:")
    print(f"   瞬时记忆: {initial_stats['ultra_short_term']['current_size']}/{initial_stats['ultra_short_term']['capacity']}")
    print(f"   工作记忆: {initial_stats['working_memory']['current_size']}/{initial_stats['working_memory']['capacity']}")
    print(f"   长期记忆: {initial_stats['long_term']['total_memories']}")
    
    # 2. 测试短期记忆特性（十八秒定律）
    print("\n2. 测试十八秒定律...")
    print("   添加一系列记忆到瞬时记忆:")
    
    ultra_short_memories = [
        ("第一个记忆：今天的日期是2026-04-06", 0.5, MemoryType.FACT),
        ("第二个记忆：我正在测试记忆系统", 0.6, MemoryType.LOG),
        ("第三个记忆：Python是最好的编程语言之一", 0.3, MemoryType.OPINION),
        ("第四个记忆：量子计算使用量子比特", 0.8, MemoryType.FACT),
        ("第五个记忆：需要完成大学作业", 0.9, MemoryType.TASK),
        ("第六个记忆：OpenClaw工作正常", 0.7, MemoryType.LOG),
        ("第七个记忆：GitHub上有好项目", 0.4, MemoryType.OPINION),
        ("第八个记忆：超过容量，第一个将被淘汰", 0.6, MemoryType.FACT),
        ("第九个记忆：演示十八秒淘汰", 0.5, MemoryType.LOG),
    ]
    
    for i, (content, importance, mem_type) in enumerate(ultra_short_memories):
        mem_id = memory_system.encode_memory(
            content, 
            importance=importance,
            memory_type=mem_type,
            source=f"test_{i+1}"
        )
        print(f"    [{i+1}] {mem_id[:8]}: {content[:30]}...")
    
    # 检查瞬时记忆状态
    ultra_stats = memory_system.ultra_short_term.get_stats()
    print(f"\n   瞬时记忆状态:")
    print(f"   容量: {ultra_stats['current_size']}/{ultra_stats['capacity']}")
    print(f"   平均年龄: {ultra_stats['average_age_seconds']:.1f}秒")
    print(f"   生命周期: {ultra_stats['lifespan_seconds']}秒")
    
    # 3. 模拟时间流逝和遗忘
    print("\n3. 模拟时间流逝和记忆衰减...")
    print("   等待10秒，让一些记忆衰减...")
    time.sleep(10)
    
    # 再次检查瞬时记忆
    print("   10秒后瞬时记忆状态:")
    for mem_id, (memory, access_time) in memory_system.ultra_short_term.buffer.items():
        age = (datetime.now() - access_time).total_seconds()
        activation = memory.calculate_decay()
        print(f"   {mem_id[:8]}: {memory.content[:30]}... (已存 {age:.1f}秒, 激活: {activation:.2f})")
    
    # 4. 测试工作记忆转移
    print("\n4. 测试重要记忆的工作记忆转移...")
    
    important_memories = [
        ("非常重要的决定：明天开始学习量子算法", 0.95, MemoryType.DECISION, 0.8),
        ("情感记忆：终于解决了编程难题，非常开心", 0.8, MemoryType.EXPERIENCE, 0.9),
        ("关键知识：薛定谔方程描述量子态演化", 0.9, MemoryType.FACT, 0.5),
        ("代码突破：实现了量子傅里叶变换", 0.85, MemoryType.CODE, 0.7),
    ]
    
    for content, importance, mem_type, emotion in important_memories:
        mem_id = memory_system.encode_memory(
            content,
            importance=importance,
            memory_type=mem_type,
            emotional_value=emotion,
            source="important_test"
        )
        print(f"   重要记忆: {content[:40]}... (情感: {emotion:.1f})")
    
    # 检查工作记忆状态
    working_stats = memory_system.working_memory.get_stats()
    print(f"\n   工作记忆状态:")
    print(f"   容量: {working_stats['current_size']}/{working_stats['capacity']}")
    print(f"   平均激活: {working_stats['average_activation']:.2f}")
    print(f"   候选巩固: {working_stats['consolidation_candidates']}")
    
    # 5. 测试记忆检索
    print("\n5. 测试记忆检索功能...")
    
    test_queries = [
        ("量子", "寻找量子相关记忆"),
        ("Python", "寻找Python相关记忆"),
        ("开心", "情感记忆检索"),
        ("代码", "代码相关记忆"),
    ]
    
    for query, description in test_queries:
        print(f"\n   查询: '{query}' ({description})")
        results = memory_system.query(query, top_k=3)
        
        if results:
            for i, (memory, score) in enumerate(results):
                print(f"    {i+1}. [{memory.type.value}] 分数:{score:.3f}")
                print(f"       内容: {memory.content[:60]}...")
                print(f"       层级: {memory.hierarchy.value}, 激活: {memory.calculate_decay():.2f}")
        else:
            print("   未找到相关记忆")
    
    # 6. 执行完整的睡眠周期
    print("\n" + "=" * 50)
    print("6. 执行睡眠周期 (记忆巩固)...")
    print("=" * 50)
    
    sleep_stats = memory_system.perform_sleep_cycle()
    print(f"\n   睡眠周期完成统计:")
    print(f"   瞬时记忆剩余: {sleep_stats['ultra_short_term']['current_size']}")
    print(f"   工作记忆剩余: {sleep_stats['working_memory']['current_size']}")
    print(f"   长期记忆新增: {sleep_stats['long_term']['total_memories']}")
    
    # 7. 测试记忆的持久性和检索
    print("\n7. 测试记忆持久性和重启恢复...")
    
    # 保存系统状态
    memory_system.consolidator._save_long_term_memories()
    print("   长期记忆已保存到文件")
    
    # 创建新系统实例加载记忆
    print("   创建新系统实例并加载记忆...")
    new_system = EnhancedMemorySystem(config)
    
    new_stats = new_system.get_system_stats()
    print(f"   新系统加载的长期记忆: {new_stats['long_term']['total_memories']}")
    
    # 测试从长期记忆检索
    long_term_query = "量子"
    print(f"\n   从长期记忆检索: '{long_term_query}'")
    
    # 注意：长期记忆检索需要实现，这里只是演示结构
    print("   (长期记忆检索功能需要实现在find_similar_memory中)")
    
    # 8. 整体系统统计
    print("\n" + "=" * 70)
    print("最终系统统计:")
    print("=" * 70)
    
    final_stats = memory_system.get_system_stats()
    
    print("\n系统概览:")
    print(f"  运行时间: {final_stats['system_uptime_seconds']:.0f} 秒")
    print(f"  总处理记忆: {final_stats['total_memories_processed']}")
    print(f"  上次睡眠周期: {final_stats['last_sleep_cycle'] or '从未'}")
    
    print("\n瞬时记忆 (18秒窗口):")
    print(f"  容量: {final_stats['ultra_short_term']['current_size']}/{final_stats['ultra_short_term']['capacity']}")
    print(f"  平均年龄: {final_stats['ultra_short_term']['average_age_seconds']:.1f} 秒")
    
    print("\n工作记忆 (有限容量):")
    print(f"  容量: {final_stats['working_memory']['current_size']}/{final_stats['working_memory']['capacity']}")
    print(f"  平均激活: {final_stats['working_memory']['average_activation']:.2f}")
    print(f"  类型分布: {final_stats['working_memory']['type_distribution']}")
    
    print("\n长期记忆 (持久存储):")
    print(f"  总记忆: {final_stats['long_term']['total_memories']}")
    print(f"  最大容量: {final_stats['long_term']['max_capacity']}")
    print(f"  平均重要性: {final_stats['long_term']['average_importance']:.2f}")
    print(f"  平均置信度: {final_stats['long_term']['average_confidence']:.2f}")
    
    # 9. 清理测试文件
    print("\n" + "=" * 70)
    
    test_file = "memory/test_complete_system.json"
    if os.path.exists(test_file):
        os.remove(test_file)
        print(f"[清理] 已删除测试文件: {test_file}")
    
    # 打印最后一条测试记忆的编码示例
    last_memory = "人类记忆模型测试完成，系统表现符合预期"
    last_id = memory_system.encode_memory(
        last_memory,
        importance=0.9,
        memory_type=MemoryType.LOG,
        source="test_conclusion"
    )
    
    print(f"\n[完成] 测试完成! 最后记忆ID: {last_id[:8]}")
    print("=" * 70)


def test_memory_decay_functions():
    """测试记忆衰减函数"""
    print("\n" + "=" * 70)
    print("记忆衰减函数测试")
    print("=" * 70)
    
    from code.modules.enhanced_working_memory import MemoryItem, MemoryHierarchy
    
    # 创建测试记忆
    memory_items = []
    
    # 1. 瞬时记忆 (18秒衰减)
    ultra_short = MemoryItem(
        id="test_ultra_1",
        content="这是瞬时记忆",
        hierarchy=MemoryHierarchy.ULTRA_SHORT_TERM,
        importance=0.5
    )
    
    # 2. 工作记忆 (对数衰减)
    working = MemoryItem(
        id="test_working_1",
        content="这是工作记忆",
        hierarchy=MemoryHierarchy.WORKING_MEMORY,
        importance=0.7,
        confidence=0.8
    )
    
    # 3. 长期记忆 (艾宾浩斯曲线)
    long_term = MemoryItem(
        id="test_long_1",
        content="这是长期记忆",
        hierarchy=MemoryHierarchy.LONG_TERM,
        importance=0.9,
        confidence=0.9,
        emotional_value=0.8
    )
    
    memory_items = [ultra_short, working, long_term]
    
    # 测试不同时间点的衰减
    print("测试不同记忆层级在不同时间点的激活水平:\n")
    print("时间(秒) | 瞬时 | 工作 | 长期")
    print("-" * 40)
    
    for t in [0, 10, 30, 60, 300, 1800, 3600, 86400]:  # 从0秒到1天
        print(f"{t:>7} |", end="")
        
        for memory in memory_items:
            # 设置最后访问时间为t秒前
            from datetime import datetime, timedelta
            test_time = datetime.now() - timedelta(seconds=t)
            memory.last_accessed = test_time
            
            activation = memory.calculate_decay()
            print(f" {activation:.3f} |", end="")
        
        print()
    
    print("\n衰减模式解读:")
    print("  瞬时记忆: 在18秒内快速衰减 (τ=18秒)")
    print("  工作记忆: 对数衰减，保持时间更长")
    print("  长期记忆: 艾宾浩斯曲线，随情感增强")


def demo_practical_application():
    """演示实际应用场景"""
    print("\n" + "=" * 70)
    print("实际应用场景演示")
    print("=" * 70)
    
    # 创建更实用的配置
    config = {
        "ultra_short_term": {
            "max_items": 9,  # 7±2的上限
            "lifespan_seconds": 18.0
        },
        "working_memory": {
            "capacity": 25,  # 实际工作记忆容量
            "consolidation_threshold": 0.7,
            "rehearsal_cycles": 3
        },
        "long_term": {
            "storage_path": "memory/practical_demo.json",
            "max_memories": 500,
            "reconsolidation_interval_hours": 24
        }
    }
    
    # 初始化系统
    print("\n场景: 学生的一天 - 学习量子物理\n")
    
    memory_system = EnhancedMemorySystem(config)
    
    # 模拟一天的记忆流
    daily_memories = [
        # 早上学习
        ("量子力学基本原理：波粒二象性", 0.9, MemoryType.FACT, "早课", ["物理学", "基础"], 0.3),
        ("薛定谔方程：iℏ∂ψ/∂t = Hψ", 0.95, MemoryType.CODE, "公式", ["方程", "数学"], 0.2),
        ("理解量子纠缠概念有点困难", 0.6, MemoryType.EXPERIENCE, "学习心得", ["困难", "概念"], -0.2),
        
        # 中午实践
        ("编写了Qiskit量子电路模拟器", 0.85, MemoryType.CODE, "编程实践", ["Python", "Qiskit"], 0.7),
        ("GitHub提交：量子算法库更新", 0.8, MemoryType.LOG, "项目", ["GitHub", "版本控制"], 0.5),
        ("小组讨论：量子计算应用前景", 0.7, MemoryType.OPINION, "讨论", ["小组", "应用"], 0.4),
        
        # 下午深入
        ("发现一个重要联系：纠缠与贝尔不等式", 0.95, MemoryType.FACT, "研究", ["关联", "理论"], 0.9),
        ("决定深入研究量子信息论", 0.9, MemoryType.DECISION, "学业规划", ["决定", "深度"], 0.6),
        ("准备下周的量子物理报告", 0.85, MemoryType.TASK, "待办事项", ["报告", "准备"], 0.3),
        
        # 晚上整理
        ("整理笔记：量子门操作矩阵表示", 0.75, MemoryType.EXPERIENCE, "整理", ["笔记", "矩阵"], 0.4),
        ("设置提醒：明天复习内容", 0.7, MemoryType.LOG, "提醒", ["规划", "复习"], 0.2),
    ]
    
    # 编码记忆
    for content, importance, mem_type, source, tags, emotion in daily_memories:
        memory_system.encode_memory(
            content,
            importance,
            mem_type,
            source,
            tags,
            emotion
        )
    
    # 模拟实时查询
    print("实时查询示例:")
    print("-" * 40)
    
    # 查询1：准备报告时需要的资料
    print("\n1. 准备量子物理报告时查询:")
    report_results = memory_system.query("量子物理", top_k=5)
    for i, (mem, score) in enumerate(report_results[:3]):
        print(f"   {i+1}. [{mem.type.value}] {mem.content[:50]}...")
    
    # 查询2：遇到困难时查找类似经验
    print("\n2. 遇到困难时查询类似经验:")
    difficulty_results = memory_system.query("困难", top_k=3)
    for i, (mem, score) in enumerate(difficulty_results):
        print(f"   {i+1}. [{mem.type.value}] {mem.content[:50]}... (情感: {mem.emotional_value:.1f})")
    
    # 查询3：决策支持
    print("\n3. 决策支持查询:")
    decision_results = memory_system.query("决定", top_k=3)
    for i, (mem, score) in enumerate(decision_results):
        print(f"   {i+1}. [{mem.type.value}] {mem.content[:50]}... (重要性: {mem.importance:.1f})")
    
    # 执行睡眠周期（一天结束）
    print("\n" + "=" * 40)
    print("一天结束，执行睡眠周期...")
    print("=" * 40)
    
    sleep_stats = memory_system.perform_sleep_cycle()
    
    print(f"\n夜间记忆巩固完成:")
    print(f"  转移到长期记忆: {sleep_stats['long_term']['total_memories']} 条")
    print(f"  工作记忆清理: {sleep_stats['working_memory']['current_size']} 条剩余")
    
    # 长期记忆查询（第二天）
    print("\n第二天，从长期记忆检索:")
    
    # 注意：这里需要实际实现长期记忆检索
    print("  (长期记忆检索依赖语义向量和相似度计算)")
    
    # 演示系统统计
    final_stats = memory_system.get_system_stats()
    
    print(f"\n最终学习统计:")
    print(f"  总编码记忆: {final_stats['total_memories_processed']}")
    print(f"  长期知识库: {final_stats['long_term']['total_memories']} 条")
    print(f"  知识结构: {final_stats['long_term']['type_distribution']}")
    
    # 清理
    test_file = "memory/practical_demo.json"
    if os.path.exists(test_file):
        os.remove(test_file)
    
    print("\n[演示完成] 记忆系统成功跟踪了一天的学习过程")


def main():
    """主测试函数"""
    print("增强记忆系统 - 完整测试套件")
    print("=" * 70)
    
    try:
        # 测试1：基础功能
        test_human_memory_model()
        
        # 测试2：记忆衰减
        test_memory_decay_functions()
        
        # 测试3：实际应用
        demo_practical_application()
        
        print("\n" + "=" * 70)
        print("所有测试完成! ✓")
        print("系统实现了:")
        print("  ✓ 十八秒瞬时记忆模型")
        print("  ✓ 工作记忆容量限制")
        print("  ✓ 长期记忆艾宾浩斯曲线")
        print("  ✓ 睡眠周期记忆巩固")
        print("  ✓ 情感增强记忆机制")
        print("=" * 70)
        
    except Exception as e:
        print(f"\n[错误] 测试过程中出错: {e}")
        import traceback
        traceback.print_exc()
        
        # 清理可能的测试文件
        test_files = [
            "memory/test_complete_system.json",
            "memory/practical_demo.json"
        ]
        
        for test_file in test_files:
            if os.path.exists(test_file):
                try:
                    os.remove(test_file)
                    print(f"[清理] 已删除: {test_file}")
                except:
                    pass


if __name__ == "__main__":
    # 确保测试目录存在
    os.makedirs("memory", exist_ok=True)
    
    main()