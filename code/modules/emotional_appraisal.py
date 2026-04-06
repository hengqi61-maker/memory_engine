#!/usr/bin/env python3
"""
情绪评估模块 (Emotional Appraisal Module)
基于PAD模型和扩展重要性维度进行情绪属性评估
"""

import re
from typing import Dict, List, Optional, Tuple
import math


class EmotionAnalyzer:
    """情绪分析器，基于PAD模型计算愉悦度、唤醒度、支配度"""
    
    def __init__(self, use_snownlp: bool = True):
        """
        初始化情绪分析器
        
        Args:
            use_snownlp: 是否使用SnowNLP进行情感分析（如可用）
        """
        self.use_snownlp = use_snownlp
        self.snownlp_available = False
        
        # 尝试导入SnowNLP
        if use_snownlp:
            try:
                from snownlp import SnowNLP
                self.SnowNLP = SnowNLP
                self.snownlp_available = True
                print("[INFO] SnowNLP 可用，使用高级情绪分析")
            except ImportError:
                print("[WARN] SnowNLP 不可用，将使用基于规则的情绪分析")
                self.snownlp_available = False
        
        # 中文情绪词典（简化版）
        self.positive_words = [
            "好", "成功", "快乐", "高兴", "满意", "喜欢", "开心", "兴奋",
            "棒", "优秀", "完美", "美好", "幸福", "乐观", "积极", "赞"
        ]
        self.negative_words = [
            "坏", "失败", "悲伤", "生气", "不满", "讨厌", "糟糕", "痛苦",
            "困难", "问题", "错误", "失望", "愤怒", "消极", "悲观", "差"
        ]
        self.arousal_words = [
            "紧急", "重要", "立刻", "马上", "危险", "赶紧", "立即", "迅速",
            "非常", "极其", "特别", "紧急", "重大", "关键", "紧急", "急"
        ]
        self.dominance_words = [
            "必须", "应该", "要", "需要", "务必", "一定", "肯定", "保证",
            "确保", "负责", "控制", "主导", "管理", "领导", "指挥", "决定"
        ]
        
        # 权重配置
        self.config = {
            "valence_weight": 0.4,      # 愉悦度权重
            "arousal_weight": 0.3,       # 唤醒度权重  
            "dominance_weight": 0.3,     # 支配度权重
            "intensity_threshold": 0.3,  # 情绪强度阈值
        }
    
    def analyze(self, text: str) -> Dict[str, float]:
        """
        分析文本情绪，返回PAD三维情绪分数
        
        Args:
            text: 输入文本
            
        Returns:
            包含情绪维度分数的字典:
            - valence: 愉悦度 [-1, 1]，负数为负面情绪，正数为正面情绪
            - arousal: 唤醒度 [0, 1]，越高表示情绪越激动
            - dominance: 支配度 [0, 1]，越高表示控制感越强
            - intensity: 情绪强度 [0, 1]
            - overall_emotion: 整体情绪分类 ("positive", "negative", "neutral")
        """
        # 基础情绪分析
        if self.snownlp_available:
            valence = self._analyze_valence_snownlp(text)
        else:
            valence = self._analyze_valence_rule(text)
        
        arousal = self._analyze_arousal(text)
        dominance = self._analyze_dominance(text)
        
        # 计算情绪强度
        intensity = self._calculate_intensity(valence, arousal, dominance)
        
        # 整体情绪分类
        overall_emotion = self._classify_overall_emotion(valence, intensity)
        
        return {
            "valence": max(-1.0, min(1.0, valence)),
            "arousal": max(0.0, min(1.0, arousal)),
            "dominance": max(0.0, min(1.0, dominance)),
            "intensity": max(0.0, min(1.0, intensity)),
            "overall_emotion": overall_emotion,
            "positive_score": max(0.0, valence) if valence > 0 else 0.0,
            "negative_score": abs(min(0.0, valence)) if valence < 0 else 0.0,
        }
    
    def _analyze_valence_snownlp(self, text: str) -> float:
        """使用SnowNLP分析情感倾向（愉悦度）"""
        try:
            s = self.SnowNLP(text)
            # SnowNLP返回0-1之间的情感分数，0为负面，1为正面
            sentiment = s.sentiments  # 0-1
            
            # 转换为-1到1的范围
            valence = (sentiment - 0.5) * 2  # -1到1
            return valence
        except Exception as e:
            print(f"[WARN] SnowNLP分析失败: {e}，回退到基于规则的方法")
            return self._analyze_valence_rule(text)
    
    def _analyze_valence_rule(self, text: str) -> float:
        """基于规则的情感分析（愉悦度）"""
        text_lower = text.lower()
        
        # 正面关键词计分
        positive_count = sum(1 for word in self.positive_words if word in text_lower)
        positive_score = positive_count / max(len(self.positive_words), 1)
        
        # 负面关键词计分
        negative_count = sum(1 for word in self.negative_words if word in text_lower)
        negative_score = negative_count / max(len(self.negative_words), 1)
        
        # 计算净愉悦度
        valence = positive_score - negative_score
        
        # 限制在[-1, 1]范围内
        return max(-1.0, min(1.0, valence))
    
    def _analyze_arousal(self, text: str) -> float:
        """分析唤醒度"""
        text_lower = text.lower()
        
        # 1. 关键词匹配
        arousal_count = sum(1 for word in self.arousal_words if word in text_lower)
        keyword_score = arousal_count / max(len(self.arousal_words), 1)
        
        # 2. 标点符号分析（感叹号、问号）
        exclamation_count = text.count('!') + text.count('！')
        question_count = text.count('?') + text.count('？')
        punctuation_score = min(1.0, (exclamation_count + question_count) / 5.0)
        
        # 3. 大写字母分析（中文不适用，留作扩展）
        uppercase_score = 0.0
        
        # 4. 副词强度词（非常、极其等）
        intensity_adverbs = ["非常", "极其", "特别", "十分", "极其", "超级", "超"]
        adverb_count = sum(1 for adv in intensity_adverbs if adv in text)
        adverb_score = min(1.0, adverb_count / 3.0)
        
        # 综合唤醒度
        arousal = 0.4 * keyword_score + 0.3 * punctuation_score + 0.2 * adverb_score + 0.1 * uppercase_score
        return max(0.0, min(1.0, arousal))
    
    def _analyze_dominance(self, text: str) -> float:
        """分析支配度"""
        text_lower = text.lower()
        
        # 1. 支配关键词匹配
        dominance_count = sum(1 for word in self.dominance_words if word in text_lower)
        keyword_score = dominance_count / max(len(self.dominance_words), 1)
        
        # 2. 句子结构分析（命令式、祈使句）
        command_patterns = [
            r'必须[^。，；！？]*[。！？]',
            r'应该[^。，；！？]*[。！？]',
            r'要[^。，；！？]*[。！？]',
            r'需要[^。，；！？]*[。！？]',
            r'务必[^。，；！？]*[。！？]',
        ]
        command_count = sum(1 for pattern in command_patterns if re.search(pattern, text))
        command_score = min(1.0, command_count / 3.0)
        
        # 3. 第一人称使用（"我"、"我们"指示控制感）
        first_person_words = ["我", "我们", "本人", "自己"]
        first_person_count = sum(1 for word in first_person_words if word in text)
        first_person_score = min(1.0, first_person_count / 5.0)
        
        # 综合支配度
        dominance = 0.5 * keyword_score + 0.3 * command_score + 0.2 * first_person_score
        return max(0.0, min(1.0, dominance))
    
    def _calculate_intensity(self, valence: float, arousal: float, dominance: float) -> float:
        """计算情绪强度"""
        # 基于PAD三维向量的范数
        intensity = math.sqrt(valence**2 + arousal**2 + dominance**2) / math.sqrt(3.0)
        return max(0.0, min(1.0, intensity))
    
    def _classify_overall_emotion(self, valence: float, intensity: float) -> str:
        """分类整体情绪"""
        if intensity < self.config["intensity_threshold"]:
            return "neutral"
        elif valence > 0.1:
            return "positive"
        elif valence < -0.1:
            return "negative"
        else:
            return "neutral"


class SignificanceScorer:
    """重要性评分器，基于扩展维度计算记忆重要性"""
    
    def __init__(self):
        # 权重配置（可调整）
        self.weights = {
            "personal_relevance": 0.30,   # 个人相关性
            "task_utility": 0.25,        # 任务效用
            "social_value": 0.20,        # 社会价值
            "novelty": 0.15,             # 新颖性
            "complexity": 0.10,          # 复杂性（负权重）
        }
        
        # 启发式规则
        self.rules = {
            "quantum_keywords": ["量子", "计算", "信息", "算法", "比特", "门"],
            "project_keywords": ["项目", "任务", "目标", "计划", "进度"],
            "error_keywords": ["错误", "问题", "失败", "修复", "调试"],
            "todo_keywords": ["TODO", "FIXME", "待办", "待处理", "待办事项"],
        }
    
    def score(self, text: str, emotion_scores: Dict[str, float]) -> float:
        """
        计算记忆的重要性分数
        
        Args:
            text: 记忆文本
            emotion_scores: 情绪分析结果
            
        Returns:
            重要性分数 [0, 1]
        """
        # 1. 情绪强度贡献
        emotional_contribution = emotion_scores.get("intensity", 0.0) * 0.4
        
        # 2. 扩展维度贡献
        extended_score = self._calculate_extended_score(text)
        
        # 3. 上下文规则贡献
        rule_score = self._apply_rules(text)
        
        # 加权综合重要性
        importance = (
            emotional_contribution * 0.4 +
            extended_score * 0.5 +
            rule_score * 0.1
        )
        
        return max(0.0, min(1.0, importance))
    
    def _calculate_extended_score(self, text: str) -> float:
        """计算扩展维度分数"""
        # 简化启发式实现
        text_lower = text.lower()
        
        # 个人相关性（基于第一人称出现频率）
        personal_words = ["我", "我们", "自己", "个人", "我的"]
        personal_count = sum(1 for word in personal_words if word in text_lower)
        personal_relevance = min(1.0, personal_count / 5.0)
        
        # 任务效用（基于任务相关关键词）
        task_words = ["任务", "项目", "工作", "目标", "计划", "执行"]
        task_count = sum(1 for word in task_words if word in text_lower)
        task_utility = min(1.0, task_count / 5.0)
        
        # 社会价值（基于社会性词语）
        social_words = ["社会", "文化", "道德", "伦理", "价值", "意义"]
        social_count = sum(1 for word in social_words if word in text_lower)
        social_value = min(1.0, social_count / 5.0)
        
        # 新颖性（基于独特词密度 - 简化处理）
        total_words = len(text)
        unique_words = len(set(text_lower.split()))
        novelty = min(1.0, unique_words / max(total_words, 1)) if total_words > 0 else 0.0
        
        # 复杂性（基于句子长度和专业术语）
        sentence_length = len(text)
        complexity = min(1.0, sentence_length / 200.0)  # 假设200字符为高复杂性
        
        # 加权平均
        extended_score = (
            personal_relevance * self.weights["personal_relevance"] +
            task_utility * self.weights["task_utility"] +
            social_value * self.weights["social_value"] +
            novelty * self.weights["novelty"] -
            complexity * self.weights["complexity"]
        )
        
        return max(0.0, min(1.0, extended_score))
    
    def _apply_rules(self, text: str) -> float:
        """应用启发式规则"""
        text_lower = text.lower()
        rule_score = 0.0
        
        # 量子计算关键词（对用户高度相关）
        if any(keyword in text_lower for keyword in self.rules["quantum_keywords"]):
            rule_score = max(rule_score, 0.8)
        
        # 项目相关关键词
        if any(keyword in text_lower for keyword in self.rules["project_keywords"]):
            rule_score = max(rule_score, 0.7)
        
        # 错误和待办事项
        if any(keyword in text_lower for keyword in self.rules["error_keywords"]):
            rule_score = max(rule_score, 0.9)
        
        if any(keyword in text_lower for keyword in self.rules["todo_keywords"]):
            rule_score = max(rule_score, 1.0)
        
        return rule_score


class MemoryClassifier:
    """记忆分类器"""
    
    def __init__(self):
        self.type_patterns = {
            "fact": ["事实", "数据", "统计", "日期", "时间", "地点", "定义"],
            "decision": ["决定", "选择", "决策", "评估", "判断", "结论"],
            "opinion": ["观点", "看法", "认为", "觉得", "评价", "偏好"],
            "instruction": ["步骤", "流程", "指南", "指令", "方法", "如何"],
            "experience": ["经历", "体验", "故事", "回忆", "事件", "发生"],
            "code": ["代码", "函数", "类", "模块", "算法", "编程"],
            "log": ["日志", "记录", "报告", "调试", "错误", "异常"],
        }
    
    def classify(self, text: str) -> str:
        """分类记忆类型"""
        text_lower = text.lower()
        scores = {}
        
        for memory_type, patterns in self.type_patterns.items():
            score = sum(1 for pattern in patterns if pattern in text_lower)
            scores[memory_type] = score
        
        # 找出最高分数的类型
        if scores:
            best_type = max(scores.items(), key=lambda x: x[1])[0]
            if scores[best_type] > 0:
                return best_type
        
        return "unknown"


def create_emotion_analyzer(mode: str = 'hybrid') -> EmotionAnalyzer:
    """
    创建情绪分析器
    
    Args:
        mode: 分析模式 ('hybrid', 'rule', 'snownlp')
    """
    if mode == 'snownlp':
        return EmotionAnalyzer(use_snownlp=True)
    elif mode == 'rule':
        return EmotionAnalyzer(use_snownlp=False)
    else:  # hybrid
        return EmotionAnalyzer(use_snownlp=True)


# 示例使用
if __name__ == "__main__":
    # 测试情绪分析器
    analyzer = create_emotion_analyzer('hybrid')
    scorer = SignificanceScorer()
    classifier = MemoryClassifier()
    
    test_texts = [
        "我今天非常高兴，量子计算项目取得了重大突破！",
        "系统出现了一个严重错误，需要立即修复。",
        "根据数据统计，用户满意度达到95%。",
        "我认为应该采用这个算法，它效率更高。",
    ]
    
    for text in test_texts:
        print(f"\n文本: {text}")
        emotion_scores = analyzer.analyze(text)
        print(f"  情绪分析: {emotion_scores}")
        
        importance = scorer.score(text, emotion_scores)
        print(f"  重要性分数: {importance:.3f}")
        
        memory_type = classifier.classify(text)
        print(f"  记忆类型: {memory_type}")