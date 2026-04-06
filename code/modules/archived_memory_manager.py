#!/usr/bin/env python3
"""
归档管理器 - 用于处理修剪的记忆归档
为OpenClawMemoryEngine设计的归档系统
"""
import os
import json
import shutil
from datetime import datetime
from typing import List, Dict

class ArchivedMemoryManager:
    """管理修剪记忆的归档存储"""
    
    def __init__(self, archive_dir: str):
        """
        初始化归档管理器
        
        Args:
            archive_dir: 归档目录路径，如 'memory/engine/archived/'
        """
        self.archive_dir = archive_dir
        os.makedirs(self.archive_dir, exist_ok=True)
        print(f"[目录] 归档目录: {self.archive_dir}")
    
    def generate_timestamp(self) -> str:
        """生成归档文件名的时间戳"""
        now = datetime.now()
        return now.strftime("%Y-%m-%d_%H-%M")
    
    def _generate_pruned_summary(self, pruned_memories: List[Dict]) -> str:
        """生成修剪记忆的Markdown摘要"""
        summary = f"""# 修剪记忆归档

## 归档信息
- **归档时间**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
- **记忆数量**: {len(pruned_memories)} 条
- **主要类型**: {self._get_main_types(pruned_memories)}

## 修剪记忆列表
"""
        
        for i, mem in enumerate(pruned_memories, 1):
            fact = mem.get('fact', mem.get('content', '无内容'))
            mem_type = mem.get('type', 'unknown')
            importance = mem.get('importance', 0.0)
            timestamp = mem.get('timestamp', '')
            
            summary += f"\n### {i}. [{mem_type}] 记忆"
            summary += f"\n- **时间**: {timestamp}"
            if importance > 0:
                summary += f"\n- **重要性**: {importance:.2f}"
            summary += f"\n- **内容预览**: {fact[:200]}..."
            
            # 添加元数据
            if 'confidence' in mem:
                summary += f"\n- **置信度**: {mem['confidence']:.2f}"
            
            summary += "\n"
        
        summary += f"\n---\n*归档生成时间: {datetime.now().isoformat()}*"
        return summary
    
    def _get_main_types(self, memories: List[Dict]) -> str:
        """获取记忆的主要类型分布"""
        type_counts = {}
        for mem in memories:
            mem_type = mem.get('type', 'unknown')
            type_counts[mem_type] = type_counts.get(mem_type, 0) + 1
        
        if not type_counts:
            return "无类型信息"
        
        sorted_types = sorted(type_counts.items(), key=lambda x: x[1], reverse=True)
        types_str = ", ".join([f"{t}({c})" for t, c in sorted_types[:3]])
        
        if len(type_counts) > 3:
            types_str += f" 等 {len(type_counts)} 种类型"
        
        return types_str
    
    def archive_pruned_memories(self, 
                               pruned_memories: List[Dict], 
                               reason: str = "normal_pruning",
                               prune_log: str = "") -> Dict[str, str]:
        """
        将修剪的记忆归档保存
        
        Args:
            pruned_memories: 修剪的记忆列表
            reason: 修剪原因 (normal_pruning, low_confidence, overlap, etc.)
            prune_log: 修剪操作日志
            
        Returns:
            包含归档文件路径的字典
        """
        if not pruned_memories:
            print("📭 无修剪记忆可归档")
            return {}
        
        timestamp = self.generate_timestamp()
        base_name = f"pruned_{timestamp}_{reason}"
        
        # 文件路径
        json_path = os.path.join(self.archive_dir, f"{base_name}.json")
        md_path = os.path.join(self.archive_dir, f"{base_name}.md")
        log_path = os.path.join(self.archive_dir, f"prune_log_{timestamp}.txt")
        
        print(f"[ARCHIVE] 归档 {len(pruned_memories)} 条记忆 -> {base_name}")
        
        # 1. 保存JSON数据
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump({
                "metadata": {
                    "archive_time": datetime.now().isoformat(),
                    "reason": reason,
                    "count": len(pruned_memories),
                    "source": "OpenClawMemoryEngine"
                },
                "pruned_memories": pruned_memories
            }, f, indent=2, ensure_ascii=False)
        
        # 2. 生成并保存Markdown摘要
        summary = self._generate_pruned_summary(pruned_memories)
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(summary)
        
        # 3. 如果有修剪日志，保存日志
        if prune_log:
            with open(log_path, "w", encoding="utf-8") as f:
                f.write(f"# 修剪操作日志\n")
                f.write(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"原因: {reason}\n")
                f.write(f"记忆数量: {len(pruned_memories)}\n\n")
                f.write(f"## 操作详情\n{prune_log}")
        
        print(f"[OK] 归档完成:")
        print(f"   JSON: {os.path.basename(json_path)}")
        print(f"   Markdown: {os.path.basename(md_path)}")
        if prune_log:
            print(f"   日志: {os.path.basename(log_path)}")
        
        return {
            "json": json_path,
            "md": md_path,
            "log": log_path if prune_log else None
        }
    
    def list_archives(self, max_results: int = 10) -> List[Dict]:
        """列出所有归档文件"""
        archives = []
        
        if not os.path.exists(self.archive_dir):
            return archives
        
        for filename in os.listdir(self.archive_dir):
            if filename.startswith("pruned_") and filename.endswith(".json"):
                file_path = os.path.join(self.archive_dir, filename)
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    
                    md_file = filename.replace(".json", ".md")
                    md_exists = os.path.exists(os.path.join(self.archive_dir, md_file))
                    
                    archives.append({
                        "filename": filename,
                        "path": file_path,
                        "count": data.get("metadata", {}).get("count", 0),
                        "time": data.get("metadata", {}).get("archive_time", ""),
                        "reason": data.get("metadata", {}).get("reason", "unknown"),
                        "has_markdown": md_exists
                    })
                except Exception as e:
                    print(f"[WARNING]️  读取归档文件失败 {filename}: {e}")
        
        # 按时间排序（最新的在前）
        archives.sort(key=lambda x: x.get("time", ""), reverse=True)
        return archives[:max_results]


# 简化的增强版StorageLayer，包含归档功能
class EnhancedStorageLayer:
    """增强版存储层，包含归档功能"""
    
    def __init__(self, base_path: str, archive_dir: str = None):
        """
        初始化增强存储层
        
        Args:
            base_path: 主存储文件基础路径（不含扩展名）
            archive_dir: 归档目录，如 'memory/engine/archived/'
        """
        self.json_path = f"{base_path}.json"
        self.md_path = f"{base_path}.md"
        self.bak_path = f"{base_path}.json.bak"
        
        # 归档管理器
        if archive_dir:
            self.archive_manager = ArchivedMemoryManager(archive_dir)
            self.has_archive = True
            print(f"[文件夹] 已启用归档功能，目录: {archive_dir}")
        else:
            self.archive_manager = None
            self.has_archive = False
    
    def load(self) -> List[Dict]:
        """加载记忆（与原始StorageLayer兼容）"""
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
        """原子保存（与原始StorageLayer兼容）"""
        tmp_path = self.json_path + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        if os.path.exists(self.json_path):
            shutil.copy(self.json_path, self.bak_path)
        
        os.replace(tmp_path, self.json_path)
        
        with open(self.md_path, "w", encoding="utf-8") as f:
            f.write(summary_content)
        print(f"[保存] 已保存: {self.json_path} 和 {self.md_path}")
    
    def archive_pruned(self, pruned_memories: List[Dict], reason: str = "normal_pruning") -> bool:
        """归档修剪的记忆"""
        if not self.has_archive or not pruned_memories:
            return False
        
        try:
            self.archive_manager.archive_pruned_memories(
                pruned_memories, 
                reason=reason,
                prune_log=f"来自存储: {self.json_path}\n修剪数量: {len(pruned_memories)}"
            )
            return True
        except Exception as e:
            print(f"[WARN]  归档失败: {e}")
            return False
    
    def list_archives(self):
        """列出归档文件"""
        if not self.has_archive:
            return []
        return self.archive_manager.list_archives()


# 示例使用
if __name__ == "__main__":
    print("=" * 60)
    print("归档管理器测试")
    print("=" * 60)
    
    # 示例记忆数据
    example_pruned_memories = [
        {
            "fact": "测试记忆 1: 关于量子计算的基础概念",
            "type": "knowledge",
            "importance": 0.5,
            "timestamp": datetime.now().isoformat(),
            "confidence": 0.8
        },
        {
            "fact": "测试记忆 2: Python代码片段示例",
            "type": "code",
            "importance": 0.7,
            "timestamp": datetime.now().isoformat(),
            "confidence": 0.9
        }
    ]
    
    # 创建归档管理器
    archive_dir = "memory/engine/archived"
    manager = ArchivedMemoryManager(archive_dir)
    
    # 归档测试
    result = manager.archive_pruned_memories(
        example_pruned_memories,
        reason="test_pruning",
        prune_log="这是测试修剪操作\n用于验证归档功能"
    )
    
    print(f"\n[CHART] 归档结果: {json.dumps(result, indent=2, ensure_ascii=False)}")
    
    # 列出归档
    archives = manager.list_archives()
    print(f"\n[CLIPBOARD] 归档列表 ({len(archives)} 个):")
    for arch in archives:
        print(f"  - {arch['filename']}: {arch['count']} 条记忆 ({arch['reason']})")