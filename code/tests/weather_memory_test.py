#!/usr/bin/env python3
"""
测试记忆引擎对天气和技能安装相关记忆的处理
"""
import os
import sys
import json
import numpy as np
from datetime import datetime
from sklearn.metrics.pairwise import cosine_similarity

# 控制台编码设置
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

print("=" * 70)
print("天气记忆文件处理测试")
print("=" * 70)

# 检查依赖
print("\n[1] 检查依赖...")
try:
    import ollama
    print("  ollama: OK")
except ImportError:
    print("  ollama: MISSING")
    sys.exit(1)

try:
    import numpy as np
    print(f"  numpy: OK ({np.__version__})")
except ImportError:
    print("  numpy: MISSING")
    sys.exit(1)

try:
    from sklearn.metrics.pairwise import cosine_similarity
    print("  scikit-learn: OK")
except ImportError:
    print("  scikit-learn: MISSING")
    sys.exit(1)

class WeatherMemoryEngine:
    def __init__(self, memory_name="weather_memory"):
        self.json_path = f"{memory_name}.json"
        self.md_path = f"{memory_name}.md"
        
        # 加载现有记忆
        self.long_term_knowledge = []
        if os.path.exists(self.json_path):
            try:
                with open(self.json_path, "r", encoding="utf-8") as f:
                    self.long_term_knowledge = json.load(f)
                print(f"  已加载 {len(self.long_term_knowledge)} 条现有记忆")
            except Exception as e:
                print(f"  加载记忆失败: {e}")
        
        self.short_term_buffer = []
    
    def _embed(self, text: str) -> np.ndarray:
        try:
            text = text[:8192]
            response = ollama.embeddings(model="nomic-embed-text", prompt=text)
            vec = np.array(response["embedding"])
            norm = np.linalg.norm(vec)
            if norm > 0:
                vec = vec / norm
            return vec
        except Exception as e:
            print(f"  嵌入失败: {e}")
            # 零向量安全隔离
            return np.zeros(768)
    
    def ingest_file(self, file_path: str):
        if not os.path.exists(file_path):
            print(f"  文件不存在: {file_path}")
            return
        
        print(f"  正在处理文件: {file_path}")
        
        with open(file_path, "r", encoding="utf-8") as f:
            text = f.read()
        
        # 分析文件结构：这是一个会话历史记录
        # 分割为不同的消息块
        lines = text.split('\n')
        sections = []
        current_section = []
        
        # 基于标题和用户/助手标记来分割
        for line in lines:
            if line.strip().startswith('user: [') or line.strip().startswith('assistant: ['):
                if current_section:
                    sections.append('\n'.join(current_section))
                    current_section = []
            current_section.append(line)
        
        if current_section:
            sections.append('\n'.join(current_section))
        
        print(f"  从文件解析出 {len(sections)} 个对话部分")
        
        # 对每个部分进行处理
        processed_count = 0
        for i, section in enumerate(sections):
            if not section.strip():
                continue
            
            # 提取关键信息类型
            memory_type = "conversation"
            importance = 0.5
            
            content_lower = section.lower()
            
            # 根据内容判断类型和重要性
            if "weather" in content_lower or "天气" in content_lower or "wttr.in" in content_lower:
                memory_type = "weather_info"
                importance = 0.8
            elif "skill" in content_lower or "安装" in content_lower or "clawhub" in content_lower:
                memory_type = "skill_installation"
                importance = 0.9
            elif "pdf" in content_lower or "文档" in content_lower:
                memory_type = "pdf_processing"
                importance = 0.85
            elif "permission" in content_lower or "授权" in content_lower or "权限" in content_lower:
                memory_type = "security_discussion"
                importance = 0.9
            
            # 生成嵌入向量
            vec = self._embed(section)
            
            # 添加到短期缓存
            self.short_term_buffer.append({
                "id": f"section_{i}",
                "content": section[:400],  # 截取部分内容
                "vec": vec.tolist(),
                "importance": importance,
                "type": memory_type,
                "timestamp": datetime.now().isoformat()
            })
            
            processed_count += 1
            if processed_count % 5 == 0:
                print(f"  已处理 {processed_count} 个部分")
        
        print(f"  已添加 {len(self.short_term_buffer)} 条记忆到短期缓存")
    
    def consolidate_memories(self):
        """将短期记忆合并为长期记忆"""
        if not self.short_term_buffer:
            print("  短期缓存为空，无需合并")
            return
        
        print(f"  正在合并 {len(self.short_term_buffer)} 条短期记忆...")
        
        # 按类型分组
        type_groups = {}
        for mem in self.short_term_buffer:
            mem_type = mem['type']
            if mem_type not in type_groups:
                type_groups[mem_type] = []
            type_groups[mem_type].append(mem)
        
        # 为每个组生成摘要
        for mem_type, memories in type_groups.items():
            if not memories:
                continue
            
            # 选择重要性最高的记忆作为代表
            top_memory = max(memories, key=lambda x: x['importance'])
            
            # 生成摘要
            summary_content = f"[{mem_type}] 摘要: {top_memory['content'][:150]}..."
            
            # 使用原始向量或重新嵌入
            if 'vec' in top_memory:
                vec = np.array(top_memory['vec'])
            else:
                vec = self._embed(summary_content)
            
            # 添加到长期记忆
            self.long_term_knowledge.append({
                "fact": summary_content,
                "vec": vec.tolist(),
                "timestamp": datetime.now().isoformat(),
                "type": mem_type,
                "confidence": 0.95,
                "source": "weather_fallback_conversation"
            })
        
        print(f"  生成了 {len(type_groups)} 类长期记忆")
        self.short_term_buffer = []
    
    def save(self):
        """保存记忆到文件"""
        if not self.long_term_knowledge:
            print("  无长期记忆需要保存")
            return
        
        # 保存JSON
        with open(self.json_path, "w", encoding="utf-8") as f:
            json.dump(self.long_term_knowledge, f, indent=2, ensure_ascii=False)
        
        # 保存Markdown摘要
        header = "# 天气会话记忆摘要\n\n"
        header += f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        header += "| ID | 类型 | 摘要内容 | 置信度 |\n|---|---|---|---|\n"
        
        rows = []
        for i, mem in enumerate(self.long_term_knowledge):
            fact = mem.get('fact', '')[:100]
            mem_type = mem.get('type', 'unknown')
            confidence = mem.get('confidence', 0)
            rows.append(f"| {i} | {mem_type} | {fact}... | {confidence:.2f} |")
        
        with open(self.md_path, "w", encoding="utf-8") as f:
            f.write(header + "\n".join(rows))
        
        print(f"  已保存到: {self.json_path}")
        print(f"  摘要文件: {self.md_path}")
    
    def search(self, query: str, min_score=0.3):
        """搜索记忆"""
        if not self.long_term_knowledge:
            print(f"  长期记忆为空，无法搜索: '{query}'")
            return []
        
        query_vec = self._embed(query)
        
        results = []
        for mem in self.long_term_knowledge:
            if 'vec' in mem:
                try:
                    mem_vec = np.array(mem['vec'])
                    similarity = cosine_similarity([query_vec], [mem_vec])[0][0]
                    
                    # 类型匹配加分
                    type_bonus = 1.0
                    if 'weather' in query.lower() and mem.get('type') == 'weather_info':
                        type_bonus = 1.3
                    elif 'skill' in query.lower() and mem.get('type') == 'skill_installation':
                        type_bonus = 1.3
                    elif 'pdf' in query.lower() and mem.get('type') == 'pdf_processing':
                        type_bonus = 1.3
                    
                    confidence = mem.get('confidence', 0.5)
                    final_score = similarity * confidence * type_bonus
                    
                    if final_score >= min_score:
                        results.append({
                            "content": mem.get('fact', ''),
                            "score": final_score,
                            "similarity": similarity,
                            "type": mem.get('type', 'unknown'),
                            "confidence": confidence
                        })
                except Exception as e:
                    print(f"  计算相似度错误: {e}")
        
        results.sort(key=lambda x: x['score'], reverse=True)
        return results[:5]

# 主测试逻辑
print("\n[2] 初始化记忆引擎...")
engine = WeatherMemoryEngine("weather_test_output")

print("\n[3] 处理天气记忆文件...")
weather_file = r"C:\Users\Lenovo\.openclaw\workspace\memory\2026-03-02-weather-fallback.md"
engine.ingest_file(weather_file)

print("\n[4] 合并记忆...")
engine.consolidate_memories()

print("\n[5] 保存记忆...")
engine.save()

print("\n[6] 测试搜索功能...")
test_queries = [
    "天气查询",
    "wttr.in 服务",
    "安装Skill失败",
    "PDF处理技能",
    "权限授权讨论",
    "ClawHub安装问题",
    "天气技能替代方案"
]

for query in test_queries:
    print(f"\n  搜索: '{query}'")
    results = engine.search(query)
    if results:
        for i, res in enumerate(results):
            print(f"    {i+1}. [{res['type']}] 分数:{res['score']:.3f}")
            print(f"        {res['content'][:80]}...")
    else:
        print("    未找到相关记忆")

print("\n[7] 显示生成的文件信息...")
if os.path.exists("weather_test_output.json"):
    with open("weather_test_output.json", "r", encoding="utf-8") as f:
        data = json.load(f)
        print(f"  JSON文件: weather_test_output.json")
        print(f"    包含 {len(data)} 条长期记忆")
        
        # 按类型统计
        type_counts = {}
        for mem in data:
            mem_type = mem.get('type', 'unknown')
            type_counts[mem_type] = type_counts.get(mem_type, 0) + 1
        
        print("    类型分布:")
        for mem_type, count in type_counts.items():
            print(f"      {mem_type}: {count}条")

if os.path.exists("weather_test_output.md"):
    with open("weather_test_output.md", "r", encoding="utf-8") as f:
        lines = f.readlines()
        print(f"  Markdown文件: weather_test_output.md")
        print(f"    行数: {len(lines)}")
        if lines:
            print("    前5行:")
            for line in lines[:5]:
                print(f"      {line.rstrip()}")

print("\n" + "=" * 70)
print("[OK] 天气记忆文件测试完成!")
print("=" * 70)