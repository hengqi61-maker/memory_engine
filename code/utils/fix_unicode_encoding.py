#!/usr/bin/env python3
"""
修复Python文件中的Unicode字符编码问题
将所有emoji和特殊Unicode字符替换为ASCII文本
"""

import os
import re
import sys

# 扩展映射表
UNICODE_TO_ASCII = {
    # 常见emoji
    '\u26a0': '[WARNING]',      # [WARNING]️
    '\u2139': '[INFO]',         # [INFO]️  
    '\u274c': '[ERROR]',        # [ERROR]
    '\u2705': '[OK]',           # [OK]
    '\u2714': '[CHECK]',        # [CHECK]
    '\u2716': '[CROSS]',        # [CROSS]
    '\u2757': '[EXCLAMATION]',  # [EXCLAMATION]
    '\u2753': '[QUESTION]',     # [QUESTION]
    '\u2b55': '[CIRCLE]',       # [CIRCLE]
    '\u2747': '[SPARKLE]',      # [SPARKLE]
    
    # 彩色Emoji (可能需要处理多个代码点)
    '\U0001f9e0': '[BRAIN]',     # [BRAIN]
    '\U0001f4e6': '[ARCHIVE]',   # [ARCHIVE]
    '\U0001f4ca': '[CHART]',     # [CHART]
    '\U0001f4c1': '[FOLDER]',    # [FOLDER]
    '\U0001f4dd': '[NOTE]',      # [NOTE]
    '\U0001f4a4': '[SLEEP]',     # [SLEEP]
    '\U0001f50d': '[SEARCH]',    # [SEARCH]
    '\U0001f680': '[ROCKET]',    # [ROCKET]
    '\U0001f511': '[KEY]',       # [KEY]
    '\U0001f4c4': '[FILE]',      # [FILE]
    '\U0001f4be': '[SAVE]',      # [SAVE]
    '\u2728': '[SPARKLES]',      # [SPARKLES]
    '\U0001f4ad': '[INBOX]',     # 📭
    '\U0001f527': '[WRENCH]',    # [WRENCH]
    '\U0001f528': '[HAMMER]',    # [HAMMER]
    '\U0001f4cb': '[CLIPBOARD]', # [CLIPBOARD]
    '\U0001f4da': '[BOOKS]',     # [BOOKS]
    '\U0001f5c3': '[FOLDER_DARK]', # [FOLDER_DARK]
    '\U0001f4c9': '[CHART_DOWN]',  # [CHART_DOWN]
    '\U0001f4c8': '[CHART_UP]',    # [CHART_UP]
    
    # 动物和表情
    '\U0001f408': '[CAT]',       # [CAT]
    '\U0001f43e': '[PAW]',       # [PAW]
    '\U0001f600': '[HAPPY]',     # [HAPPY]
    '\U0001f603': '[SMILE]',     # [SMILE]
    '\U0001f606': '[LAUGH]',     # [LAUGH]
    '\U0001f622': '[CRY]',       # [CRY]
    '\U0001f62d': '[SOB]',       # [SOB]
    '\U0001f625': '[SAD]',       # [SAD]
    
    # 符号
    '\u2702': '[SCISSORS]',      # [SCISSORS]️
    '\u2709': '[ENVELOPE]',      # [ENVELOPE]
    '\u270f': '[PENCIL]',        # [PENCIL]
    '\u2712': '[PEN]',           # [PEN]
    '\u2764': '[HEART]',         # [HEART]
    
    # 添加更多...
}

def safe_encode(text: str) -> str:
    """将文本中的Unicode字符安全编码为ASCII"""
    # 构建正则表达式模式
    pattern = re.compile('|'.join(re.escape(k) for k in UNICODE_TO_ASCII.keys()))
    
    def replace_char(match):
        char = match.group(0)
        return UNICODE_TO_ASCII.get(char, '[UNKNOWN]')
    
    return pattern.sub(replace_char, text)

def process_file(filepath: str):
    """处理单个Python文件"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查是否需要处理
        needs_fix = any(char in content for char in UNICODE_TO_ASCII.keys())
        if not needs_fix:
            return False
        
        # 替换Unicode字符
        new_content = safe_encode(content)
        
        # 写回文件
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        return True
    except Exception as e:
        print(f"[ERROR] 处理文件 {filepath} 失败: {e}")
        return False

def main():
    """主函数"""
    if len(sys.argv) > 1:
        files = sys.argv[1:]
    else:
        # 处理当前目录下所有.py文件
        files = [f for f in os.listdir('.') if f.endswith('.py')]
    
    print(f"正在处理 {len(files)} 个文件...")
    
    fixed_count = 0
    for filepath in files:
        if not os.path.exists(filepath):
            print(f"[WARNING] 文件不存在: {filepath}")
            continue
            
        print(f"处理: {filepath}")
        if process_file(filepath):
            print(f"  [OK] 已修复")
            fixed_count += 1
        else:
            print(f"  [INFO] 无需修复")
    
    print(f"\n处理完成，修复了 {fixed_count} 个文件")

if __name__ == "__main__":
    main()