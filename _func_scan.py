"""扫描超长函数 — 可读性结构分析"""
import os, re

ROOT = r'c:\Users\a\Desktop\san_guo\Android\ASSET'
SKIP = {'test_optimization.py', 'test_migration.py', 'test_custom_hero_editor.py',
        'simple_test.py', '_bug_scan3.py', '_bug_scan4.py', '_func_scan.py'}

results = []

for fn in sorted(os.listdir(ROOT)):
    if not fn.endswith('.py') or fn in SKIP:
        continue
    path = os.path.join(ROOT, fn)
    with open(path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    func_starts = []
    for i, line in enumerate(lines):
        # 匹配 def 或 class 定义
        m = re.match(r'^(    |\t)*def\s+(\w+)\s*\(', line)
        if m:
            indent = len(line) - len(line.lstrip())
            func_starts.append((i, m.group(2), indent))

    for idx, (start, name, indent) in enumerate(func_starts):
        # 找函数结束：下一个同级或更少缩进的非空行
        end = len(lines)
        for j in range(start + 1, len(lines)):
            line = lines[j]
            if line.strip() and not line.strip().startswith('#'):
                cur_indent = len(line) - len(line.lstrip())
                if cur_indent <= indent and not line.strip().startswith(')'):
                    end = j
                    break
        length = end - start
        if length >= 80:  # 超过80行的函数
            results.append((length, fn, start + 1, name))

results.sort(reverse=True)
print(f"超长函数（≥80行）：共 {len(results)} 个\n")
print(f"{'行数':>6}  {'文件':<30} {'行号':>6}  函数名")
print("-" * 70)
for length, fn, line, name in results[:30]:
    print(f"{length:>6}  {fn:<30} {line:>6}  {name}")
if len(results) > 30:
    print(f"\n... 还有 {len(results)-30} 个")
