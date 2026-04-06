#!/usr/bin/env python3
"""测试情绪评估模块"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'code', 'modules'))

try:
    from emotional_appraisal import EmotionAnalyzer
    analyzer = EmotionAnalyzer()
    print("[OK] 导入成功")
    
    # 测试中文情绪分析
    text = "这是一个测试句子"
    result = analyzer.analyze_emotion(text)
    print(f"[完成] 情感分析结果: valence={result['valence']:.2f}, arousal={result['arousal']:.2f}, dominance={result['dominance']:.2f}")
    
    # 测试SnowNLP可用性
    try:
        analyzer.analyze_emotion("中文测试")
        print("[完成] SnowNLP 可用")
    except Exception as e:
        print(f"[ERROR] SnowNLP 错误: {e}")
    
    # 测试重要性评估
    result = analyzer.evaluate_importance(text)
    print(f"[完成] 重要性评估: personal_relevance={result['personal_relevance']:.2f}, task_utility={result['task_utility']:.2f}")
    
    # 测试记忆分类
    result = analyzer.classify_memory_type(result['personal_relevance'], result['task_utility'])
    print(f"[完成] 记忆分类: {result}")
    
except ImportError as e:
    print(f"[ERROR] 导入失败: {e}")
except Exception as e:
    print(f"[ERROR] 测试失败: {e}")
    import traceback
    traceback.print_exc()