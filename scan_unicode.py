#!/usr/bin/env python3
import re
import sys

with open('code/examples/example_usage.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, line in enumerate(lines, 1):
    for j, ch in enumerate(line):
        if ord(ch) > 127:
            print(f"Line {i}, Col {j+1}: {repr(ch)} (U+{ord(ch):04X}) - {repr(line.strip()[:50])}")
            # 替换常见emoji
            if ch == '[大脑]':
                lines[i-1] = lines[i-1].replace('[大脑]', '[大脑]')
            elif ch == '😴':
                lines[i-1] = lines[i-1].replace('😴', '[睡眠]')
            elif ch == '⚙️':
                # ⚙️是两个字符：\u2699和\ufe0f
                lines[i-1] = lines[i-1].replace('⚙️', '[齿轮]')
            elif ch == '[检索]':
                lines[i-1] = lines[i-1].replace('[检索]', '[搜索]')
            elif ch == '[统计]':
                lines[i-1] = lines[i-1].replace('[统计]', '[统计]')
            elif ch == '[笔记]':
                lines[i-1] = lines[i-1].replace('[笔记]', '[笔记]')
            elif ch == '[钥匙]':
                lines[i-1] = lines[i-1].replace('[钥匙]', '[钥匙]')
            elif ch == '[启动]':
                lines[i-1] = lines[i-1].replace('[启动]', '[启动]')
            elif ch == '[保存]':
                lines[i-1] = lines[i-1].replace('[保存]', '[保存]')
            elif ch == '[闪光]':
                lines[i-1] = lines[i-1].replace('[闪光]', '[闪光]')

# 写回文件
with open('code/examples/example_usage.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print("处理完成")