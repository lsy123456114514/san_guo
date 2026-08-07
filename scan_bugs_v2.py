#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
综合 Bug 扫描工具 v2
检测维度：
1. 除零保护缺失（a/b 未判断 b!=0）
2. 空序列直接索引访问（lst[0]/lst[-1]/lst[i] 无 if 守卫）
3. 未关闭的文件句柄（open() 不用 with）
4. 裸 except: → except Exception:（提示，已修复过）
5. 零尺寸 Surface 创建（pygame.Surface((0, h)) / (w, 0)）
6. 渐变/进度条零尺寸（width<=0 或 height<=0 没 return）
7. 颜色越界（RGB 没夹制 0-255）
8. 循环内反复创建 Font（性能隐患）
9. 危险的 save() 调用（临时状态持久化）
10. import 缺失（使用 sys._MEIPASS 但没 import sys）
11. 嵌套 nested while 导致 CPU 爆炸
12. Slider 除零（max_val==min_val 或 width==0）
13. 字符串拼接/格式化变量可能 None
"""
import os
import re
import sys

PATTERNS = [
    # 1. 除零 —— 不包含 if 保护的单行
    ("division_no_guard",
     r"(?P<lhs>[\w\.]+)\s*/\s*(?P<rhs>[\w\.]+)(?!\s*if\s+\w+|.*if\s+\k<rhs>\s*>\s*0|.*if\s+\k<rhs>\s*!=\s*0|.*if\s+.*\b\k<rhs>\b)",
     "潜在除零（需判断右侧分母是否可能为 0）"),

    # 2. 空序列直接索引：访问 [0] / [-1] / [i] 不在 if len(...): 后
    ("empty_seq_index",
     r"(?P<var>[\w\.]+)\[(?:0|-1|\d+)\](?!\s*if\s+len\(\k<var>\)|.*if\s+\k<var>\s*)",
     "可能在空序列上直接索引"),

    # 3. 未关闭句柄：= open(...) 非 with 行
    ("unclosed_open",
     r"(?<!with\s)\b\w+\s*=\s*open\(",
     "可能未关闭的文件句柄（考虑用 with 语句）"),

    # 5. 零尺寸 Surface
    ("zero_size_surface",
     r"pygame\.Surface\(\(\s*\d+\s*,\s*0\s*\)|pygame\.Surface\(\(\s*0\s*,\s*\d+\s*\)|pygame\.Surface\(\(\s*0\s*,\s*0\s*\)|pygame\.Surface\(\(\s*w\s*,\s*0\s*\)|pygame\.Surface\(\(\s*0\s*,\s*h\s*\))",
     "可能创建零尺寸 Surface，导致崩溃"),

    # 6. 渐变矩形零尺寸：draw_gradient_rect 无 width/height 检查
    # (已在 modern_ui_system 中修复，提示其他实现)

    # 7. 颜色越界：RGB 计算无 clamp
    ("color_no_clamp",
     r"(?:r\s*=|g\s*=|b\s*=)\s*int\(\s*\d+\s*\*\s*\w+(\[0\]|\[1\]|\[2\])\s*\+\s*\d+\s*\*\s*\w+(?:\[0\]|\[1\]|\[2\])\s*\)(?!\s*.*max\(0,\s*min\(255)",
     "颜色计算可能越界，未夹制 0-255"),

    # 8. 循环内 Font 创建
    ("font_in_loop",
     r"(for|while)\s+.*\n.*\n.*pygame\.font\.Font\(",
     "循环内创建字体（性能内存隐患）"),

    # 9. 临时状态 save() 调用
    ("unnecessary_save",
     r"\bdef\s+(add_notification|draw_.*_ui|render_.*|_update_.*)\b.*\n.*\bsave\(\)",
     "临时状态函数调用 save() 持久化（性能隐患）"),

    # 10. 缺失 import sys 但使用 sys._MEIPASS
    ("missing_sys_import",
     r"sys\._MEIPASS",
     "使用 sys._MEIPASS 需确认文件顶部有 import sys"),

    # 11. 嵌套 while：while 中又 while
    ("nested_while",
     r"(while\s+.*\n(?:[ \t].*\n)*?[ \t]while\s+)",
     "嵌套 while 循环可能导致 CPU 占用爆炸（需加 Clock.tick）"),

    # 12. Slider 除零：(value - min) / (max - min) 无保护
    ("slider_division",
     r"\([\w\.]+\s*-\s*min_val\)\s*/\s*\(\s*max_val\s*-\s*min_val\s*\)(?!\s*if)",
     "Slider 分母可能为 0（max==min）"),

    # 13. 字典键直接访问但没 .get：data["xxx"] 无 try/except 或 get
    # (范围太大，仅检查常见高危路径)
    ("dangerous_key_access",
     r"data\[\"heroes\"\]\[\"[^\"]+\"\]\[\"attack\"\]|data\[\"resources\"\]\[\"[^\"]+\"\]",
     "多级字典键直接访问，若缺键会 KeyError（建议 safe_get）"),
]


def scan_file(path):
    """扫描单个文件，返回 (bugs, lines_count)"""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        return [(path, "READ_ERROR", 0, f"读取失败: {e}")], 0

    bugs = []
    lines = content.split('\n')
    lines_count = len(lines)

    # 预编译
    for name, pattern, desc in PATTERNS:
        try:
            for m in re.finditer(pattern, content, re.MULTILINE | re.DOTALL):
                # 计算行号
                pos = m.start()
                lineno = content[:pos].count('\n') + 1
                # 截取附近上下文
                context = lines[lineno - 1].strip() if 0 <= lineno - 1 < lines_count else m.group(0)[:80]
                bugs.append((path, name, lineno, f"{desc} | 上下文: {context[:120]}"))
        except re.error as e:
            bugs.append((path, "REGEX_ERROR", 0, f"正则 {name} 错误: {e}"))

    return bugs, lines_count


def main():
    target = sys.argv[1] if len(sys.argv) > 1 else '.'
    print(f"[扫描目录] {target}\n")
    all_bugs = []
    files_scanned = 0
    total_lines = 0

    for root, dirs, files in os.walk(target):
        if any(x in root for x in ('venv', '__pycache__', 'site-packages', '.git')):
            continue
        for f in files:
            if not f.endswith('.py'):
                continue
            path = os.path.join(root, f)
            bugs, lc = scan_file(path)
            files_scanned += 1
            total_lines += lc
            all_bugs.extend(bugs)

    print(f"[扫描结果] 文件: {files_scanned} 个, 总行数: {total_lines}, 潜在 Bug: {len(all_bugs)} 处\n")
    print("=" * 100)

    # 按类型分组
    by_type = {}
    for b in all_bugs:
        by_type.setdefault(b[1], []).append(b)

    for t, lst in sorted(by_type.items(), key=lambda x: -len(x[1])):
        print(f"\n--- [{t}] 共 {len(lst)} 处 ---")
        for path, name, lineno, desc in lst[:30]:
            rel = os.path.relpath(path, target)
            print(f"  - {rel}:{lineno}  {desc}")
        if len(lst) > 30:
            print(f"  ... (另 {len(lst) - 30} 处省略)")

    # 生成 TSV 报告便于检索
    report = os.path.join(os.path.dirname(__file__), 'bug_report_v2.tsv')
    with open(report, 'w', encoding='utf-8') as f:
        f.write("File\tLine\tType\tDescription\n")
        for path, name, lineno, desc in all_bugs:
            rel = os.path.relpath(path, target)
            f.write(f"{rel}\t{lineno}\t{name}\t{desc}\n")
    print(f"\n[报告] 已保存到: {report}")


if __name__ == '__main__':
    main()
