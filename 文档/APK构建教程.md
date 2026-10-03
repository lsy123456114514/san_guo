# 三国霸业 APK 本地构建教程

## 准备工作

### 1. 安装 Python 3.8+
确保你电脑上安装了较新版本的Python

### 2. 安装 Java JDK 11-17
下载并安装 Java JDK

### 3. 安装 Buildozer
```bash
pip install buildozer
```

### 4. 安装 Android SDK（或者让Buildozer自动下载）

## 开始构建

### 方法一：用Buildozer自动构建（推荐）

1. 打开命令行，进入项目目录
2. 运行：
   ```bash
   buildozer android debug
   ```
3. 等待10-30分钟（首次很慢，因为要下载很多东西）
4. 构建完成后，APK就在 `bin/` 文件夹里！

### 方法二：使用 BuildAPK（更简单）

或者安装 `buildapk` 工具（比buildozer简单）：

```bash
pip install buildapk
buildapk
```

## 常见问题

**问题：网络很慢？**
答：可以配置代理，或者用手机热点试试

**问题：缺少依赖？**
答：`pip install kivy pygame numpy requests pillow`

**问题：Java找不到？**
答：设置JAVA_HOME环境变量，指向JDK安装目录

## 构建成功后

APK文件在 `bin/sangoheroes-1.0.0-arm64-v8a-debug.apk`

把这个APK发到手机上安装即可！
