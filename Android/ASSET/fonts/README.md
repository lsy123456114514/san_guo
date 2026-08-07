# 字体文件说明

这个目录用于存放内置字体文件，以确保游戏在不同系统上都能正确显示中文。

## 当前使用的字体

- **字魂白鸽天行体(商用需授权).ttf** - 主要中文字体

> ⚠️ 注意：此字体文件商用需授权，请确保拥有合法使用权限。

## 字体降级方案

游戏内置了完善的字体降级机制：

1. **优先使用**：此目录下的内置字体文件（字魂白鸽天行体）
2. **然后尝试**：通过 `pygame.font.match_font()` 匹配系统字体路径
3. **接着尝试**：使用 `pygame.font.SysFont()` 加载系统字体
4. **最后兜底**：使用 Pygame 默认字体

支持的系统字体：
- Windows: Microsoft YaHei, Microsoft YaHei UI, SimHei, SimSun, NSimSun, Segoe UI, Arial
- macOS: PingFang SC, Hiragino Sans GB, STHeiti, Songti SC, Helvetica
- Linux: Noto Sans CJK SC, WenQuanYi Micro Hei, SimHei, DejaVu Sans

