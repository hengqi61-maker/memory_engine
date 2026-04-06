#!/usr/bin/env python3
"""
长期存储适配器层
为现有的 OpenClawMemoryEngine 提供兼容接口
允许平滑迁移到新的长期存储系统
"""

import os
import json
from datetime import datetime
from typing import List, Dict, Optional

from long_term_storage import LongTermStorage, StoreSchema


class LongTermStorageAdapter:
    """
    适配器类，提供与 EnhancedStorageLayer 相同的接口
    但使用新的 LongTermStorage 作为后端
    """
    
    def __init__(self, base_path: str, archive_dir: str = None):
        """
        初始化适配器
        
        Args:
            base_path: 主存储文件基础路径（不含扩展名）
            archive_dir: 归档目录
        """
        self.base_path = base_path
        self.archive_dir = archive_dir
        
        # 提取存储目录和名称
        storage_dir = os.path.dirname(base_path)
        memory_name = os.path.basename(base_path)
        
        # 如果 archive_dir 未提供，使用默认路径
        if not archive_dir:
            archive_dir = os.path.join(storage_dir, "archived")
        
        # 初始化长期存储系统
        self.long_term_storage = LongTermStorage(
            storage_dir=os.path.join(storage_dir, "long_term"),
            embedding_dim=768,
            enable_archive=True
        )
        
        # 兼容性标志
        self.has_archive = True
        self.json_path = f"{base_path}.json"
        self.md_path = f"{base_path}.md"
        
        print(f"[适配器] 初始化长期存储适配器")
        print(f"         存储目录: {storage_dir}")
        print(f"         归档目录: {archive_dir}")
    
    def load(self) -> List[Dict]:
        """
        加载记忆（与 EnhancedStorageLayer 兼容）
        从长期存储中加载所有活跃记忆
        
        Returns:
            记忆对象列表
        """
        store_data = self.long_term_storage.store_data
        
        if not store_data:
            return []
        
        # 从长期存储中提取活跃记忆的 memory_obj
        memories = []
        for mem in store_data.get("memories", []):
            # 仅包含未归档的记忆
            if not mem.get("archived_path"):
                memories.append(mem["memory_obj"])
        
        print(f"[适配器] 加载了 {len(memories)} 条活跃记忆")
        return memories
    
    def save_atomic(self, data: List[Dict], summary_content: str):
        """
        原子保存（与 EnhancedStorageLayer 兼容）
        将记忆保存到长期存储
        
        Args:
            data: 记忆对象列表
            summary_content: Markdown 摘要（暂时忽略，由长期存储自己生成）
        """
        print(f"[适配器] 开始原子保存 {len(data)} 条记忆...")
        
        # 首先，获取当前长期存储中的所有活跃记忆
        current_store = self.long_term_storage.store_data.get("memories", [])
        current_active = [m for m in current_store if not m.get("archived_path")]
        
        # 我们需要找出新增的记忆
        existing_ids = {m["memory_obj"]["id"] for m in current_active if "id" in m["memory_obj"]}
        new_memories = []
        
        for mem in data:
            mem_id = mem.get("id")
            if mem_id and mem_id not in existing_ids:
                new_memories.append(mem)
        
        # 批量存储新记忆
        if new_memories:
            storage_ids = self.long_term_storage.store_batch(new_memories)
            print(f"[适配器] 新增 {len(storage_ids)} 条记忆到长期存储")
        else:
            # 如果没有新记忆，只保存存储状态
            self.long_term_storage.save()
            print(f"[适配器] 无新记忆，仅保存存储状态")
        
        # 同时保存兼容的 JSON 文件（供旧系统使用）
        self._save_compatible_json(data)
        
        # 保存 Markdown 摘要
        self._save_markdown(summary_content)
        
        print("[适配器] 原子保存完成")
    
    def _save_compatible_json(self, data: List[Dict]):
        """保存兼容的 JSON 文件（向后兼容）"""
        try:
            # 原子保存
            tmp_path = self.json_path + ".tmp"
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            if os.path.exists(self.json_path):
                import shutil
                shutil.copy2(self.json_path, self.json_path + ".bak")
            
            os.replace(tmp_path, self.json_path)
            
            print(f"[适配器] 兼容JSON已保存: {self.json_path}")
        except Exception as e:
            print(f"[WARN] 保存兼容JSON失败: {e}")
    
    def _save_markdown(self, content: str):
        """保存 Markdown 摘要"""
        try:
            with open(self.md_path, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"[适配器] Markdown已保存: {self.md_path}")
        except Exception as e:
            print(f"[WARN] 保存Markdown失败: {e}")
    
    def archive_pruned(self, pruned_memories: List[Dict], reason: str = "normal_pruning") -> bool:
        """
        归档修剪的记忆（与 EnhancedStorageLayer 兼容）
        
        Args:
            pruned_memories: 修剪的记忆列表
            reason: 修剪原因
        
        Returns:
            是否成功
        """
        if not pruned_memories:
            print("[适配器] 无修剪记忆可归档")
            return True
        
        print(f"[适配器] 开始归档 {len(pruned_memories)} 条修剪记忆，原因: {reason}")
        
        # 需要找到这些记忆对应的 storage_id
        # 由于我们不知道原始记忆的 storage_id，我们需要通过内容来匹配
        # 这是一个简化的实现，在实际使用中可能需要更精确的匹配
        
        storage_ids_to_archive = []
        
        for pruned_mem in pruned_memories:
            mem_id = pruned_mem.get("id")
            if not mem_id:
                continue
            
            # 在长期存储中查找对应的记忆
            found = False
            for stored_mem in self.long_term_storage.store_data.get("memories", []):
                mem_obj = stored_mem.get("memory_obj", {})
                stored_id = mem_obj.get("id")
                
                if stored_id == mem_id:
                    # 找到匹配的记忆
                    storage_ids_to_archive.append(stored_mem["storage_id"])
                    found = True
                    break
            
            if not found:
                print(f"[WARN] 未找到记忆 {mem_id} 在长期存储中，跳过归档")
        
        # 执行归档
        if storage_ids_to_archive:
            success = self.long_term_storage.archive(storage_ids_to_archive, reason)
            if success:
                print(f"[适配器] 成功归档 {len(storage_ids_to_archive)} 条记忆")
            else:
                print(f"[WARN]️ 归档失败")
            
            return success
        else:
            print("[适配器] 未找到需要归档的记忆ID")
            return False
    
    def list_archives(self):
        """列出归档文件（与 EnhancedStorageLayer 兼容）"""
        # 返回归档统计信息
        stats = self.long_term_storage.get_stats()
        
        archives = []
        if "archived_memories" in stats and stats["archived_memories"] > 0:
            archives.append({
                "count": stats["archived_memories"],
                "time": datetime.now().isoformat(),
                "reason": "various",
                "source": "long_term_storage"
            })
        
        return archives


# ==================== 迁移工具 ====================
class MigrationTool:
    """迁移工具，帮助从旧存储迁移到新存储系统"""
    
    @staticmethod
    def migrate_from_old_json(old_json_path: str, new_storage: LongTermStorage):
        """
        从旧的 JSON 存储文件迁移到新的长期存储
        
        Args:
            old_json_path: 旧 JSON 文件路径
            new_storage: 新的长期存储实例
        """
        if not os.path.exists(old_json_path):
            print(f"[迁移] 旧文件不存在: {old_json_path}")
            return False
        
        try:
            with open(old_json_path, "r", encoding="utf-8") as f:
                old_data = json.load(f)
            
            print(f"[迁移] 从 {old_json_path} 加载了 {len(old_data)} 条记忆")
            
            # 转换和迁移每条记忆
            migrated_count = 0
            for i, mem in enumerate(old_data):
                try:
                    # 确保记忆有必要的字段
                    if "fact" not in mem and "content" in mem:
                        mem["fact"] = mem["content"][:200] + "..."
                    
                    if "vec" not in mem or not mem["vec"]:
                        # 生成伪向量
                        import numpy as np
                        mem["vec"] = np.random.rand(768).tolist()
                    
                    if "importance" not in mem:
                        mem["importance"] = 0.5
                    
                    if "type" not in mem:
                        mem["type"] = "log"
                    
                    if "timestamp" not in mem:
                        mem["timestamp"] = datetime.now().isoformat()
                    
                    if "metadata" not in mem:
                        mem["metadata"] = {}
                    
                    # 存储到新系统
                    storage_id = new_storage.store(mem)
                    migrated_count += 1
                    
                    if (i + 1) % 100 == 0:
                        print(f"[迁移] 已迁移 {i+1} 条记忆...")
                        
                except Exception as e:
                    print(f"[WARN] 迁移记忆 {i} 失败: {e}")
            
            # 保存新存储
            new_storage.save()
            
            print(f"[迁移] 迁移完成: {migrated_count}/{len(old_data)} 条记忆成功迁移")
            return True
            
        except Exception as e:
            print(f"[ERROR] 迁移失败: {e}")
            return False
    
    @staticmethod
    def migrate_from_old_storage(old_storage_dir: str, new_storage_dir: str = "./long_term_storage"):
        """
        从旧存储目录迁移到新的长期存储
        
        Args:
            old_storage_dir: 旧存储目录（包含 JSON 和归档文件）
            new_storage_dir: 新存储目录
        """
        print(f"[迁移] 开始从 {old_storage_dir} 迁移到 {new_storage_dir}")
        
        # 初始化新存储
        new_storage = LongTermStorage(
            storage_dir=new_storage_dir,
            embedding_dim=768,
            enable_archive=True
        )
        
        # 迁移主 JSON 文件
        old_json = os.path.join(old_storage_dir, "openclaw_memory.json")
        if os.path.exists(old_json):
            MigrationTool.migrate_from_old_json(old_json, new_storage)
        else:
            # 尝试其他可能的文件名
            for filename in os.listdir(old_storage_dir):
                if filename.endswith(".json") and "memory" in filename.lower():
                    MigrationTool.migrate_from_old_json(
                        os.path.join(old_storage_dir, filename), 
                    new_storage)
                    break
        
        # 迁移归档文件
        old_archive_dir = os.path.join(old_storage_dir, "archived")
        if os.path.exists(old_archive_dir):
            MigrationTool._migrate_archives(old_archive_dir, new_storage)
        
        print("[迁移] 迁移工具执行完成")
    
    @staticmethod
    def _migrate_archives(archive_dir: str, new_storage: LongTermStorage):
        """迁移归档文件"""
        import glob
        
        archive_files = glob.glob(os.path.join(archive_dir, "**", "pruned_*.json"), recursive=True)
        
        print(f"[迁移] 找到 {len(archive_files)} 个归档文件")
        
        for i, archive_file in enumerate(archive_files):
            try:
                with open(archive_file, "r", encoding="utf-8") as f:
                    archive_data = json.load(f)
                
                pruned_memories = archive_data.get("pruned_memories", [])
                if not pruned_memories:
                    continue
                
                # 提取原因
                metadata = archive_data.get("metadata", {})
                reason = metadata.get("reason", "unknown")
                
                print(f"[迁移] 处理归档文件 {i+1}: {os.path.basename(archive_file)} ({len(pruned_memories)} 条记忆)")
                
                # 迁移归档的记忆
                for mem in pruned_memories:
                    try:
                        # 标记为已归档
                        if "metadata" not in mem:
                            mem["metadata"] = {}
                        mem["metadata"]["archived_source"] = archive_file
                        
                        # 存储到新系统
                        storage_id = new_storage.store(mem)
                        
                        # 立即归档这个记忆
                        new_storage.archive([storage_id], reason=f"migrated_{reason}")
                        
                    except Exception as e:
                        print(f"[WARN] 迁移归档记忆失败: {e}")
                
            except Exception as e:
                print(f"[WARN] 处理归档文件失败 {archive_file}: {e}")


# ==================== 测试函数 ====================
def test_adapter():
    """测试适配器功能"""
    print("=" * 70)
    print("长期存储适配器 - 测试")
    print("=" * 70)
    
    # 创建测试目录
    test_dir = "./test_adapter"
    import shutil
    if os.path.exists(test_dir):
        shutil.rmtree(test_dir)
    os.makedirs(test_dir)
    
    # 初始化适配器
    base_path = os.path.join(test_dir, "memory_store")
    adapter = LongTermStorageAdapter(base_path)
    
    # 创建测试数据
    test_memories = [
        {
            "id": "test_001",
            "content": "测试记忆 1: 关于量子计算",
            "fact": "测试记忆 1: 关于量子计算",
            "vec": [0.1] * 768,
            "importance": 0.9,
            "type": "knowledge",
            "timestamp": datetime.now().isoformat(),
            "confidence": 0.95
        },
        {
            "id": "test_002",
            "content": "测试记忆 2: Python代码示例",
            "fact": "测试记忆 2: Python代码示例",
            "vec": [0.2] * 768,
            "importance": 0.7,
            "type": "code",
            "timestamp": datetime.now().isoformat(),
            "confidence": 0.8
        }
    ]
    
    # 测试保存
    summary = "# 测试摘要\n\n这是测试摘要内容"
    adapter.save_atomic(test_memories, summary)
    
    # 测试加载
    loaded = adapter.load()
    print(f"[测试] 加载了 {len(loaded)} 条记忆")
    
    # 测试归档
    success = adapter.archive_pruned([test_memories[0]], reason="test_pruning")
    print(f"[测试] 归档结果: {'成功' if success else '失败'}")
    
    # 再次加载，应该只剩一条
    loaded_after = adapter.load()
    print(f"[测试] 归档后加载了 {len(loaded_after)} 条活跃记忆")
    
    # 清理
    shutil.rmtree(test_dir)
    print("\n[测试] 测试完成，已清理测试目录")


if __name__ == "__main__":
    # 运行测试
    test_adapter()