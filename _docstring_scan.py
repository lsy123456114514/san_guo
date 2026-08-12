"""扫描缺失 docstring 的函数和类"""
import os, re

ROOT = r'c:\Users\a\Desktop\san_guo\Android\ASSET'
SKIP = {'test_optimization.py', 'test_migration.py', 'test_custom_hero_editor.py',
        'simple_test.py', '_bug_scan3.py', '_bug_scan4.py', '_func_scan.py',
        '_docstring_scan.py'}

results = []

for fn in sorted(os.listdir(ROOT)):
    if not fn.endswith('.py') or fn in SKIP:
        continue
    path = os.path.join(ROOT, fn)
    with open(path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    for i, line in enumerate(lines):
        m = re.match(r'^(\s*)(def|class)\s+(\w+)', line)
        if not m:
            continue
        indent = m.group(1)
        name = m.group(3)
        kind = m.group(2)

        # 跳过魔术方法（__xxx__）和单下划线私有
        if name.startswith('__') and name.endswith('__') and name != '__init__':
            continue

        # 检查接下来几行是否有 docstring
        has_doc = False
        for j in range(i + 1, min(i + 5, len(lines))):
            stripped = lines[j].strip()
            if not stripped or stripped.startswith('#'):
                continue
            if stripped.startswith('"""') or stripped.startswith("'''"):
                has_doc = True
            break

        if not has_doc:
            results.append((fn, i + 1, kind, name))

# 按文件分组统计
from collections import Counter
file_counts = Counter(r[0] for r in results)
print(f"缺失 docstring 的函数/类：共 {len(results)} 处\n")
print(f"{'文件':<35} {'数量':>5}")
print("-" * 45)
for fn, cnt in file_counts.most_common(20):
    print(f"{fn:<35} {cnt:>5}")
if len(file_counts) > 20:
    print(f"\n... 还有 {len(file_counts)-20} 个文件")

print(f"\n=== 前30个缺失项 ===")
for fn, line, kind, name in results[:30]:
    print(f"  {fn}:{line}  {kind} {name}")
