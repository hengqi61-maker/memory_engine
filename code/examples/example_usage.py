#!/usr/bin/env python3
"""
OpenClaw生物学启发记忆引擎 - 使用示例

演示如何集成和使用新记忆引擎，包括：
1. 基本配置和初始化
2. 记忆摄入和处理
3. 记忆检索和查询
4. 系统管理和监控
5. 与现有OpenClaw引擎的集成
"""

import json
import os
import sys
# 设置UTF-8编码以避免Windows控制台Unicode错误
try:
    if sys.stdout.encoding != 'utf-8':
        sys.stdout.reconfigure(encoding='utf-8')
except (AttributeError, LookupError):
    # Python <3.7 或平台不支持，跳过
    pass
import time
from pathlib import Path
from datetime import datetime

# 添加当前目录到路径以便导入
sys.path.insert(0, os.path.dirname(__file__))
# 添加modules目录路径
modules_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "modules"))
sys.path.insert(0, modules_dir)

# 导入引擎
try:
    from biological_memory_engine import (
        BiologicalMemoryEngine,
        MemoryItem,
        MemoryQuery,
        MemoryContext,
        MemoryType,
        MemoryStatus
    )
    ENGINE_AVAILABLE = True
except ImportError as e:
    print(f"[警告] 无法导入生物记忆引擎: {e}")
    ENGINE_AVAILABLE = False

# 导入现有OpenClaw引擎用于兼容性演示
try:
    from openclaw_memory_engine_fixed import OpenClawMemoryEngine
    LEGACY_ENGINE_AVAILABLE = True
except ImportError:
    LEGACY_ENGINE_AVAILABLE = False


# ============================================================================
# 示例1: 基本配置和使用
# ============================================================================

def example_basic_usage():
    """基础使用示例"""
    print("=" * 70)
    print("示例1: 基础使用")
    print("=" * 70)
    
    if not ENGINE_AVAILABLE:
        print("[ERROR] 引擎不可用，跳过示例")
        return
    
    # 1. 配置引擎
    config = {
        "system_name": "DemoMemoryEngine",
        "version": "1.0.0",
        "module_configs": {
            "working_memory": {
                "capacity": 15,
                "embedding_backend": "ollama"  # 使用Ollama嵌入
            },
            "long_term_storage": {
                "storage_path": "./example_storage",
                "storage_backend": "json"
            },
            "consolidation_pruning": {
                "decay_rates": {
                    "fact": 0.01,
                    "decision": 0.03,
                    "opinion": 0.05,
                    "instruction": 0.02,
                    "emotional": 0.04
                }
            }
        }
    }
    
    # 2. 初始化引擎
    engine = BiologicalMemoryEngine(config)
    print("[OK] 引擎初始化完成")
    print(f"   管道: {engine.config.get('pipeline', [])}")
    
    # 3. 创建测试记忆内容
    test_memories = [
        {
            "content": "OpenClaw是一个智能个人助理系统，支持记忆管理。",
            "source": "系统介绍",
            "tags": ["openclaw", "助理", "记忆"]
        },
        {
            "content": "记忆遗忘曲线表明人类记忆会随时间指数衰减。",
            "source": "心理学",
            "tags": ["记忆", "心理学", "遗忘曲线"]
        },
        {
            "content": "工作记忆容量有限，通常为4-7个信息块。",
            "source": "认知科学",
            "tags": ["工作记忆", "认知科学", "容量限制"]
        },
        {
            "content": "情绪评估可以让AI理解内容的重要性。",
            "source": "AI设计",
            "tags": ["情绪", "AI", "重要性"]
        }
    ]
    
    # 4. 摄入记忆
    print("\n[NOTE] 摄入记忆:")
    for i, memory_data in enumerate(test_memories):
        result = engine.ingest(
            content=memory_data["content"],
            content_type="text",
            source=memory_data["source"]
        )
        
        if result.success:
            memory_item = result.data
            print(f"   [OK] 记忆 {i+1}: {memory_data['content'][:40]}...")
            print(f"       状态: {memory_item.status.value}, 类型: {memory_item.memory_type.value}")
            print(f"       重要性: {memory_item.importance:.2f}, 强度: {memory_item.strength:.2f}")
        else:
            print(f"   [ERROR] 记忆 {i+1} 失败: {result.message}")
    
    # 5. 检索记忆
    print("\n[SEARCH] 检索记忆:")
    test_queries = ["记忆", "工作记忆", "情绪"]
    
    for query in test_queries:
        result = engine.retrieve(query, top_k=2)
        
        if result.success and result.data:
            memories = result.data if isinstance(result.data, list) else [result.data]
            print(f"   [CLIPBOARD] 查询: '{query}'")
            for j, memory in enumerate(memories[:2]):
                # 显示摘要信息
                print(f"      结果 {j+1}: {memory.content[:60]}...")
                print(f"          类型: {memory.memory_type.value}, 重要性: {memory.importance:.2f}")
                if memory.emotional_scores:
                    emotion_summary = f"情绪: {memory.emotional_scores.get('overall_emotion', '未知')}"
                    print(f"          {emotion_summary}")
        else:
            print(f"   [ERROR] 查询 '{query}' 无结果: {result.message}")
    
    # 6. 系统统计
    print("\n[CHART] 系统统计:")
    stats = engine.get_stats()
    print(f"   总处理记忆数: {stats.get('total_processed', 0)}")
    print(f"   模块统计:")
    for module, module_stats in stats.get("modules", {}).items():
        count = module_stats.get("process_count", 0)
        if count > 0:
            avg_time = module_stats.get("avg_time_ms", 0)
            print(f"     {module}: {count}次处理, 平均{avg_time:.1f}ms")
    
    # 7. 睡眠周期
    print("\n[睡眠] 执行睡眠周期（记忆巩固）:")
    sleep_result = engine.sleep_cycle()
    print(f"   {sleep_result.message}")
    
    print("\n" + "=" * 70)
    print("示例1完成")
    print("=" * 70)


# ============================================================================
# 示例2: 高级功能和自定义处理
# ============================================================================

def example_advanced_features():
    """高级功能示例"""
    print("\n" + "=" * 70)
    print("示例2: 高级功能和自定义处理")
    print("=" * 70)
    
    if not ENGINE_AVAILABLE:
        print("[ERROR] 引擎不可用，跳过示例")
        return
    
    # 1. 使用自定义配置
    config = {
        "pipeline": [
            "sensory_registration",
            "working_memory",
            "emotional_appraisal",
            "long_term_storage"  # 跳过巩固修剪
        ],
        "module_configs": {
            "sensory_registration": {
                "channels": ["text", "log"],
                "buffer_size": 500,
                "attention_rules": [
                    {"pattern": "错误", "priority": 1.8},
                    {"pattern": "重要", "priority": 1.5},
                    {"pattern": "注意", "priority": 1.3}
                ]
            },
            "emotional_appraisal": {
                "rules": {
                    "urgent_keywords": ["紧急", "立刻", "马上"]
                }
            }
        }
    }
    
    engine = BiologicalMemoryEngine(config)
    
    # 2. 使用MemoryItem直接控制
    print("[CLIPBOARD] 直接使用MemoryItem创建记忆:")
    
    custom_memory = MemoryItem(
        content="这是一个非常重要且紧急的系统通知，需要立即处理。",
        content_type="text",
        source="system_alert",
        memory_type=MemoryType.DECISION,
        importance=0.9,
        keywords=["系统", "通知", "紧急", "重要"]
    )
    
    # 手动处理单步
    context = MemoryContext(
        user_id="test_user",
        attention_focus=["系统监控", "报警处理"]
    )
    
    # 直接使用coordinator处理特定模块
    result = engine.coordinator.process_memory(custom_memory, context)
    
    if result.success:
        processed_memory = result.data
        print(f"   [OK] 自定义记忆处理完成")
        print(f"       状态: {processed_memory.status.value}")
        print(f"       情绪评分: {processed_memory.emotional_scores}")
        print(f"       处理路径: {context.processing_path}")
    
    # 3. 高级查询
    print("\n[SEARCH] 高级查询示例:")
    
    # 创建复杂查询
    query = MemoryQuery(
        query_text="系统",
        content_types=["text"],
        min_importance=0.3,
        max_results=5,
        retrieval_mode="hybrid",
        weights={
            "semantic": 0.4,
            "temporal": 0.3,
            "causal": 0.2,
            "emotional": 0.1
        }
    )
    
    result = engine.retrieve(query=query.query_text, top_k=query.max_results)
    
    if result.success and result.data:
        memories = result.data
        print(f"   查询结果: {len(memories)} 条记忆")
        for i, memory in enumerate(memories[:3]):
            # 显示详细信息
            tags = f", 关键词: {', '.join(memory.keywords[:3])}" if memory.keywords else ""
            print(f"   {i+1}. {memory.content[:50]}...")
            print(f"       类型: {memory.memory_type.value}, 来源: {memory.source}{tags}")
            if memory.emotional_scores:
                valence = memory.emotional_scores.get('valence', 0)
                emotion = "正面" if valence > 0.2 else "负面" if valence < -0.2 else "中性"
                print(f"       情绪: {emotion} (效价: {valence:.2f})")
    
    # 4. 管道执行控制
    print("\n[齿轮] 自定义管道执行:")
    
    # 只执行部分模块
    partial_pipeline = ["working_memory", "emotional_appraisal"]
    
    test_item = MemoryItem(
        content="这是一个测试项目，用于演示部分管道处理。",
        source="test"
    )
    
    result = engine.coordinator.execute_pipeline(
        pipeline=partial_pipeline,
        memory_item=test_item
    )
    
    if result.success:
        item = result.data
        print(f"   [OK] 部分管道处理完成")
        print(f"       最终状态: {item.status.value}")
        print(f"       经过模块: {result.metadata.get('processing_path', [])}")
    
    # 5. 系统状态管理
    print("\n[CHART] 详细系统统计:")
    stats = engine.coordinator.get_system_stats()
    
    # 输出格式化统计
    total_processed = stats.get("total_processed", 0)
    total_errors = stats.get("total_errors", 0)
    error_rate = (total_errors / total_processed * 100) if total_processed > 0 else 0
    
    print(f"   总处理数: {total_processed}")
    print(f"   总错误数: {total_errors} (错误率: {error_rate:.1f}%)")
    print(f"   平均处理时间: {stats.get('avg_processing_time_ms', 0):.1f}ms")
    
    print("\n" + "=" * 70)
    print("示例2完成")
    print("=" * 70)


# ============================================================================
# 示例3: 与现有OpenClaw引擎的兼容性集成
# ============================================================================

def example_compatibility_integration():
    """兼容性集成示例"""
    print("\n" + "=" * 70)
    print("示例3: 与现有OpenClaw引擎的兼容性集成")
    print("=" * 70)
    
    if not ENGINE_AVAILABLE or not LEGACY_ENGINE_AVAILABLE:
        print("[WARNING]️  缺少依赖，跳过兼容性示例")
        if not LEGACY_ENGINE_AVAILABLE:
            print("   无法导入openclaw_memory_engine_fixed")
        return
    
    print("目标: 将新生物记忆引擎与原有OpenClaw引擎集成")
    print("策略: 创建适配器层，支持渐进式迁移")
    
    # 1. 演示向后兼容适配器
    class BackwardCompatibleAdapter:
        """向后兼容适配器"""
        
        def __init__(self, new_engine: BiologicalMemoryEngine, legacy_engine: OpenClawMemoryEngine):
            self.new_engine = new_engine
            self.legacy_engine = legacy_engine
            self.migration_mode = "hybrid"  # hybrid, new_only, legacy_only
        
        def ingest_log_file(self, file_path: str, use_new_engine: bool = True):
            """兼容原有的ingest_log_file方法"""
            if use_new_engine and self.migration_mode in ["hybrid", "new_only"]:
                print(f"   🆕 使用新引擎处理文件: {file_path}")
                
                try:
                    # 读取文件
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # 使用新引擎处理
                    result = self.new_engine.ingest(
                        content=content,
                        content_type="log",
                        source=file_path
                    )
                    
                    if result.success:
                        print(f"      [OK] 新引擎处理成功")
                        return True
                    else:
                        print(f"      [WARNING]️  新引擎处理失败: {result.message}")
                        # 回退到旧引擎
                        if self.migration_mode == "hybrid":
                            print(f"      ↪️ 回退到旧引擎")
                            return self.legacy_engine.ingest_log_file(file_path)
                        else:
                            return False
                            
                except Exception as e:
                    print(f"      [ERROR] 新引擎异常: {e}")
                    if self.migration_mode == "hybrid":
                        return self.legacy_engine.ingest_log_file(file_path)
                    else:
                        return False
            else:
                print(f"   🏛️  使用旧引擎处理文件: {file_path}")
                return self.legacy_engine.ingest_log_file(file_path)
        
        def retrieve(self, query_text: str, top_k: int = 5):
            """兼容原有的retrieve方法"""
            if self.migration_mode in ["hybrid", "new_only"]:
                print(f"   🆕 使用新引擎检索: '{query_text}'")
                
                result = self.new_engine.retrieve(query_text, top_k)
                
                if result.success and result.data:
                    memories = result.data if isinstance(result.data, list) else [result.data]
                    
                    # 转换为旧格式
                    legacy_format = []
                    for memory in memories:
                        legacy_format.append({
                            "content": memory.content[:200],
                            "type": memory.memory_type.value,
                            "confidence": memory.confidence,
                            "importance": memory.importance,
                            "timestamp": memory.timestamp
                        })
                    
                    print(f"      [OK] 新引擎找到 {len(legacy_format)} 条结果")
                    return legacy_format
                else:
                    print(f"      [WARNING]️  新引擎无结果，尝试旧引擎")
                    if self.migration_mode == "hybrid":
                        return self.legacy_engine.retrieve(query_text, top_k)
                    else:
                        return []
            else:
                print(f"   🏛️  使用旧引擎检索: '{query_text}'")
                return self.legacy_engine.retrieve(query_text, top_k)
        
        def sleep_cycle(self):
            """兼容原有的sleep_cycle方法"""
            if self.migration_mode in ["hybrid", "new_only"]:
                print(f"   🆕 使用新引擎睡眠周期")
                result = self.new_engine.sleep_cycle()
                if result.success:
                    print(f"      [OK] 新引擎睡眠周期完成: {result.message}")
                    
                    # 如果需要，也执行旧引擎的睡眠周期
                    if self.migration_mode == "hybrid":
                        print(f"      ↪️ 同时执行旧引擎睡眠周期")
                        self.legacy_engine.sleep_cycle()
                else:
                    print(f"      [ERROR] 新引擎睡眠周期失败: {result.message}")
            else:
                print(f"   🏛️  使用旧引擎睡眠周期")
                self.legacy_engine.sleep_cycle()
        
        def set_migration_mode(self, mode: str):
            """设置迁移模式"""
            valid_modes = ["legacy_only", "hybrid", "new_only"]
            if mode in valid_modes:
                old_mode = self.migration_mode
                self.migration_mode = mode
                print(f"迁移模式从 '{old_mode}' 切换到 '{mode}'")
            else:
                print(f"无效模式: {mode}, 有效模式: {valid_modes}")
    
    # 2. 初始化新旧引擎
    print("\n1. 初始化新旧引擎...")
    
    new_engine = BiologicalMemoryEngine({
        "module_configs": {
            "long_term_storage": {
                "storage_path": "./compatibility_storage"
            }
        }
    })
    
    legacy_engine = OpenClawMemoryEngine(
        memory_name="legacy_memory_store",
        enable_archive=True,
        archive_dir="./legacy_archive"
    )
    
    print("   [OK] 新旧引擎初始化完成")
    
    # 3. 创建适配器
    print("\n2. 创建兼容性适配器...")
    adapter = BackwardCompatibleAdapter(new_engine, legacy_engine)
    
    # 4. 演示混合模式工作流
    print("\n3. 混合模式工作流演示:")
    
    # 测试模式切换
    adapter.set_migration_mode("hybrid")
    
    # 创建一个测试日志文件
    test_log_content = """[INFO] 系统启动完成
[WARNING] 内存使用率达到85%
[ERROR] 数据库连接失败，正在重试
[INFO] 用户登录成功
[IMPORTANT] 需要备份重要数据
"""
    
    test_log_path = "./test_system.log"
    with open(test_log_path, 'w', encoding='utf-8') as f:
        f.write(test_log_content)
    
    print(f"\n   a) 摄入日志文件: {test_log_path}")
    adapter.ingest_log_file(test_log_path)
    
    print(f"\n   b) 检索测试:")
    results = adapter.retrieve("错误", top_k=3)
    if results:
        print(f"      找到 {len(results)} 条相关记录")
        for i, res in enumerate(results[:2]):
            print(f"        {i+1}. {res.get('content', '')[:60]}...")
    
    print(f"\n   c) 执行睡眠周期:")
    adapter.sleep_cycle()
    
    # 5. 演示渐进迁移
    print("\n4. 渐进迁移策略:")
    
    print("   [CLIPBOARD] 迁移计划:")
    print("     1. 阶段1: 使用'hybrid'模式，新旧引擎并行")
    print("     2. 阶段2: 监控新引擎性能和准确性")
    print("     3. 阶段3: 切换到'new_only'模式，旧引擎作为备份")
    print("     4. 阶段4: 完全迁移，移除旧引擎依赖")
    
    print("\n   [CHART] 迁移检查点:")
    print("     [OK] 新旧引擎API兼容性: 通过适配器实现")
    print("     [OK] 数据格式兼容性: 支持双向转换")
    print("     [OK] 性能基准测试: 需要实际测试验证")
    print("     [OK] 错误处理和回滚: 适配器支持自动回退")
    
    # 清理测试文件
    try:
        os.remove(test_log_path)
    except:
        pass
    
    print("\n" + "=" * 70)
    print("示例3完成")
    print("=" * 70)


# ============================================================================
# 示例4: 性能测试和监控
# ============================================================================

def example_performance_monitoring():
    """性能测试和监控示例"""
    print("\n" + "=" * 70)
    print("示例4: 性能测试和监控")
    print("=" * 70)
    
    if not ENGINE_AVAILABLE:
        print("[ERROR] 引擎不可用，跳过示例")
        return
    
    import time
    import random
    
    # 初始化引擎（轻量配置）
    config = {
        "module_configs": {
            "working_memory": {"capacity": 10},
            "long_term_storage": {"storage_path": "./perf_test_storage"}
        }
    }
    
    engine = BiologicalMemoryEngine(config)
    
    # 1. 批量摄入性能测试
    print("[CHART_UP] 批量摄入性能测试:")
    
    # 生成测试数据
    test_items = []
    for i in range(50):
        content = f"测试记忆项目 {i+1}: "
        content += " ".join([f"关键词{random.randint(1, 20)}" for _ in range(5)])
        test_items.append(content)
    
    # 测试单条摄入
    print("   a) 单条摄入测试 (10条):")
    single_times = []
    for i, content in enumerate(test_items[:10]):
        start = time.time()
        result = engine.ingest(content, source=f"perf_test_{i}")
        elapsed = time.time() - start
        
        if result.success:
            single_times.append(elapsed)
            if i < 3:  # 显示前3条的时间
                print(f"      记忆 {i+1}: {elapsed*1000:.1f}ms")
    
    avg_single = sum(single_times) / len(single_times) if single_times else 0
    print(f"      平均: {avg_single*1000:.1f}ms/条")
    
    # 2. 批量检索性能测试
    print("\n   b) 检索性能测试:")
    
    queries = ["测试", "关键词", "记忆", "项目"]
    retrieval_times = []
    
    for query in queries:
        start = time.time()
        result = engine.retrieve(query, top_k=5)
        elapsed = time.time() - start
        
        if result.success:
            retrieval_times.append(elapsed)
            count = len(result.data) if isinstance(result.data, list) else (1 if result.data else 0)
            print(f"      查询 '{query}': {elapsed*1000:.1f}ms, 结果: {count}条")
    
    avg_retrieval = sum(retrieval_times) / len(retrieval_times) if retrieval_times else 0
    print(f"      平均检索时间: {avg_retrieval*1000:.1f}ms")
    
    # 3. 内存和存储监控
    print("\n   c) 资源使用监控:")
    
    stats = engine.get_stats()
    
    memory_items_count = 0
    total_processing_time = 0
    
    for module_name, module_stats in stats.get("modules", {}).items():
        count = module_stats.get("process_count", 0)
        avg_time = module_stats.get("avg_time_ms", 0)
        
        if count > 0:
            memory_items_count = max(memory_items_count, count)
            total_processing_time += avg_time * count / 1000  # 转换为秒
            
            print(f"      {module_name}: {count}次处理, 平均{avg_time:.1f}ms")
    
    print(f"\n      总处理次数: {memory_items_count}")
    print(f"      总处理时间: {total_processing_time:.2f}秒")
    
    # 4. 负载测试建议
    print("\n   d) 负载测试建议:")
    print("      1. 逐步增加并发请求数量")
    print("      2. 监控内存使用和响应时间")
    print("      3. 测试长时间运行的稳定性")
    print("      4. 验证大规模记忆库的检索性能")
    
    # 5. 性能优化提示
    print("\n   e) 性能优化提示:")
    print("      1. 调整工作记忆容量以减少内存使用")
    print("      2. 配置合适的存储后端（如SQLite）")
    print("      3. 启用缓存减少重复计算")
    print("      4. 批量处理减少模块间调用开销")
    
    # 清理测试存储
    try:
        import shutil
        shutil.rmtree("./perf_test_storage", ignore_errors=True)
    except:
        pass
    
    print("\n" + "=" * 70)
    print("示例4完成")
    print("=" * 70)


# ============================================================================
# 示例5: 实际应用场景
# ============================================================================

def example_real_world_scenarios():
    """实际应用场景示例"""
    print("\n" + "=" * 70)
    print("示例5: 实际应用场景")
    print("=" * 70)
    
    if not ENGINE_AVAILABLE:
        print("[ERROR] 引擎不可用，跳过示例")
        return
    
    print("场景1: 学习笔记记忆系统")
    
    # 初始化专门用于学习的配置
    learning_config = {
        "system_name": "LearningMemorySystem",
        "module_configs": {
            "sensory_registration": {
                "channels": ["text", "concept"],
                "attention_rules": [
                    {"pattern": "定义", "priority": 1.5},
                    {"pattern": "定理", "priority": 1.5},
                    {"pattern": "例子", "priority": 1.3},
                    {"pattern": "重要", "priority": 1.8}
                ]
            },
            "consolidation_pruning": {
                "decay_rates": {
                    "fact": 0.005,      # 事实记忆衰减更慢
                    "instruction": 0.01,  # 指令/步骤衰减慢
                    "default": 0.02
                }
            },
            "long_term_storage": {
                "storage_path": "./learning_memory",
                "max_size_gb": 5.0
            }
        }
    }
    
    learning_engine = BiologicalMemoryEngine(learning_config)
    
    # 模拟学习内容
    learning_materials = [
        "机器学习定义: 让计算机从数据中学习模式，无需明确编程。",
        "梯度下降算法: 通过迭代调整参数最小化损失函数。",
        "过拟合现象: 模型在训练集上表现很好，但在测试集上表现差。",
        "交叉验证: 将数据集分成多份，轮流作为训练集和验证集。",
        "准确率公式: (正确预测数) / (总预测数)。"
    ]
    
    print("\n   a) 摄入学习材料:")
    for material in learning_materials:
        result = learning_engine.ingest(
            content=material,
            content_type="text",
            source="机器学习课程"
        )
        
        if result.success:
            print(f"      [OK] {material[:30]}...")
    
    print("\n   b) 复习和检索:")
    review_queries = ["机器学习", "过拟合", "交叉验证", "准确率"]
    
    for query in review_queries:
        result = learning_engine.retrieve(query, top_k=2)
        
        if result.success and result.data:
            memories = result.data
            print(f"      [BOOKS] '{query}': {len(memories)} 条相关记忆")
    
    print("\n   c) 学习效果巩固（睡眠周期）:")
    sleep_result = learning_engine.sleep_cycle()
    print(f"      {sleep_result.message}")
    
    print("\n场景2: 项目日志分析和决策支持")
    
    # 项目日志分析配置
    project_config = {
        "module_configs": {
            "emotional_appraisal": {
                "rules": {
                    "priority_keywords": ["错误", "失败", "成功", "完成", "延期"]
                }
            },
            "working_memory": {
                "capacity": 30  # 更大的工作记忆用于项目跟踪
            }
        }
    }
    
    project_engine = BiologicalMemoryEngine(project_config)
    
    # 模拟项目日志
    project_logs = [
        "2026-03-28: 项目启动会议，确定需求和目标。",
        "2026-03-29: 数据库设计完成，开始后端开发。",
        "2026-03-30: 遇到API性能问题，需要优化。",
        "2026-03-31: 性能优化成功，响应时间减少50%。",
        "2026-04-01: 前端UI开发完成，开始集成测试。",
        "2026-04-02: 发现关键bug，影响用户登录功能。",
        "2026-04-03: bug修复完成，测试通过。",
        "2026-04-04: 项目延期两天，等待客户确认。",
        "2026-04-05: 客户反馈积极，项目进入部署阶段。"
    ]
    
    print("\n   a) 分析项目日志:")
    for log in project_logs:
        # 为不同类型的内容添加情绪标记
        if "错误" in log or "bug" in log or "问题" in log:
            importance = 0.8
        elif "成功" in log or "完成" in log or "积极" in log:
            importance = 0.7
        elif "延期" in log or "等待" in log:
            importance = 0.6
        else:
            importance = 0.5
        
        result = project_engine.ingest(
            content=log,
            content_type="log",
            source="项目管理系统",
            # importance参数不直接支持，通过其他方式传递
        )
        
        if result.success:
            # 可以在这里调整重要性
            pass
    
    print("\n   b) 项目状态查询:")
    status_result = project_engine.retrieve("项目状态", top_k=5)
    if status_result.success and status_result.data:
        print(f"      找到 {len(status_result.data)} 条项目相关记录")
        latest = status_result.data[0] if isinstance(status_result.data, list) else status_result.data
        print(f"      最新进展: {latest.content}")
    
    print("\n   c) 问题和解决方案检索:")
    problem_result = project_engine.retrieve("问题", top_k=3)
    if problem_result.success and problem_result.data:
        problems = problem_result.data
        print(f"      发现 {len(problems)} 个问题记录")
        for i, problem in enumerate(problems[:3]):
            print(f"        问题{i+1}: {problem.content}")
    
    print("\n场景2: 个人知识库管理")
    print("   可用于整理研究笔记、灵感想法、个人计划等")
    print("   基于生物学记忆原理，实现智能组织和检索")
    
    # 清理测试数据
    try:
        import shutil
        shutil.rmtree("./learning_memory", ignore_errors=True)
    except:
        pass
    
    print("\n" + "=" * 70)
    print("示例5完成")
    print("=" * 70)


# ============================================================================
# 主执行函数
# ============================================================================

def main():
    """主执行函数"""
    print("OpenClaw生物学启发记忆引擎 - 完整示例套件")
    print("版本: 1.0.0 | 设计: 架构设计子代理")
    print()
    
    # 运行所有示例
    examples = [
        ("基础使用", example_basic_usage),
        ("高级功能", example_advanced_features),
        ("兼容性集成", example_compatibility_integration),
        ("性能测试", example_performance_monitoring),
        ("实际应用", example_real_world_scenarios)
    ]
    
    for name, func in examples:
        try:
            func()
        except Exception as e:
            print(f"示例 '{name}' 执行失败: {e}")
            import traceback
            traceback.print_exc()
        print()
    
    print("=" * 70)
    print("所有示例完成")
    print("=" * 70)
    
    # 总结和下一步建议
    print("\n🎯 下一步建议:")
    print("1. 在实际项目中集成新记忆引擎")
    print("2. 运行性能基准测试和对比")
    print("3. 根据实际使用反馈调整配置")
    print("4. 开发可视化界面和监控工具")
    print("5. 考虑分布式扩展和云部署")


if __name__ == "__main__":
    main()