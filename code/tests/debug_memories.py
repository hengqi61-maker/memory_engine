import json
import numpy as np

path = r'C:\Users\Lenovo\.openclaw\workspace\memory\engine\openclaw_memory.json'
print(f'检查文件: {path}')
try:
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
except Exception as e:
    print(f'读取错误: {e}')
    exit()

print(f'记忆数量: {len(data)}')
for i, item in enumerate(data):
    fact = item.get('fact', '无fact')
    memory_type = item.get('type', '未知')
    vec = item.get('vec', [])
    print(f'\n--- 记忆 {i} ---')
    print(f'类型: {memory_type}')
    print(f'事实: {fact[:100]}...')
    if vec:
        vec_np = np.array(vec)
        print(f'向量维度: {len(vec_np)}')
        print(f'向量范数: {np.linalg.norm(vec_np):.6f}')
        print(f'均值: {np.mean(vec_np):.6f}')
        print(f'标准差: {np.std(vec_np):.6f}')
        print(f'标准差: {np.std(vec_np):.6f}')
        # 检查是否为零向量
        if np.allclose(vec_np, 0):
            print('警告：零向量！')
        else:
            print('非零向量')
    else:
        print('无向量字段')

# 检查备份文件是否存在
backup_path = path + '.bak'
if os.path.exists(backup_path):
    print(f'\n[WARNING]️ 备份文件存在: {backup_path}')
    print('这可能影响记忆加载')