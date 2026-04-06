#!/usr/bin/env python3
# 替换memory_engine目录下所有.py文件中的Unicode表情符号为ASCII文本
import re
import os

# 映射表
unicode_to_ascii = {
    '\u26a0': '[WARN]',      # [WARN]️
    '\u2139': '[INFO]',      # [INFO]️
    '\u274c': '[ERROR]',     # [ERROR]
    '\U0001f9e0': '[大脑]',  # [大脑]
    '\U0001f4e6': '[归档]',  # [归档]
    '\U0001f4ca': '[统计]',  # [统计]
    '\U0001f4c1': '[目录]',  # [目录]
    '\U0001f4dd': '[笔记]',  # [笔记]
    '\U0001f4a4': '[睡眠]',  # [睡眠]
    '\U0001f50d': '[检索]',  # [检索]
    '\U0001f680': '[启动]',  # [启动]
    '\U0001f511': '[钥匙]',  # [钥匙]
    '\u2705': '[完成]',      # [完成]
    '\U0001f4c4': '[文件]',  # [文件]
    '\U0001f4be': '[保存]',  # [保存]
    '\u2728': '[闪光]',      # [闪光]
    '\U0001f4ad': '[空箱]',  # 📭
    '\u2702': '[剪刀]',      # [剪刀]️
    '\U0001f4cb': '[列表]',  # [列表]
}

def replace_in_file(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        pattern = re.compile('|'.join(re.escape(k) for k in unicode_to_ascii.keys()))
        new_content = pattern.sub(lambda m: unicode_to_ascii.get(m.group(0), m.group(0)), content)
        
        if new_content != content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f"已处理: {filepath}")
            return True
        else:
            print(f"无更改: {filepath}")
            return False
    except Exception as e:
        print(f"错误处理 {filepath}: {e}")
        return False

def main():
    # 遍历memory_engine目录
    base_dir = os.path.dirname(os.path.abspath(__file__))
    processed = 0
    
    for root, dirs, files in os.walk(base_dir):
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                if replace_in_file(filepath):
                    processed += 1
    
    print(f"\n处理完成！共处理了 {processed} 个文件。")

if __name__ == '__main__':
    main()