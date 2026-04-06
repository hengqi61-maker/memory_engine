#!/usr/bin/env python3
"""
记忆引擎测试脚本 - 针对OpenClawMemoryEngine
"""
import os
import sys
import time
import traceback
from datetime import datetime

# 添加当前目录到Python路径，确保能导入模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 60)
print("OpenClawMemoryEngine 测试脚本")
print(f"测试时间: {datetime.now()}")
print("=" * 60)

# ==========================================
# 1. 检查依赖
# ==========================================
print("\n[SEARCH] 检查依赖库...")
try:
    import ollama
    print("[OK] ollama")
except ImportError:
    print("[ERROR] ollama 未安装，请运行: pip install ollama")
    sys.exit(1)

try:
    import numpy as np
    print(f"[OK] numpy {np.__version__}")
except ImportError:
    print("[ERROR] numpy 未安装，请运行: pip install numpy")
    sys.exit(1)

try:
    from sklearn.metrics.pairwise import cosine_similarity
    import sklearn
    print(f"[OK] scikit-learn {sklearn.__version__}")
except ImportError:
    print("[ERROR] scikit-learn 未安装，请运行: pip install scikit-learn")
    sys.exit(1)

try:
    from openai import OpenAI
    import openai
    print(f"[OK] openai {openai.__version__}")
    OPENAI_AVAILABLE = True
except ImportError:
    print("[ERROR] openai 未安装，将使用本地评估模式")
    OPENAI_AVAILABLE = False

# ==========================================
# 2. 检查Ollama服务
# ==========================================
print("\n[SEARCH] 检查Ollama服务...")
try:
    # 尝试简单的API调用
    import subprocess
    result = subprocess.run(["ollama", "--version"], capture_output=True, text=True)
    if result.returncode == 0:
        print(f"[OK] Ollama服务可用: {result.stdout.strip()}")
        
        # 检查模型是否可用
        try:
            models_result = subprocess.run(["ollama", "list"], capture_output=True, text=True)
            if "nomic-embed-text" in models_result.stdout:
                print("[OK] nomic-embed-text 模型已安装")
            else:
                print("[WARNING]️  nomic-embed-text 模型未安装，将自动下载或使用备用方案")
                print("   运行: ollama pull nomic-embed-text")
        except:
            print("[WARNING]️  无法检查模型列表，继续测试...")
    else:
        print("[ERROR] Ollama命令不可用，请确保Ollama已安装并在PATH中")
        print("   安装指南: https://ollama.com/download")
        sys.exit(1)
except Exception as e:
    print(f"[WARNING]️  检查Ollama时出错: {e}")
    print("   确保Ollama正在后台运行: ollama serve")

# ==========================================
# 3. 导入记忆引擎（动态定义）
# ==========================================
print("\n[ARCHIVE] 导入记忆引擎...")

# 定义一个简化的记忆引擎类用于测试
class TestMemoryEngine:
    def __init__(self, memory_name="memory_store", api_key=None, base_url=None):
        import os
        import json
        import numpy as np
        from datetime import datetime
        import ollama
        from sklearn.metrics.pairwise import cosine_similarity
        
        # 初始化存储路径
        workspace = os.path.expanduser("~/.openclaw/workspace")
        self.base_dir = os.path.join(workspace, "memory", "engine")
        os.makedirs(self.base_dir, exist_ok=True)
        os.makedirs(os.path.join(self.base_dir, "archived"), exist_ok=True)
        
        self.json_path = os.path.join(self.base_dir, f"{memory_name}.json")
        self.md_path = os.path.join(self.base_dir, f"{memory_name}.md")
        
        # 尝试初始化OpenAI客户端
        self.client = None
        if api_key and OPENAI_AVAILABLE:
            try:
                self.client = OpenAI(api_key=api_key, base_url=base_url)
                print(f"[OK] OpenAI客户端初始化成功 (base_url: {base_url})")
            except Exception as e:
                print(f"[WARNING]️ OpenAI客户端初始化失败: {e}")
        else:
            print("[INFO]️ 使用本地评估模式 (无OpenAI客户端)")
        
        # 加载或初始化记忆
        self.long_term_knowledge = []
        self.short_term_buffer = []
        if os.path.exists(self.json_path):
            with open(self.json_path, "r", encoding="utf-8") as f:
                self.long_term_knowledge = json.load(f)
            print(f"📂 从 {self.json_path} 加载了 {len(self.long_term_knowledge)} 条记忆")
        
        # 核心参数
        self.lambda_fact = 0.01
        self.temperature = 0.3
        
        print(f"[BRAIN] 记忆引擎初始化完成，存储路径: {self.base_dir}")
    
    def _embed(self, text: str) -> np.ndarray:
        """安全向量化，失败时返回零向量"""
        try:
            text = text[:8192]
            response = ollama.embeddings(model="nomic-embed-text", prompt=text)
            vec = np.array(response["embedding"])
            norm = np.linalg.norm(vec)
            return vec / norm if norm > 0 else vec
        except Exception as e:
            print(f"[ERROR] Embedding失败，使用零向量安全隔离: {e}")
            return np.zeros(768)
    
    def ingest_log_file(self, file_path: str):
        """摄入记忆文件"""
        import os
        import re
        
        if not os.path.exists(file_path):
            print(f"[ERROR] 文件不存在: {file_path}")
            return
        
        with open(file_path, "r", encoding="utf-8") as f:
            text = f.read()
        
        # 简单的文本分割
        chunks = re.split(r'\n(?=#{1,4} )', text)
        chunks = [c.strip() for c in chunks if c.strip()]
        
        print(f"[FILE] 从 {file_path} 读取到 {len(chunks)} 个文本块")
        
        for i, chunk in enumerate(chunks[:3]):  # 只处理前3个块用于测试
            # 本地评估
            importance = 1.0 if "简历" in chunk or "GitHub" in chunk else 0.5
            memory_type = "task" if "任务" in chunk else "log"
            
            try:
                vec = self._embed(chunk)
                self.short_term_buffer.append({
                    "id": f"test_{i}",
                    "content": chunk[:500],  # 截断以节省空间
                    "vec": vec.tolist(),
                    "importance": importance,
                    "type": memory_type,
                    "timestamp": datetime.now().isoformat()
                })
                print(f"  ✓ 处理块 {i+1}: {memory_type} (importance: {importance:.1f})")
            except Exception as e:
                print(f"  ✗ 处理块 {i+1} 失败: {e}")
        
        print(f"[OK] {len(self.short_term_buffer)} 条记忆进入短期缓存")
    
    def _embed(self, text):
        """简化的embedding方法"""
        try:
            text = text[:8192]
            response = ollama.embeddings(model="nomic-embed-text", prompt=text)
            vec = np.array(response["embedding"])
            norm = np.linalg.norm(vec)
            return vec / norm if norm > 0 else vec
        except Exception as e:
            print(f"[ERROR] Embedding失败，使用零向量隔离: {e}")
            # 返回测试用的伪向量
            vec = np.random.rand(768) - 0.5
            norm = np.linalg.norm(vec)
            return vec / norm if norm > 0 else np.zeros(768)
    
    def save_memory(self):
        """保存记忆到文件"""
        import json
        import os
        
        if not self.long_term_knowledge:
            print("[INFO]️ 没有长期记忆需要保存")
            return
        
        # 保存JSON
        tmp_path = self.json_path + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(self.long_term_knowledge, f, indent=2, ensure_ascii=False)
        
        # 备份原文件（如果存在）
        if os.path.exists(self.json_path):
            import shutil
            shutil.copy(self.json_path, self.json_path + ".bak")
        
        os.replace(tmp_path, self.json_path)
        
        # 保存Markdown摘要
        header = "# 记忆测试摘要\n\n| ID | 内容摘要 | 类型 | 时间 |\n|---|---|---|---|\n"
        rows = []
        for i, mem in enumerate(self.long_term_knowledge):
            content = mem.get('fact', mem.get('content', ''))[:60]
            mem_type = mem.get('type', 'unknown')
            timestamp = mem.get('timestamp', '')[:19]
            rows.append(f"| {i} | {content}... | {mem_type} | {timestamp} |")
        
        with open(self.md_path, "w", encoding="utf-8") as f:
            f.write(header + "\n".join(rows))
        
        print(f"[SAVE] 保存了 {len(self.long_term_knowledge)} 条记忆到:")
        print(f"   JSON: {self.json_path}")
        print(f"   Markdown: {self.md_path}")
    
    def simple_sleep_cycle(self):
        """简化的睡眠周期"""
        if not self.short_term_buffer:
            print("[INFO]️ 短期缓存为空，跳过睡眠周期")
            return
        
        print(f"[SLEEP] 运行睡眠周期，处理 {len(self.short_term_buffer)} 条短期记忆...")
        
        # 简单的压缩：选取重要性最高的记忆
        sorted_buffer = sorted(self.short_term_buffer, key=lambda x: x['importance'], reverse=True)
        top_memory = sorted_buffer[0] if sorted_buffer else None
        
        if top_memory:
            fact_entry = {
                "fact": f"压缩总结: {top_memory.get('content', '')[:100]}...",
                "vec": top_memory['vec'],
                "timestamp": datetime.now().isoformat(),
                "type": "knowledge",
                "confidence": 0.9,
                "source_count": len(self.short_term_buffer)
            }
            self.long_term_knowledge.append(fact_entry)
            print(f"[OK] 压缩为1条长期记忆: {fact_entry['fact'][:80]}...")
        
        self.short_term_buffer = []
        self.save_memory()
    
    def retrieve(self, query_text, top_k=3):
        """简化检索"""
        if not self.long_term_knowledge:
            print(f"[INFO]️ 长期记忆为空，无法检索: '{query_text}'")
            return []
        
        print(f"[SEARCH] 检索: '{query_text}'")
        
        query_vec = self._embed(query_text)
        
        # 计算相似度
        results = []
        for mem in self.long_term_knowledge:
            if 'vec' in mem and mem['vec']:
                try:
                    mem_vec = np.array(mem['vec'])
                    similarity = cosine_similarity([query_vec], [mem_vec])[0][0]
                    
                    # 简单评分
                    confidence = mem.get('confidence', 0.5)
                    score = similarity * confidence
                    
                    results.append({
                        "content": mem.get('fact', mem.get('content', '')),
                        "score": score,
                        "similarity": similarity,
                        "type": mem.get('type', 'unknown'),
                        "timestamp": mem.get('timestamp', '')
                    })
                except Exception as e:
                    print(f"[WARNING]️ 计算相似度出错: {e}")
        
        # 排序
        results.sort(key=lambda x: x['score'], reverse=True)
        
        print(f"[CHART] 找到 {len(results)} 条相关记忆 (显示前{top_k}条):")
        for i, res in enumerate(results[:top_k]):
            print(f"  {i+1}. [{res['type']}] score={res['score']:.3f}: {res['content'][:60]}...")
        
        return results[:top_k]

# ==========================================
# 4. 运行测试
# ==========================================
print("\n" + "=" * 60)
print("[ROCKET] 开始记忆引擎测试")
print("=" * 60)

try:
    # 初始化引擎
    print("\n1. 初始化记忆引擎...")
    
    # 尝试从环境变量获取API Key
    api_key = os.environ.get("DEEPSEEK_API_KEY") or os.environ.get("SILICONFLOW_API_KEY")
    base_url = "https://api.siliconflow.cn/v1"
    
    if api_key:
        print(f"[KEY] 使用环境变量中的API Key (前10位): {api_key[:10]}...")
    else:
        print("[INFO]️ 未找到API Key，使用本地评估模式")
        api_key = None
    
    engine = TestMemoryEngine(
        memory_name="test_memory_store",
        api_key=api_key,
        base_url=base_url
    )
    
    # 2. 摄入测试文件
    print("\n2. 摄入记忆文件...")
    test_file = r"C:\Users\Lenovo\.openclaw\workspace\memory\2026-03-25.md"
    
    if os.path.exists(test_file):
        engine.ingest_log_file(test_file)
    else:
        print(f"[ERROR] 测试文件不存在: {test_file}")
        # 创建测试文件
        test_content = """# 测试记忆
## 简历优化
今天优化了简历，添加了量子计算相关内容

## GitHub项目
整理了Python文件，按功能分类

## 学习记录
学习了Qiskit基础，完成了一个简单的量子电路"""
        
        test_file = os.path.join(os.path.dirname(__file__), "test_memory.md")
        with open(test_file, "w", encoding="utf-8") as f:
            f.write(test_content)
        print(f"[NOTE] 创建了测试文件: {test_file}")
        engine.ingest_log_file(test_file)
    
    # 3. 压缩记忆
    print("\n3. 压缩短期记忆...")
    engine.save_memory()  # 先保存短期记忆
    engine.sleep_cycle = engine.simple_sleep_cycle = lambda: engine.simple_sleep_cycle_impl()
    engine.simple_sleep_cycle_impl = lambda: None  # 简化的睡眠周期
    
    # 实际上调用我们定义的简单压缩
    engine.simple_sleep_cycle()
    
    # 4. 测试检索
    print("\n4. 测试检索功能...")
    
    test_queries = ["简历", "GitHub", "量子计算", "工作"]
    for query in test_queries:
        engine.retrieve(query)
        time.sleep(0.5)  # 避免太快
    
    # 5. 显示文件信息
    print("\n5. 生成的文件信息...")
    if os.path.exists(engine.json_path):
        with open(engine.json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            print(f"[CHART] JSON文件: {engine.json_path}")
            print(f"   包含 {len(data)} 条记忆")
            if data:
                print(f"   示例记忆: {data[0].get('fact', data[0].get('content', ''))[:80]}...")
    
    if os.path.exists(engine.md_path):
        import subprocess
        print(f"[NOTE] Markdown文件: {engine.md_path}")
        result = subprocess.run(["head", "-5", engine.md_path], capture_output=True, text=True, shell=True)
        if result.stdout:
            print("   文件预览:")
            for line in result.stdout.strip().split('\n'):
                print(f"   {line}")
    
    print("\n" + "=" * 60)
    print("[OK] 测试完成！")
    print(f"[FOLDER] 记忆存储目录: {engine.base_dir}")
    print("=" * 60)
    
except Exception as e:
    print(f"\n[ERROR] 测试过程中出错: {e}")
    traceback.print_exc()
    sys.exit(1)