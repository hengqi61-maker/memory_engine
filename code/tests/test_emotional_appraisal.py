#!/usr/bin/env python3
"""
情绪评估模块测试脚本
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from emotional_appraisal import (
    EmotionalAppraisalEngine,
    RawMemoryChunk,
    create_emotion_analyzer,
    SignificanceScorer,
    ContextAwareness,
    MemoryClassifier
)

def test_emotion_analyzer():
    """测试情绪分析器"""
    print("=" * 70)
    print("测试情绪分析器")
    print("=" * 70)
    
    texts = [
        "我今天非常高兴，项目成功了！",
        "这个问题很糟糕，让我很生气。",
        "根据数据分析，结果符合预期。",
        "我有点不确定该怎么做。"
    ]
    
    analyzer = create_emotion_analyzer('hybrid')
    
    for text in texts:
        scores = analyzer.analyze(text)
        print(f"文本: {text[:30]}...")
        print(f"  愉悦度: {scores.pleasure:+.3f}")
        print(f"  唤醒度: {scores.arousal:+.3f}")
        print(f"  支配度: {scores.dominance:+.3f}")
        print(f"  情绪强度: {scores.intensity:.3f}")
        print()

def test_significance_scorer():
    """测试重要性评分器"""
    print("=" * 70)
    print("测试重要性评分器")
    print("=" * 70)
    
    texts = [
        "我今天完成了量子计算的作业，感觉很有成就感。",
        "社会公平是一个重要议题，我们需要更多讨论。",
        "根据实验数据，温度上升了2.5度。",
        "我不确定这个决定是否正确，需要更多思考。"
    ]
    
    scorer = SignificanceScorer()
    
    for text in texts:
        scores = scorer.estimate_dimensions(text)
        extended_score = scorer.calculate_extended_score(scores)
        
        print(f"文本: {text[:30]}...")
        print(f"  个人相关性: {scores.personal_relevance:.3f}")
        print(f"  任务效用: {scores.task_utility:.3f}")
        print(f"  社会价值: {scores.social_value:.3f}")
        print(f"  新颖性: {scores.novelty:.3f}")
        print(f"  复杂性: {scores.complexity:.3f}")
        print(f"  扩展得分: {extended_score:.3f}")
        print()

def test_memory_classifier():
    """测试记忆分类器"""
    print("=" * 70)
    print("测试记忆分类器")
    print("=" * 70)
    
    texts = [
        "量子计算使用量子比特代替经典比特，具有叠加态特性。",
        "我决定选择Python作为主要编程语言，因为它有丰富的库。",
        "我觉得今天的天气真好，阳光明媚，心情愉快。",
        "首先安装Python，然后配置环境变量，最后验证安装。"
    ]
    
    classifier = MemoryClassifier()
    
    for text in texts:
        result = classifier.analyze_memory(text)
        print(f"文本: {text[:40]}...")
        print(f"  类型: {result['memory_type']} (置信度: {result['confidence']:.3f})")
        print(f"  描述: {result['type_description']}")
        print(f"  类型重要性: {result['type_importance']:.3f}")
        if result['subtype']:
            print(f"  子类型: {result['subtype']}")
        print()

def test_context_awareness():
    """测试上下文感知"""
    print("=" * 70)
    print("测试上下文感知")
    print("=" * 70)
    
    processor = ContextAwareness()
    
    # 模拟对话
    conversation = [
        ("用户", "我今天在学习量子计算。"),
        ("助手", "量子计算很有趣，你在学习什么具体内容？"),
        ("用户", "我在学习量子比特和叠加态，但有些概念不太理解。"),
        ("用户", "另外，我的作业明天就要交了，有点着急。")
    ]
    
    for speaker, text in conversation:
        processor.update_conversation_history(text, speaker)
        processor.update_user_state(text)
        
        context_factor = processor.calculate_context_factor(text)
        topic_relevance = processor.calculate_topic_relevance(text)
        
        print(f"[{speaker}] {text}")
        print(f"  上下文因子: {context_factor:.3f}")
        print(f"  主题相关性: {topic_relevance:.3f}")
        
        if speaker == "用户":
            print(f"  用户状态: 紧急={processor.user_state.get('urgency', 0):.3f}, "
                  f"兴趣={processor.user_state.get('interest', 0):.3f}")
        print()

def test_full_engine():
    """测试完整引擎"""
    print("=" * 70)
    print("测试完整情绪评估引擎")
    print("=" * 70)
    
    engine = EmotionalAppraisalEngine()
    
    # 更新对话上下文
    engine.update_conversation_context(
        "我正在研究记忆增强技术，特别是情绪对记忆的影响。",
        speaker="user"
    )
    
    # 创建测试记忆
    test_memories = [
        RawMemoryChunk(
            content="情绪显著增强记忆编码，高唤醒度事件更容易被记住。",
            timestamp="2026-03-28T10:00:00",
            source="research_paper",
            metadata={"author": "Qi Heng", "topic": "memory"}
        ),
        RawMemoryChunk(
            content="我决定在记忆引擎中添加情绪评估模块，这很重要！",
            timestamp="2026-03-28T10:05:00",
            source="conversation",
            metadata={"speaker": "assistant", "urgency": "high"}
        ),
        RawMemoryChunk(
            content="根据数据统计，PAD模型由Mehrabian和Russell于1974年提出。",
            timestamp="2026-03-28T10:10:00",
            source="textbook",
            metadata={"page": 45, "subject": "心理学"}
        )
    ]
    
    # 评估记忆
    appraised_memories = []
    for i, raw_memory in enumerate(test_memories):
        print(f"\n处理记忆 #{i+1}...")
        appraised = engine.appraise_memory(raw_memory)
        appraised_memories.append(appraised)
        
        print(f"  类型: {appraised.memory_type} (置信度: {appraised.classification_confidence:.2f})")
        print(f"  情绪强度: {appraised.emotional_intensity:.2f}")
        print(f"  重要性评分: {appraised.significance_score:.2f}")
        print(f"  留存优先级: {appraised.retention_priority:.2f}")
    
    # 显示统计
    print(f"\n{'='*70}")
    print("引擎统计:")
    stats = engine.get_stats()
    print(f"  总评估数: {stats['total_appraised']}")
    print(f"  平均处理时间: {stats['avg_processing_time']:.3f}s")
    
    if 'type_distribution' in stats:
        print(f"  类型分布: {stats['type_distribution']}")

def test_integration_with_existing_engine():
    """测试与现有记忆引擎的集成"""
    print("=" * 70)
    print("测试与现有记忆引擎的集成")
    print("=" * 70)
    
    # 模拟现有记忆引擎的_evaluate_signal方法被替换
    try:
        from emotional_appraisal import EmotionalAppraisalEngine, RawMemoryChunk
        
        # 模拟现有记忆引擎类
        class MockMemoryEngine:
            def __init__(self):
                self.appraisal_engine = EmotionalAppraisalEngine()
            
            def _evaluate_signal(self, chunk):
                """使用情绪评估引擎代替简单的关键词匹配"""
                raw_memory = RawMemoryChunk(
                    content=chunk,
                    timestamp="2026-03-28T10:00:00",
                    source="memory_engine",
                    metadata={"chunk_length": len(chunk)}
                )
                
                appraised = self.appraisal_engine.appraise_memory(raw_memory)
                
                return {
                    "type": appraised.memory_type,
                    "importance": appraised.significance_score,
                    "confidence": appraised.confidence,
                    "emotion": appraised.emotion_scores.to_dict(),
                    "significance": appraised.significance_scores.to_dict(),
                    "retention_priority": appraised.retention_priority
                }
        
        # 测试
        mock_engine = MockMemoryEngine()
        
        test_chunks = [
            "量子计算是下一代计算技术",
            "我需要决定是否学习量子计算",
            "我认为量子计算很有前途"
        ]
        
        for chunk in test_chunks:
            result = mock_engine._evaluate_signal(chunk)
            print(f"块: {chunk[:30]}...")
            print(f"  类型: {result['type']}")
            print(f"  重要性: {result['importance']:.2f}")
            print(f"  置信度: {result['confidence']:.2f}")
            print(f"  留存优先级: {result['retention_priority']:.2f}")
            print()
        
        print("[OK] 集成测试通过")
        
    except Exception as e:
        print(f"[ERROR] 集成测试失败: {e}")

def main():
    """运行所有测试"""
    print("情绪评估模块测试套件")
    print("=" * 70)
    
    tests = [
        ("情绪分析器", test_emotion_analyzer),
        ("重要性评分器", test_significance_scorer),
        ("记忆分类器", test_memory_classifier),
        ("上下文感知", test_context_awareness),
        ("完整引擎", test_full_engine),
        ("集成测试", test_integration_with_existing_engine),
    ]
    
    for name, test_func in tests:
        print(f"\n>>> 开始测试: {name}")
        try:
            test_func()
            print(f"[OK] {name} 测试完成")
        except Exception as e:
            print(f"[ERROR] {name} 测试失败: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 70)
    print("所有测试完成")

if __name__ == "__main__":
    main()