@echo off
echo ====================================
echo 编译 OpenGL 渲染器 C++ DLL
echo ====================================

cd /d "%~dp0"

echo.
echo 检查编译环境...

:: 检查是否有 MSVC
where cl >nul 2>&1
if %errorlevel%==0 (
    echo 使用 MSVC 编译器
    goto :msvc_build
)

:: 检查是否有 MinGW
where g++ >nul 2>&1
if %errorlevel%==0 (
    echo 使用 MinGW 编译器
    goto :mingw_build
)

:: 检查是否有 CMake 和 Ninja/其他生成器
where cmake >nul 2>&1
if %errorlevel%==0 (
    echo 使用 CMake 构建
    goto :cmake_build
)

echo.
echo 错误: 未找到支持的编译器 (cl/g++/cmake)
echo 请安装以下之一:
echo   - Visual Studio (包含 MSVC)
echo   - MinGW-w64
echo   - CMake
echo.
echo 或者您可以手动编译:
echo   g++ -shared -fPIC -o opengl_renderer.dll opengl_renderer.cpp -lopengl32 -lglu32
echo.
pause
exit /b 1

:msvc_build
echo.
echo 开始 MSVC 编译...
cl /LD /EHsc /MD /O2 /I. opengl_renderer.cpp opengl32.lib glu32.lib /Fe:opengl_renderer.dll
if %errorlevel% neq 0 (
    echo 编译失败!
    pause
    exit /b 1
)
echo 编译成功: opengl_renderer.dll
goto :done

:mingw_build
echo.
echo 开始 MinGW 编译...
g++ -shared -fPIC -o opengl_renderer.dll opengl_renderer.cpp -lopengl32 -lglu32 -static-libgcc -static-libstdc++
if %errorlevel% neq 0 (
    echo 编译失败!
    pause
    exit /b 1
)
echo 编译成功: opengl_renderer.dll
goto :done

:cmake_build
echo.
echo 创建 build 目录...
if not exist build mkdir build
cd build

echo.
echo 运行 CMake...
cmake .. -G "MinGW Makefiles" -DCMAKE_BUILD_TYPE=Release
if %errorlevel% neq 0 (
    echo CMake 配置失败!
    cd ..
    rmdir /s /q build 2>nul
    pause
    exit /b 1
)

echo.
echo 编译...
cmake --build . --config Release
if %errorlevel% neq 0 (
    echo 编译失败!
    cd ..
    pause
    exit /b 1
)

echo.
echo 复制 DLL 到根目录...
copy /Y Release\opengl_renderer.dll ..\ 2>nul || copy /Y MinGW\opengl_renderer.dll ..\ 2>nul || true
cd ..

:done
echo.
echo ====================================
echo 编译完成！
echo ====================================
echo.
echo 生成的 DLL 文件: opengl_renderer.dll
echo.
pause
