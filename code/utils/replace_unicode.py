#!/usr/bin/env python3
# 替换Unicode表情符号为ASCII文本

import re

# 映射表
unicode_to_ascii = {
    '\u26a0': '[WARN]',  # [WARNING]️
    '\u2139': '[INFO]',  # [INFO]️
    '\u274c': '[ERROR]',  # [ERROR]
    '\U0001f9e0': '[大脑]',  # [BRAIN]
    '\U0001f4e6': '[归档]',  # [ARCHIVE]
    '\U0001f4ca': '[统计]',  # [CHART]
    '\U0001f4c1': '[目录]',  # [FOLDER]
    '\U0001f4dd': '[笔记]',  # [NOTE]
    '\U0001f4a4': '[睡眠]',  # [SLEEP]
    '\U0001f50d': '[检索]',  # [SEARCH]
    '\U0001f680': '[启动]',  # [ROCKET]
    '\U0001f511': '[钥匙]',  # [KEY]
    '\u2705': '[完成]',  # [OK]
    '\U0001f4c4': '[文件]',  # [FILE]
    '\U0001f4be': '[保存]',  # [SAVE]
    '\u2728': '[闪光]',  # [SPARKLES]
    '\U0001f4ad': '[空箱]',  # 📭
    '\u2702': '[剪刀]',  # [SCISSORS]️
    '\U0001f4cb': '[列表]',  # [CLIPBOARD]
}

def replace_unicode(match):
    char = match.group(0)
    return unicode_to_ascii.get(char, char)

# 读取文件
with open('openclaw_memory_engine_fixed.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 替换所有Unicode表情符号
pattern = re.compile('|'.join(re.escape(k) for k in unicode_to_ascii.keys()))
new_content = pattern.sub(replace_unicode, content)

# 写回文件
with open('openclaw_memory_engine_fixed.py', 'w', encoding='utf-8') as f:
    f.write(new_content)

print("[OK] 已替换Unicode字符")