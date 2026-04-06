#!/usr/bin/env python3
"""
OpenClawMemoryEngine - 修复版
集成了归档管理器和双重存储，修复了原始代码中的错误
"""
import os
import re
import json
import shutil
import hashlib
import numpy as np
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from sklearn.metrics.pairwise import cosine_similarity

# 尝试导入可选的模块
try:
    import ollama
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False
    print("[WARN] Ollama不可用，将使用伪嵌入")

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    print("[WARN] OpenAI不可用，将使用本地评估")

# 导入归档管理器
try:
    # 尝试从当前目录导入
    import sys
    sys.path.insert(0, os.path.dirname(__file__))
    from archived_memory_manager import EnhancedStorageLayer, ArchivedMemoryManager
    ARCHIVE_AVAILABLE = True
except ImportError:
    print("[WARN] 无法导入归档管理器，归档功能将被禁用")
    ARCHIVE_AVAILABLE = False

class OpenClawMemoryEngine:
    def __init__(self, memory_name="memory_store", api_key=None, base_url=None, 
                 enable_archive=True, archive_dir=None):
        """
        初始化记忆引擎
        
        Args:
            memory_name: 存储文件的基础名称（不含扩展名）
            api_key: OpenAI API Key (从环境变量读取更安全)
            base_url: API基础URL
            enable_archive: 是否启用归档功能
            archive_dir: 归档目录，默认在memory/engine/archived/
        """
        # 1. 存储路径配置
        workspace_dir = os.path.dirname(os.path.abspath(__file__))
        self.base_dir = os.path.join(workspace_dir, "memory", "engine")
        os.makedirs(self.base_dir, exist_ok=True)
        
        self.json_path = os.path.join(self.base_dir, f"{memory_name}.json")
        self.md_path = os.path.join(self.base_dir, f"{memory_name}.md")
        
        print(f"[路径] 存储路径:")
        print(f"   JSON: {self.json_path}")
        print(f"   Markdown: {self.md_path}")
        
        # 2. 初始化OpenAI客户端（可选）
        self.client = None
        if api_key or os.environ.get("DEEPSEEK_API_KEY"):
            api_key = api_key or os.environ.get("DEEPSEEK_API_KEY")
            base_url = base_url or "https://api.siliconflow.cn/v1"
            
            if OPENAI_AVAILABLE:
                try:
                    self.client = OpenAI(api_key=api_key, base_url=base_url)
                    print(f"[钥匙] OpenAI客户端初始化成功 (base_url: {base_url})")
                except Exception as e:
                    print(f"[WARN] OpenAI客户端初始化失败: {e}")
            else:
                print("[INFO] OpenAI库不可用，使用本地评估模式")
        else:
            print("[INFO] 无API Key，使用本地评估模式")
        
        # 3. 初始化存储层和归档管理器
        self.enable_archive = enable_archive and ARCHIVE_AVAILABLE
        if self.enable_archive:
            # 设置归档目录
            if not archive_dir:
                archive_dir = os.path.join(self.base_dir, "archived")
            os.makedirs(archive_dir, exist_ok=True)
            
            self.storage = EnhancedStorageLayer(
                base_path=os.path.join(self.base_dir, memory_name),
                archive_dir=archive_dir
            )
            print(f"[归档] 已启用归档功能，目录: {archive_dir}")
        else:
            # 使用简化的存储层
            self.storage = self.SimpleStorageLayer(self.json_path, self.md_path)
            print("[INFO]️ 使用简单存储层（无归档功能）")
        
        # 4. 加载现有记忆
        self.long_term_knowledge = self.storage.load()
        self.short_term_buffer = []
        
        print(f"[统计] 已加载 {len(self.long_term_knowledge)} 条长期记忆")
        
        # 5. 参数配置
        self.lambda_task = 0.2
        self.lambda_fact = 0.01
        self.temperature = 0.3
        self.debug_mode = True
    
    # ==================== 简单存储层（当归档不可用时） ====================
    class SimpleStorageLayer:
        """简化存储层，兼容EnhancedStorageLayer接口"""
        def __init__(self, json_path, md_path):
            self.json_path = json_path
            self.md_path = md_path
            self.has_archive = False
        
        def load(self):
            if not os.path.exists(self.json_path):
                return []
            try:
                with open(self.json_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"[WARN]️ 加载失败: {e}")
                return []
        
        def save_atomic(self, data, summary_content):
            # 原子保存
            tmp_path = self.json_path + ".tmp"
            try:
                with open(tmp_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                
                # 备份原文件
                if os.path.exists(self.json_path):
                    shutil.copy(self.json_path, self.json_path + ".bak")
                
                os.replace(tmp_path, self.json_path)
                print(f"[保存] JSON已保存: {self.json_path}")
            except Exception as e:
                print(f"[ERROR] 保存JSON失败: {e}")
                return
            
            # 保存Markdown
            try:
                with open(self.md_path, "w", encoding="utf-8") as f:
                    f.write(summary_content)
                print(f"[笔记] Markdown已保存: {self.md_path}")
            except Exception as e:
                print(f"[WARN]️ 保存Markdown失败: {e}")
        
        def archive_pruned(self, pruned_memories, reason="normal_pruning"):
            # 简单存储层没有归档功能
            print(f"[INFO]️ 归档功能未启用，忽略 {len(pruned_memories)} 条修剪记忆")
            return False
    
    # ==================== 文本处理 ====================
    def _split_text(self, text, max_chunk_size=500):
        """智能切分文本"""
        # 按标题分割
        sections = re.split(r'\n(?=#{1,4} )', text)
        chunks = []
        
        for section in sections:
            section = section.strip()
            if not section:
                continue
            
            lines = section.split('\n')
            title = lines[0] if lines[0].startswith('#') else ""
            content = "\n".join(lines[1:]) if title else section
            
            sub_chunks = self._split_long_text(content, max_chunk_size)
            
            for sub in sub_chunks:
                chunk = f"{title}\n{sub}" if title else sub
                chunks.append(chunk.strip())
        
        if len(chunks) <= 1:
            chunks = [p.strip() for p in text.split('\n\n') if p.strip()]
        
        print(f"[归档] 切分完成：{len(chunks)} 个片段")
        return chunks
    
    def _split_long_text(self, text, max_len):
        """切分长文本"""
        if len(text) <= max_len:
            return [text]
        
        sentences = re.split(r'(?<=[.!?。！？])', text)
        chunks = []
        current = ""
        
        for s in sentences:
            if len(current) + len(s) < max_len:
                current += s
            else:
                chunks.append(current.strip())
                current = s
        
        if current:
            chunks.append(current.strip())
        
        return chunks
    
    # ==================== 嵌入向量化 ====================
    def _embed(self, text):
        """文本向量化，失败时返回伪嵌入向量而非零向量"""
        # 伪向量生成函数（内部复用）
        def _pseudo_embedding(text):
            import hashlib
            h = hashlib.sha256(text.encode()).hexdigest()
            seed = int(h[:8], 16) % 10000
            np.random.seed(seed)
            vec = np.random.rand(768) - 0.5
            norm = np.linalg.norm(vec)
            if norm > 0:
                vec = vec / norm
            return vec
        
        # 情况1: Ollama库未安装/不可用
        if not OLLAMA_AVAILABLE:
            print("[WARN]️ Ollama不可用，使用伪嵌入向量")#存在巨大数据漏洞
            return _pseudo_embedding(text)
        
        # 情况2: Ollama库可用，尝试API调用
        try:
            # 截断超长文本
            MAX_LENGTH = 8192
            if len(text) > MAX_LENGTH:
                text = text[:MAX_LENGTH]
                print(f"[WARN]️ 文本过长，截断至 {MAX_LENGTH} 字符")
            
            response = ollama.embeddings(
                model="nomic-embed-text",
                prompt=text
            )
            
            vec = np.array(response["embedding"])
            
            # 归一化
            norm = np.linalg.norm(vec)
            if norm > 0:
                vec = vec / norm
            
            return vec
            
        except Exception as e:
            print(f"[WARN]️ Ollama API调用失败，降级到伪嵌入向量 (错误: {e})")
            return _pseudo_embedding(text)
    
    # ==================== 记忆评估 ====================#记忆评估明显不合理
    def _evaluate_signal(self, chunk):
        """
        评估记忆片段的重要性
        改进：使用本地规则，避免API调用
        """
        # 本地评估规则
        importance = 0.5
        memory_type = "log"
        
        # 识别重要关键词
        chunk_lower = chunk.lower()
        
        if any(keyword in chunk_lower for keyword in ["简历", "项目", "工作", "任务"]):
            importance = 0.8
            memory_type = "task"
        elif any(keyword in chunk_lower for keyword in ["github", "代码", "python", "文件"]):
            importance = 0.7
            memory_type = "code"
        elif any(keyword in chunk_lower for keyword in ["量子", "qiskit", "计算", "物理", "学习"]):
            importance = 0.9
            memory_type = "knowledge"
        
        # 标题块更重要
        if chunk.startswith('#'):
            importance = max(importance, 0.7)
        
        return {"type": memory_type, "importance": importance}
    
    # ==================== 记忆摄入 ====================
    def ingest_log_file(self, file_path):
        """摄入日志文件"""
        if not os.path.exists(file_path):
            print(f"[ERROR] 文件不存在: {file_path}")
            return
        
        with open(file_path, "r", encoding="utf-8") as f:
            text = f.read()
        
        chunks = self._split_text(text)
        print(f"[大脑] 开始处理 {len(chunks)} 个记忆片段...")
        
        for i, chunk in enumerate(chunks):
            # 评估重要性
            metadata = self._evaluate_signal(chunk)
            
            # 生成嵌入向量
            vec = self._embed(chunk)
            
            memory = {
                "id": f"{datetime.now().strftime('%Y%m%d')}_{i}",
                "content": chunk[:500],  # 截断以节省空间
                "vec": vec.tolist(),
                "importance": metadata['importance'],
                "type": metadata['type'],
                "timestamp": datetime.now().isoformat()
            }
            
            self.short_term_buffer.append(memory)
            print(f"   [{i+1}/{len(chunks)}] 类型:{metadata['type']} 权重:{metadata['importance']:.1f}")
        
        print(f"[完成] 成功摄入 {len(chunks)} 条记忆到短期缓存")
    
    # ==================== 睡眠周期 ====================
    def sleep_cycle(self, enable_pruning=True):
        """
        睡眠周期：压缩短期记忆并归档修剪的记忆
        
        Args:
            enable_pruning: 是否启用修剪归档
        """
        print("\n[睡眠] 开始记忆巩固...")
        
        if not self.short_term_buffer:
            print("📭 短期缓存为空，跳过睡眠周期")
            return
        
        # 1. 筛选短期记忆
        survived = self._filter_memories()
        print(f"[统计] 筛选后保留 {len(survived)} 条记忆（原始: {len(self.short_term_buffer)}）")
        
        # 2. 如果启用了修剪，归档被淘汰的记忆
        if enable_pruning and len(self.short_term_buffer) > len(survived):
            pruned_count = len(self.short_term_buffer) - len(survived)
            pruned_memories = [m for m in self.short_term_buffer if m not in survived]
            
            print(f"[剪刀]️ 准备归档 {pruned_count} 条修剪记忆...")
            success = self.storage.archive_pruned(pruned_memories, reason="normal_pruning")
            if success:
                print(f"[归档] 已归档 {pruned_count} 条记忆")
            else:
                print(f"[WARN]️ 归档失败，修剪记忆将丢失")
        
        # 3. 压缩保留的记忆
        new_facts = self._consolidate(survived)
        
        # 4. 添加到长期记忆
        self.long_term_knowledge.extend(new_facts)
        self.short_term_buffer = []
        
        # 5. 保存记忆
        summary = self._generate_summary()
        self.storage.save_atomic(self.long_term_knowledge, summary)
        
        print(f"[完成] 睡眠周期完成，添加了 {len(new_facts)} 条新事实到长期记忆")
    
    # ==================== 记忆筛选 ====================
    def _filter_memories(self):
        """筛选短期记忆，基于重要性和时间衰减"""
        if not self.short_term_buffer:#记忆文件前方的系数怎么确定？不同的记忆有不同的起始值，遗忘系数不合理
            return []
        
        now = datetime.now()
        energies = []
        
        for m in self.short_term_buffer:
            # 计算时间衰减
            dt = (now - datetime.fromisoformat(m['timestamp'])).total_seconds() / 3600
            decay = np.exp(-self.lambda_fact * dt)
            energy = m['importance'] * decay
            energies.append(energy)
        
        # 使用softmax计算保留概率
        probs = self._softmax(np.array(energies))#soft函数的过度归一化，修剪阈值系数确定不科学
        
        # 保留概率大于0.1的记忆
        return [m for m, p in zip(self.short_term_buffer, probs) if p > 0.1]
    
    # ==================== 记忆压缩 ====================
    def _consolidate(self, memories):
        """压缩记忆"""
        if not memories:
            return []
        
        if len(memories) == 1:
            # 只有一条记忆，直接使用
            content = memories[0]['content']
            fact_text = f"记忆: {content[:200]}..."
        else:
            # 合并重要记忆
            top_memory = max(memories, key=lambda x: x['importance'])
            content = top_memory['content']
            fact_text = f"总结: {content[:150]}... (共 {len(memories)} 条相关记忆)"
        
        # 生成新向量
        vec = self._embed(fact_text)
        
        return [{
            "fact": fact_text,
            "vec": vec.tolist(),
            "timestamp": datetime.now().isoformat(),
            "type": "knowledge",
            "confidence": 0.9,
            "source_count": len(memories)
        }]
    
    # ==================== 检索功能 ====================
    def retrieve(self, query_text, top_k=5, query_type=None):
        """简化的检索功能"""
        if not self.long_term_knowledge:
            print(f"📭 长期记忆为空，无法检索: '{query_text}'")
            return []
        
        print(f"[检索] 检索: '{query_text}' (类型: {query_type})")
        
        # 查询向量
        query_vec = self._embed(query_text)
        
        results = []
        now = datetime.now()
        
        for i, mem in enumerate(self.long_term_knowledge):
            if 'vec' not in mem or not mem['vec']:
                continue
            
            try:
                mem_vec = np.array(mem['vec'])
                
                # 计算相似度
                similarity = cosine_similarity([query_vec], [mem_vec])[0][0]
                
                # 类型匹配权重
                type_w = 1.2 if query_type and mem.get('type') == query_type else 0.8
                
                # 时间衰减
                dt = (now - datetime.fromisoformat(mem['timestamp'])).total_seconds() / 3600
                time_w = np.exp(-0.01 * dt)  # 轻微时间衰减
                
                # 置信度
                confidence = mem.get('confidence', 0.5)
                
                # 最终得分
                score = similarity * confidence * type_w * time_w
                
                if score > 0.1:  # 最低阈值的确定明显不合理
                    results.append({
                        "fact": mem.get('fact', mem.get('content', '')),
                        "score": score,
                        "similarity": similarity,
                        "type": mem.get('type', 'unknown'),
                        "timestamp": mem.get('timestamp', ''),
                        "confidence": confidence
                    })
            except Exception as e:
                if self.debug_mode:
                    print(f"[WARN]️ 记忆 {i} 计算出错: {e}")
        
        # 排序
        results.sort(key=lambda x: x['score'], reverse=True)
        
        print(f"[统计] 找到 {len(results)} 条相关记忆:")
        for i, res in enumerate(results[:min(top_k, 3)]):
            print(f"  {i+1}. [{res['type']}] 分数:{res['score']:.3f}")
            print(f"     内容: {res['fact'][:80]}...")
        
        return results[:top_k]
    
    # ==================== 辅助方法 ====================
    def _softmax(self, x):
        """Softmax函数"""
        e_x = np.exp(x - np.max(x))
        return e_x / (e_x.sum() + 1e-8)
    
    def _generate_summary(self):
        """生成Markdown摘要"""
        header = "# 长期记忆摘要\n\n"
        header += f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        header += f"记忆总数: {len(self.long_term_knowledge)}\n\n"
        header += "| ID | 事实 | 类型 | 时间 | 置信度 |\n"
        header += "|---|---|---|---|---|\n"
        
        rows = []
        for i, mem in enumerate(self.long_term_knowledge):
            fact = mem.get('fact', mem.get('content', '无内容'))[:80]
            mem_type = mem.get('type', 'unknown')
            timestamp = mem.get('timestamp', '')[:19]
            confidence = mem.get('confidence', 0.0)
            rows.append(f"| {i} | {fact}... | {mem_type} | {timestamp} | {confidence:.2f} |")
        
        return header + "\n".join(rows)
    
    def list_memories(self, limit=10):
        """列出记忆"""
        print(f"\n[列表] 记忆列表 (前{limit}条):")
        for i, mem in enumerate(self.long_term_knowledge[:limit]):
            fact = mem.get('fact', mem.get('content', '无内容'))
            print(f"{i+1}. [{mem.get('type', '未知')}] {fact[:80]}...")
    
    def get_stats(self):
        """获取统计信息"""
        stats = {
            "long_term_count": len(self.long_term_knowledge),
            "short_term_count": len(self.short_term_buffer),
            "memory_types": {}
        }
        
        # 统计类型分布
        for mem in self.long_term_knowledge:
            mem_type = mem.get('type', 'unknown')
            stats["memory_types"][mem_type] = stats["memory_types"].get(mem_type, 0) + 1
        
        return stats


# ==================== 主程序 ====================
def main():
    """测试主程序"""
    print("=" * 70)
    print("OpenClawMemoryEngine 修复版 - 测试运行")
    print("=" * 70)
    
    # 1. 初始化引擎
    print("\n[启动] 初始化记忆引擎...")
    
    # 尝试从环境变量获取API Key
    api_key = os.environ.get("DEEPSEEK_API_KEY")
    if api_key:
        print(f"[钥匙] 使用环境变量中的API Key")
    else:
        print("[信息] 未找到API Key，使用本地模式")
    
    engine = OpenClawMemoryEngine(
        memory_name="openclaw_memory",
        api_key=api_key,
        enable_archive=True
    )
    
    # 2. 测试记忆文件
    print("\n[文件] 测试记忆摄入...")
    test_file = r"C:\Users\Lenovo\.openclaw\workspace\memory\2026-03-25.md"
    
    if os.path.exists(test_file):
        print(f"找到测试文件: {test_file}")
        engine.ingest_log_file(test_file)
    else:
        print(f"[错误] 测试文件不存在: {test_file}")
        # 创建示例文件
        example_content = """# 测试记忆
## 量子计算学习
今天学习了Qiskit的基础，创建了一个简单的量子电路

## GitHub项目整理
整理了Python代码文件，按功能模块分类

## 简历更新
更新了简历，添加了量子计算相关技能"""
        
        test_file = os.path.join(os.path.dirname(__file__), "test_memory.md")
        with open(test_file, "w", encoding="utf-8") as f:
            f.write(example_content)
        print(f"[笔记] 创建了示例文件: {test_file}")
        engine.ingest_log_file(test_file)
    
    # 3. 运行睡眠周期
    print("\n[睡眠] 运行睡眠周期...")
    engine.sleep_cycle()
    
    # 4. 测试检索
    print("\n[检索] 测试检索功能...")
    test_queries = [
        ("量子", "knowledge"),
        ("GitHub", "code"),
        ("简历", "task"),
        ("学习", None)
    ]
    
    for query, qtype in test_queries:
        engine.retrieve(query, query_type=qtype)
    
    # 5. 显示统计信息
    print("\n[统计] 记忆统计:")
    stats = engine.get_stats()
    print(f"   长期记忆: {stats['long_term_count']} 条")
    print(f"   短期缓存: {stats['short_term_count']} 条")
    print(f"   类型分布: {stats['memory_types']}")
    
    # 6. 列出记忆
    engine.list_memories(limit=5)
    
    print("\n" + "=" * 70)
    print("[完成] 测试完成!")
    print(f"[目录] 存储目录: {engine.base_dir}")
    print("=" * 70)


if __name__ == "__main__":
    main()