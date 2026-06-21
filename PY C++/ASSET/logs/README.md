# 日志系统说明

## 概述
本项目使用统一的日志系统，所有日志和错误信息都会记录到文件中，不再打印到控制台。

## 文件结构

```
ASSET/
└── logs/
    ├── game.log      # 游戏运行日志
    ├── error.log     # 错误专用日志
    └── .gitkeep      # 确保目录被git跟踪
```

## 日志级别

### 1. log_info(message)
记录普通信息日志
```python
from ASSET.logger import log_info
log_info("游戏开始加载...")
```

### 2. log_warning(message)
记录警告信息
```python
from ASSET.logger import log_warning
log_warning("检测到未定义的设置项")
```

### 3. log_error(message)
记录错误信息（包含完整堆栈跟踪）
```python
from ASSET.logger import log_error
try:
    # 可能出错的代码
    pass
except Exception:
    log_error("保存文件失败")
```

### 4. log_exception(message)
记录异常信息（自动捕获堆栈）
```python
from ASSET.logger import log_exception
try:
    # 可能出错的代码
    pass
except Exception:
    log_exception("加载配置文件时发生异常")
```

### 5. log_debug(message)
记录调试信息
```python
from ASSET.logger import log_debug
log_debug(f"当前帧率: {fps}")
```

## 异常处理示例

### 方式1：使用log_exception（推荐）
```python
try:
    result = load_data()
except Exception:
    log_exception("加载数据失败")
```

### 方式2：使用log_error
```python
try:
    result = load_data()
except Exception as e:
    log_error(f"加载数据失败: {str(e)}")
```

### 方式3：在异常中手动传递
```python
try:
    result = load_data()
except Exception as e:
    import traceback
    error_msg = f"错误: {str(e)}\n堆栈:\n{traceback.format_exc()}"
    log_error(error_msg)
```

## 查看日志

### 查看完整日志
```bash
# Windows
notepad ASSET\logs\game.log

# 或直接打开文件
ASSET\logs\game.log
ASSET\logs\error.log
```

### 获取最近错误
```python
from ASSET.logger import get_recent_errors
errors = get_recent_errors()
print(errors)
```

## 日志格式

每条日志包含：
- **时间戳**: YYYY-MM-DD HH:MM:SS
- **日志级别**: [INFO] / [WARNING] / [ERROR] / [DEBUG]
- **消息内容**: 具体的日志信息
- **堆栈跟踪** (仅错误日志): 完整的异常堆栈信息

## 优势

1. **不干扰用户**: 控制台不再有杂乱的输出
2. **完整记录**: 所有错误都有完整堆栈跟踪
3. **便于调试**: 错误日志专门存放，快速定位问题
4. **持久化**: 日志文件会保留，可以事后分析

## 注意事项

- 日志文件会自动创建在 `ASSET/logs/` 目录下
- 错误日志同时写入 `game.log` 和 `error.log`
- 大日志文件可以定期清理或归档
- 日志记录失败时不会抛出异常，静默处理
