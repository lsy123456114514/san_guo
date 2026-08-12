"""深度 Bug 扫描 - 检查除零风险、空列表访问、未检查 None 返回等运行时问题。"""
import os
import re

ROOT = r'c:\Users\a\Desktop\san_guo\Android\ASSET'
SKIP = {'test_optimization.py', 'test_migration.py', 'test_custom_hero_editor.py',
        'simple_test.py', '_bug_scan3.py', '_bug_scan4.py'}

DIV_VARS = {'height', 'width', 'total', 'max_val', 'min_val', 'count', 'len',
            'size', 'duration', 'alpha', 'ratio', 'denominator', 'divisor',
            'max_life', 'max_hp', 'max_mp', 'speed', 'distance', 'delta',
            'difference', 'remaining', 'capacity', 'limit', 'interval'}

results = []

for fn in sorted(os.listdir(ROOT)):
    if not fn.endswith('.py') or fn in SKIP:
        continue
    path = os.path.join(ROOT, fn)
    with open(path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    for i, line in enumerate(lines, 1):
        s = line.strip()
        # 跳过注释和字符串
        if s.startswith('#') or s.startswith('"""') or s.startswith("'''"):
            continue

        # D1: 除零风险 — / variable 且周围无 max/min/if 保护
        for m in re.finditer(r'/\s*(\w+)\s*[\)\s,;\]]', s):
            var = m.group(1)
            if var in DIV_VARS and 'max(' not in s and 'min(' not in s:
                # 排除整除 // 和注释
                if '//' not in s[:m.start()+1] and '#' not in s:
                    results.append(('D1_div_zero', fn, i, s[:120]))

        # D2: 空列表访问 [0] 无 len 检查
        if re.search(r'\b(\w+)\[0\]', s) and 'len(' not in s and 'if ' not in s and '#' not in s:
            results.append(('D2_idx0', fn, i, s[:120]))

        # D3: 空列表访问 [-1]
        if re.search(r'\b(\w+)\[-1\]', s) and 'len(' not in s and 'if ' not in s and '#' not in s:
            results.append(('D3_idx_neg1', fn, i, s[:120]))

        # D4: .get() 后直接算术（可能 None）
        if re.search(r'\.get\([^)]+\)\s*[+\-*/]', s) and 'or ' not in s and 'if ' not in s:
            results.append(('D4_get_arith', fn, i, s[:120]))

        # D5: float() / int() 无 try 保护（可能 ValueError）
        if re.search(r'\b(float|int)\s*\([^)]+\)', s) and 'try' not in s and 'except' not in s:
            # 排除 int(数字) 和 float(数字) 字面量
            inner = re.search(r'\b(float|int)\s*\(([^)]+)\)', s)
            if inner and not re.match(r'^[\d.\s+-]+$', inner.group(2).strip()):
                if 'render' not in s and 'blit' not in s:  # 排除渲染代码
                    results.append(('D5_cast_unsafe', fn, i, s[:120]))

from collections import Counter
cnt = Counter(r[0] for r in results)
print(f"深度扫描结果：共 {len(results)} 处潜在问题")
for k, v in cnt.most_common():
    print(f"  {k}: {v} 处")

for cat in sorted(set(r[0] for r in results)):
    subset = [r for r in results if r[0] == cat]
    print(f"\n=== {cat} ({len(subset)} 处) ===")
    for _, f, ln, s in subset[:20]:
        print(f"  {f}:{ln}  {s}")
    if len(subset) > 20:
        print(f"  ... 剩 {len(subset)-20} 条")
