"""扫描缺失 docstring 的类（非函数）"""
import os, re

ROOT = r'c:\Users\a\Desktop\san_guo\Android\ASSET'
SKIP = {'test_optimization.py', 'test_migration.py', 'test_custom_hero_editor.py',
        'simple_test.py', '_bug_scan3.py', '_bug_scan4.py', '_func_scan.py',
        '_docstring_scan.py', '_class_scan.py'}

results = []

for fn in sorted(os.listdir(ROOT)):
    if not fn.endswith('.py') or fn in SKIP:
        continue
    path = os.path.join(ROOT, fn)
    with open(path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    for i, line in enumerate(lines):
        m = re.match(r'^class\s+(\w+)', line)
        if not m:
            continue
        name = m.group(1)

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
            results.append((fn, i + 1, name))

print(f"缺失 docstring 的类：共 {len(results)} 处\n")
for fn, line, name in results:
    print(f"  {fn}:{line}  class {name}")
