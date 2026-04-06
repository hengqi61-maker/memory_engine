#!/usr/bin/env python3
"""
OpenClawMemoryEngine 完整测试
运行用户提供的完整代码
"""
import os
import sys
import json
import re
import shutil
import numpy as np
from datetime import datetime
from typing import List, Dict, Tuple, Optional
from sklearn.metrics.pairwise import cosine_similarity

print("=" * 70)
print("OpenClawMemoryEngine - 完整功能测试")
print("=" * 70)

# 检查必要的导入
print("\n[1] 导入依赖库...")
try:
    import ollama
    print("  ollama: OK")
except ImportError as e:
    print(f"  ollama: ERROR - {e}")
    sys.exit(1)

try:
    import numpy as np
    print(f"  numpy: OK ({np.__version__})")
except ImportError as e:
    print(f"  numpy: ERROR - {e}")
    sys.exit(1)

try:
    from sklearn.metrics.pairwise import cosine_similarity
    print("  scikit-learn: OK")
except ImportError as e:
    print(f"  scikit-learn: ERROR - {e}")
    sys.exit(1)

# openai是可选的（用于云端评分）
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
    print("  openai: OK")
except ImportError:
    OPENAI_AVAILABLE = False
    print("  openai: 未安装，将使用本地评分")

# ==========================================
# 存储层（完全按照用户代码）
# ==========================================
print("\n[2] 初始化存储层...")

class StorageLayer:
    def __init__(self, base_path: str):
        self.json_path = f"{base_path}.json"
        self.md_path = f"{base_path}.md"
        self.bak_path = f"{base_path}.json.bak"

    def load(self) -> List[Dict]:
        if not os.path.exists(self.json_path):
            return []
        try:
            with open(self.json_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            if os.path.exists(self.bak_path):
                shutil.copy(self.bak_path, self.json_path)
                with open(self.json_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            return []

    def save_atomic(self, data: List[Dict], summary_content: str):
        tmp_path = self.json_path + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        if os.path.exists(self.json_path):
            shutil.copy(self.json_path, self.bak_path)
        
        os.replace(tmp_path, self.json_path)
        
        with open(self.md_path, "w", encoding="utf-8") as f:
            f.write(summary_content)
        print(f"   已保存: {self.json_path} 和 {self.md_path}")

# ==========================================
# 记忆引擎（用户代码 + 零向量修复）
# ==========================================
print("\n[3] 初始化记忆引擎...")

class OpenClawMemoryEngine:
    def __init__(self, memory_name="memory_store", api_key=None, base_url=None):
        # 1. 初始化云端客户端
        self.client = None
        if api_key and OPENAI_AVAILABLE:
            try:
                self.client = OpenAI(api_key=api_key, base_url=base_url)
                print(f"   已初始化OpenAI客户端 (base_url: {base_url})")
            except Exception as e:
                print(f"   OpenAI客户端初始化失败: {e}")
                self.client = None
        else:
            print("   警告: 无API Key或openai不可用，使用本地模式")
        
        # 2. 初始化存储层
        self.storage = StorageLayer(memory_name)
        self.long_term_knowledge = self.storage.load()
        self.short_term_buffer = []
        print(f"   已加载 {len(self.long_term_knowledge)} 条长期记忆")
        
        # 3. 核心参数
        self.lambda_fact = 0.01
        self.temperature = 0.3
        self.debug_mode = True

    # ---------------------------
    # 安全 Embedding（零向量修复）
    # ---------------------------
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
            print(f"   [ERROR] Embedding失败，使用零向量隔离: {e}")
            return np.zeros(768)

    def _is_valid_vector(self, vec: np.ndarray, is_query=False) -> bool:
        if vec is None or len(vec) == 0: 
            return False
        if np.all(vec == 0): 
            return not is_query
        if 0.45 < np.mean(vec) < 0.55 and 0.28 < np.std(vec) < 0.30: 
            return False
        if np.any(np.isnan(vec)) or np.any(np.isinf(vec)): 
            return False
        return True

    # ---------------------------
    # 信息摄入
    # ---------------------------
    def ingest_log_file(self, file_path: str):
        if not os.path.exists(file_path): 
            print(f"   错误: 文件不存在 - {file_path}")
            return
        
        with open(file_path, "r", encoding="utf-8") as f:
            text = f.read()
        
        chunks = re.split(r'\n(?=#{1,4} )', text) 
        chunks = [c.strip() for c in chunks if c.strip()]
        
        print(f"   从文件读取到 {len(chunks)} 个文本块")
        
        for i, chunk in enumerate(chunks):
            metadata = self._evaluate_signal_cloud(chunk)
            vec = self._embed(chunk)
            
            self.short_term_buffer.append({
                "id": f"{datetime.now().strftime('%Y%m%d')}_{i}",
                "content": chunk[:500],
                "vec": vec.tolist(),
                "importance": metadata['importance'],
                "type": metadata['type'],
                "timestamp": datetime.now().isoformat()
            })
        
        print(f"   [OK] {len(chunks)} 条碎片进入短期缓存")

    def _evaluate_signal_cloud(self, chunk: str) -> Dict:
        if self.client:
            try:
                prompt = f"分析日志属性，严格格式 Type|Score (0.1-2.0)。内容: {chunk[:200]}"
                resp = self.client.chat.completions.create(
                    model="deepseek-chat", 
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=15
                )
                match = re.search(r"(\w+)\|([\d\.]+)", resp.choices[0].message.content)
                if match:
                    return {"type": match.group(1).lower(), "importance": float(match.group(2))}
            except Exception as e:
                print(f"   云端评分失败: {e}")
        
        # 本地回退评分
        importance = 0.5
        memory_type = "log"
        
        if any(keyword in chunk for keyword in ["简历", "优化", "工作", "项目"]):
            importance = 0.8
            memory_type = "task"
        elif any(keyword in chunk for keyword in ["GitHub", "代码", "Python", "文件"]):
            importance = 0.7
            memory_type = "code"
        elif any(keyword in chunk for keyword in ["量子", "计算", "物理", "学习"]):
            importance = 0.9
            memory_type = "knowledge"
        
        return {"type": memory_type, "importance": importance}

    # ---------------------------
    # 睡眠周期
    # ---------------------------
    def sleep_cycle(self):
        print("   [SLEEP] 睡眠中：正在清理无用碎屑...")
        
        if not self.short_term_buffer:
            print("   短期缓存为空，跳过睡眠周期")
            return
        
        # 1. 筛选
        survived = self._filter_memories()
        print(f"   筛选后保留 {len(survived)} 条记忆")
        
        # 2. 反思压缩
        new_facts = self._consolidate_reflection(survived)
        
        # 3. 固化
        self.long_term_knowledge.extend(new_facts)
        self.short_term_buffer = []
        
        # 4. 保存
        summary = self._generate_md_summary(self.long_term_knowledge)
        self.storage.save_atomic(self.long_term_knowledge, summary)
        print(f"   [OK] 醒来：已添加 {len(new_facts)} 条新记忆")

    def _filter_memories(self) -> List[Dict]:
        if not self.short_term_buffer: 
            return []
        
        now = datetime.now()
        energies = []
        for m in self.short_term_buffer:
            dt = (now - datetime.fromisoformat(m['timestamp'])).total_seconds() / 3600
            decay = np.exp(-self.lambda_fact * dt)
            energies.append(m['importance'] * decay)
        
        probs = self._softmax(np.array(energies))
        return [m for m, p in zip(self.short_term_buffer, probs) if p > 0.1]

    def _consolidate_reflection(self, memories: List[Dict]) -> List[Dict]:
        if not memories: 
            return []
        
        # 简化压缩：直接使用最重要的一条
        if len(memories) == 1:
            content = memories[0]['content']
        else:
            # 选取重要性最高的
            top_memory = max(memories, key=lambda x: x['importance'])
            content = top_memory['content']
        
        fact_text = f"摘要: {content[:200]}..."
        vec = self._embed(fact_text)
        
        return [{
            "fact": fact_text,
            "vec": vec.tolist(),
            "timestamp": datetime.now().isoformat(),
            "type": "knowledge",
            "confidence": 0.95
        }]

    # ---------------------------
    # 检索
    # ---------------------------
    def retrieve(self, query_text: str, top_k=5, query_type=None, lambda_time=0.01):
        if not self.long_term_knowledge: 
            print(f"   长期记忆为空，无法检索: '{query_text}'")
            return []
        
        query_vec = self._embed(query_text)
        if not self._is_valid_vector(query_vec, is_query=True):
            print("   [WARNING]️ 搜索向量无效")
            return []
        
        mem_vecs = np.array([m['vec'] for m in self.long_term_knowledge])
        similarities = cosine_similarity([query_vec], mem_vecs)[0]
        
        scored_results = []
        now = datetime.now()
        
        for i, mem in enumerate(self.long_term_knowledge):
            type_w = 1.2 if query_type and mem.get('type') == query_type else 0.8
            dt = (now - datetime.fromisoformat(mem['timestamp'])).total_seconds() / 3600
            time_w = np.exp(-lambda_time * dt)
            final_score = similarities[i] * mem.get('confidence', 1.0) * type_w * time_w
            scored_results.append({**mem, "score": final_score})
        
        scored_results.sort(key=lambda x: x['score'], reverse=True)
        
        selected, used_vecs = [], []
        for res in scored_results:
            v = np.array(res['vec'])
            if any(cosine_similarity([v], [uv])[0][0] > 0.9 for uv in used_vecs):
                continue
            selected.append(res)
            used_vecs.append(v)
            if len(selected) >= top_k: 
                break
        
        return selected

    # ---------------------------
    # 辅助方法
    # ---------------------------
    def _softmax(self, x):
        e_x = np.exp(x - np.max(x))
        return e_x / (e_x.sum() + 1e-8)
    
    def _generate_md_summary(self, knowledge: List[Dict]) -> str:
        header = "# 长期记忆摘要\n\n| ID | 事实 | 时间 | 类型 | 置信度 |\n|---|---|---|---|---|\n"
        rows = [f"| {i} | {k.get('fact','')[:60]} | {k['timestamp'][:10]} | {k.get('type','fact')} | {k.get('confidence',1.0):.2f} |" 
                for i, k in enumerate(knowledge)]
        return header + "\n".join(rows)

# ==========================================
# 运行测试
# ==========================================
print("\n[4] 运行测试...")

# 设置存储路径
memory_file = r"C:\Users\Lenovo\.openclaw\workspace\memory\2026-03-25.md"
store_name = "test_run"

# 检查记忆文件
if not os.path.exists(memory_file):
    print(f"   错误: 记忆文件不存在 - {memory_file}")
    sys.exit(1)

print(f"   记忆文件: {memory_file}")
print(f"   存储名称: {store_name}")

# 尝试获取API Key
api_key = None
base_url = "https://api.siliconflow.cn/v1"

print("   尝试从环境变量获取API Key...")
api_key = os.environ.get("DEEPSEEK_API_KEY") or os.environ.get("SILICONFLOW_API_KEY")
if api_key:
    print(f"   使用API Key (前8位): {api_key[:8]}...")
else:
    print("   未找到API Key，使用本地评分模式")

# 初始化引擎
try:
    engine = OpenClawMemoryEngine(
        memory_name=store_name,
        api_key=api_key,
        base_url=base_url
    )
    
    print("\n[5] 测试摄入功能...")
    engine.ingest_log_file(memory_file)
    
    print("\n[6] 测试睡眠周期...")
    engine.sleep_cycle()
    
    print("\n[7] 测试检索功能...")
    test_queries = [
        ("简历", "task"),
        ("GitHub", "code"),
        ("量子", "knowledge"),
        ("工作", None)
    ]
    
    for query, qtype in test_queries:
        print(f"\n   检索: '{query}' (类型: {qtype})")
        results = engine.retrieve(query, top_k=2, query_type=qtype)
        if results:
            for i, res in enumerate(results):
                fact = res.get('fact', res.get('content', ''))
                print(f"     {i+1}. [{res.get('type')}] 分数:{res.get('score',0):.3f}")
                print(f"        {fact[:80]}...")
        else:
            print("     未找到相关记忆")
    
    print("\n" + "=" * 70)
    print("[OK] 测试完成!")
    print(f"   存储位置: {store_name}.json 和 {store_name}.md")
    print("=" * 70)
    
except Exception as e:
    print(f"\n[ERROR] 测试失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)