"""
检查批量替换后是否有断裂引用：
  - 调用了 draw_gradient_bg 但没 import
  - 调用了 get_font 但没 import
  - 调用了 cull_dead 但没 import
  - 调用了 render_text 但没 import
  - 调用了 refresh_sound_volume 但没 import
"""
import os, re

ROOT = r'c:\Users\a\Desktop\san_guo\Android\ASSET'

SYMBOLS = ['draw_gradient_bg', 'get_font', 'cull_dead', 'render_text', 'refresh_sound_volume']

issues = []
for fn in sorted(os.listdir(ROOT)):
    if not fn.endswith('.py'):
        continue
    path = os.path.join(ROOT, fn)
    with open(path, 'r', encoding='utf-8') as f:
        src = f.read()
    
    for sym in SYMBOLS:
        # 检查是否调用了该符号（排除 import 行和注释和 game_data.py 自身定义）
        if fn == 'game_data.py':
            continue
        # 找调用点：sym( 或 sym. 但不是 import 行
        call_pattern = re.compile(r'\b' + re.escape(sym) + r'\s*[\(.]')
        calls = [(i+1, line.strip()[:120]) for i, line in enumerate(src.splitlines())
                 if call_pattern.search(line) and not line.strip().startswith('#')
                 and not re.match(r'(from|import)\s', line.strip())]
        if not calls:
            continue
        # 检查是否 import 了
        import_pattern = re.compile(
            r'from\s+ASSET\.game_data\s+import\s+[^\n]*\b' + re.escape(sym) + r'\b'
            r'|from\s+game_data\s+import\s+[^\n]*\b' + re.escape(sym) + r'\b'
        )
        if not import_pattern.search(src):
            for ln, line in calls[:3]:
                issues.append(f"[缺失import] {fn}:{ln}  调用 {sym}() 但未 import  | {line}")

if issues:
    print(f"发现 {len(issues)} 处断裂引用：")
    for it in issues:
        print(f"  {it}")
else:
    print("无断裂引用，所有调用都有对应 import")
