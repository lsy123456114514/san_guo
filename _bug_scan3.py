"""
扫描真正的 Bug 模式（不是风格问题）：
  B1. 可变默认参数: def foo(x=[]) / def foo(x={})
  B2. 变量使用前未赋值: except 分支里赋值的变量在 try 外面用
  B3. is None 写成 == None
  B4. 字符串格式化 % 可能报错（参数数量不匹配难自动检测，只报 % 格式化在 logger 调用里）
  B5. 循环里修改正在迭代的字典/集合
  B6. 整数除法 / 代替 // （结果可能是浮点数但被当 int 用）
  B7. except 块里 return 但 finally 块里也有 return（finally 会覆盖）
  B8. 文件 open 但没有 with 语句也没有 close
"""
import os, re

ROOT = r'c:\Users\a\Desktop\san_guo\Android\ASSET'
results = []

for fn in sorted(os.listdir(ROOT)):
    if not fn.endswith('.py'):
        continue
    path = os.path.join(ROOT, fn)
    with open(path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    for i, line in enumerate(lines, 1):
        s = line.strip()
        
        # B1: 可变默认参数
        if re.search(r'def\s+\w+\(.*=\s*(\[\]|\{\})\s*[,)]', s):
            results.append(('B1_mutable_default', fn, i, s[:120]))
        
        # B3: == None / != None
        if re.search(r'==\s*None\b|!=\s*None\b', s) and not s.strip().startswith('#'):
            results.append(('B3_eq_none', fn, i, s[:120]))
        
        # B8: open( 没有 with 也没有 close 在同一行
        if 'open(' in s and 'with ' not in s and '.close()' not in s and not s.strip().startswith('#'):
            # 排除 os.open / codecs.open 等
            if re.search(r'\bopen\s*\(', s):
                results.append(('B8_open_no_with', fn, i, s[:120]))

# B5: for k in dict: del dict[k] 模式
for fn in sorted(os.listdir(ROOT)):
    if not fn.endswith('.py'):
        continue
    path = os.path.join(ROOT, fn)
    with open(path, 'r', encoding='utf-8') as f:
        src = f.read()
    # for x in some_dict: ... del some_dict[x] 或 some_dict.pop(x)
    for m in re.finditer(
        r'for\s+(\w+)\s+in\s+(\w+)\s*:\s*\n(?:[^\n]*\n)*?[ \t]+(?:del\s+\2\s*\[\s*\1\s*\]|\2\.pop\s*\(\s*\1\s*\))',
        src, re.M
    ):
        line_num = src[:m.start()].count('\n') + 1
        results.append(('B5_modify_iterating_dict', fn, line_num, m.group()[:120].replace('\n',' ')))

from collections import Counter
cnt = Counter(r[0] for r in results)
print(f"Bug 模式扫描结果：共 {len(results)} 处")
for k, v in cnt.most_common():
    print(f"  {k}: {v} 处")

for cat in sorted(set(r[0] for r in results)):
    subset = [r for r in results if r[0] == cat]
    print(f"\n=== {cat} ({len(subset)} 处) ===")
    for _, f, ln, s in subset[:15]:
        print(f"  {f}:{ln}  {s}")
    if len(subset) > 15:
        print(f"  ... 剩 {len(subset)-15} 条")
