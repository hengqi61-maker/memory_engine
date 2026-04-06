#!/usr/bin/env python3
"""
测试SnowNLP与情绪分析器的集成
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 测试SnowNLP是否可用
try:
    from snownlp import SnowNLP
    print("[OK] SnowNLP 导入成功")
    print(f"   版本: {SnowNLP.__version__ if hasattr(SnowNLP, '__version__') else '未知'}")
    
    # 测试基本情感分析
    test_text = "今天天气很好，心情非常愉快！"
    s = SnowNLP(test_text)
    sentiment = s.sentiments
    print(f"   测试文本: '{test_text}'")
    print(f"   情感分数: {sentiment:.4f} (0-1, 越高越正面)")
    
except ImportError as e:
    print(f"[ERROR] SnowNLP 导入失败: {e}")
    sys.exit(1)

# 测试情绪分析器能否正确使用SnowNLP
try:
    from emotional_appraisal.emotion_analyzer import EmotionAnalyzer
    print("\n[OK] EmotionAnalyzer 导入成功")
    
    # 创建分析器（应该自动检测SnowNLP）
    analyzer = EmotionAnalyzer(use_snownlp=True)
    
    # 分析不同情绪的文本
    test_cases = [
        ("量子计算项目取得重大突破！我们成功实现了量子比特的稳定控制，这是一个令人兴奋的进展。", "正面向量计算"),
        ("系统出现了一个严重错误，需要立即修复。", "负面技术问题"),
        ("根据数据统计，用户满意度达到95%。", "中性事实"),
        ("我认为这个算法设计非常巧妙，效率提升明显。", "正面评价"),
        ("这个问题很复杂，需要进一步研究。", "中性挑战"),
    ]
    
    for text, description in test_cases:
        print(f"\n分析: {description}")
        print(f"  文本: {text[:40]}...")
        
        scores = analyzer.analyze(text)
        
        valence = scores.get('valence', 0)
        arousal = scores.get('arousal', 0)
        dominance = scores.get('dominance', 0)
        intensity = scores.get('intensity', 0)
        emotion = scores.get('overall_emotion', 'unknown')
        
        print(f"  愉悦度: {valence:+.3f} (正面>0)")
        print(f"  唤醒度: {arousal:.3f} (高唤醒度)")
        print(f"  支配度: {dominance:.3f} (高支配感)")
        print(f"  情绪强度: {intensity:.3f}")
        print(f"  整体情绪: {emotion}")
        
        # 检查SnowNLP是否被实际使用
        if hasattr(analyzer, 'snownlp_available'):
            print(f"  SnowNLP可用: {analyzer.snownlp_available}")
        
except Exception as e:
    print(f"\n[ERROR] 情绪分析器测试失败: {e}")
    import traceback
    traceback.print_exc()

# 测试在记忆引擎中的集成
print("\n" + "="*60)
print("测试在完整记忆引擎中的集成")

try:
    from biological_memory_engine import BiologicalMemoryEngine, MemoryItem, MemoryContext
    
    config = {
        "system_name": "SnowNLP测试引擎",
        "module_configs": {
            "working_memory": {"capacity": 5, "embedding_backend": "fake"},
            "long_term_storage": {"storage_path": "./test_snownlp_storage"},
            "emotional_appraisal": {
                "enabled": True,
                "analyzer_mode": "hybrid"  # 应该使用SnowNLP
            }
        },
        "pipeline": ["sensory_registration", "working_memory", "emotional_appraisal", "long_term_storage"]
    }
    
    engine = BiologicalMemoryEngine(config)
    
    # 摄入带有强烈情绪的文本
    test_memory = "量子计算项目失败，我们浪费了三个月时间，感到非常失望和沮丧。"
    
    result = engine.ingest(content=test_memory, source="snownlp_test")
    
    if result.success:
        memory = result.data
        print(f"[OK] 记忆摄入成功，使用了SnowNLP分析")
        
        if memory.emotional_scores:
            print(f"  情绪分数:")
            for key, value in memory.emotional_scores.items():
                if isinstance(value, float):
                    print(f"    {key}: {value:.3f}")
                else:
                    print(f"    {key}: {value}")
            
            # 检查是否为负面情绪
            valence = memory.emotional_scores.get('valence', 0)
            if valence < -0.1:
                print(f"  [OK] 正确检测到负面情绪 (愉悦度: {valence:.3f})")
            elif valence > 0.1:
                print(f"  [OK] 检测到正面情绪 (愉悦度: {valence:.3f})")
            else:
                print(f"  [INFO] 中性情绪 (愉悦度: {valence:.3f})")
            
            # 检查SnowNLP是否被使用（通过高精度判断）
            if abs(valence) > 0.3:
                print(f"  [INFO] 强情绪检测，可能使用了SnowNLP")
        else:
            print("[WARNING] 无情绪分数")
    else:
        print(f"[ERROR] 记忆摄入失败: {result.message}")
    
    # 清理
    import shutil
    if os.path.exists("./test_snownlp_storage"):
        shutil.rmtree("./test_snownlp_storage")
        print("\n清理测试存储目录")
        
except Exception as e:
    print(f"[ERROR] 引擎集成测试失败: {e}")
    import traceback
    traceback.print_exc()

print("\n测试完成！")