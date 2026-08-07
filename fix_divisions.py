"""修复整除除数可能为 0 的问题"""
import os
import re

FIXES = [
    # 1. width // len(resources) -> width // max(1, len(resources))
    (r'(?P<v1>\w+)\s*=\s*(?P<w>\w+)\s*//\s*len\(resources\)(?!\s*if)',
     r'\g<v1> = \g<w> // max(1, len(resources))'),

    # 2. (xxx) // items_per_row -> (xxx) // max(1, items_per_row)
    (r'\)\s*//\s*items_per_row\b(?!\s*if)',
     r') // max(1, items_per_row)'),

    # 3. rows = (xxx) // cols 未保护
    (r'(?P<v1>\w+)\s*=\s*\([^)]+\)\s*//\s*cols\b(?!\s*if)',
     None),  # 单独处理：改为手动加 max(1, cols)
    # 使用更通用模式处理
    (r'(?P<v1>rows)\s*=\s*(?P<expr>\([^)]+\))\s*//\s*(?P<cols>cols)\b(?!\s*if\s+\w+\s*>\s*0)',
     None),

    # 4. color_width = (...) // color_count
    (r'(?P<v1>\w+_width)\s*=\s*\([^)]+\)\s*//\s*(?P<cc>color_count)\b(?!\s*if)',
     None),

    # 5. row = i // cols
    (r'(?P<v>\w+)\s*=\s*(?P<i>\w+)\s*//\s*(cols)\b(?!\s*if\s+cols)',
     None),

    # 6. color_index = (xxx) // color_width
    (r'(color_index)\s*=\s*\([^)]+\)\s*//\s*(color_width)\b(?!\s*if)',
     None),
]


def fix_width_len_resources(content):
    pattern = r'(\w+)\s*=\s*(\w+)\s*//\s*len\(resources\)(?!\s*if\s+len\(resources\))'
    def repl(m):
        return f"{m.group(1)} = {m.group(2)} // max(1, len(resources))"
    return re.subn(pattern, repl, content)

def fix_items_per_row(content):
    pattern = r'\)\s*//\s*items_per_row\b(?!\s*if\s+items_per_row)'
    return re.subn(pattern, ') // max(1, items_per_row)', content)

def fix_color_count(content):
    pattern = r'(\w+_width)\s*=\s*(\([^)]+\))\s*//\s*color_count\b(?!\s*if\s+color_count)'
    def repl(m):
        return f"{m.group(1)} = {m.group(2)} // max(1, color_count)"
    return re.subn(pattern, repl, content)

def fix_rows_by_cols(content):
    pattern = r'(rows)\s*=\s*(\([^)]+\))\s*//\s*cols\b(?!\s*if\s+cols)'
    def repl(m):
        return f"{m.group(1)} = {m.group(2)} // max(1, cols)"
    return re.subn(pattern, repl, content)

def fix_index_by_cols(content):
    pattern = r'(row|col)\s*=\s*(\w+)\s*//\s*cols\b(?!\s*if\s+cols)'
    def repl(m):
        return f"{m.group(1)} = {m.group(2)} // max(1, cols)"
    return re.subn(pattern, repl, content)

def fix_color_index(content):
    pattern = r'(color_index)\s*=\s*(\([^)]+\))\s*//\s*color_width\b(?!\s*if\s+color_width)'
    def repl(m):
        return f"{m.group(1)} = {m.group(2)} // max(1, color_width)"
    return re.subn(pattern, repl, content)


FIX_FUNCS = [
    fix_width_len_resources,
    fix_items_per_row,
    fix_color_count,
    fix_rows_by_cols,
    fix_index_by_cols,
    fix_color_index,
]


def fix_file(path):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        return 0
    total = 0
    for fn in FIX_FUNCS:
        content, n = fn(content)
        total += n
    if total > 0:
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"  修复 {total} 处: {os.path.basename(path)}")
    return total

def main():
    import sys
    target = sys.argv[1] if len(sys.argv) > 1 else '.'
    tf = 0
    tt = 0
    for root, dirs, files in os.walk(target):
        if any(x in root for x in ('venv', '__pycache__', 'site-packages', '.git')):
            continue
        for f in files:
            if f.endswith('.py'):
                n = fix_file(os.path.join(root, f))
                if n:
                    tf += 1
                tt += n
    print(f"\n修改文件数: {tf}, 总修改处: {tt}")

if __name__ == '__main__':
    main()
