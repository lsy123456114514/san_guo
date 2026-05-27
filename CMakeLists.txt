cmake_minimum_required(VERSION 3.15)
project(opengl_renderer LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Windows 特定配置
if(WIN32)
    # 链接 OpenGL 库
    if(CMAKE_BUILD_TYPE STREQUAL "Debug")
        add_definitions(-D_DEBUG)
    endif()
endif()

# 源文件
set(SOURCES
    opengl_renderer.cpp
)

# 创建动态库
add_library(opengl_renderer SHARED ${SOURCES})

# 包含目录
target_include_directories(opengl_renderer PRIVATE ${CMAKE_SOURCE_DIR})

# 链接库
target_link_libraries(opengl_renderer
    opengl32
    glu32
)

# 输出目录
set_target_properties(opengl_renderer PROPERTIES
    RUNTIME_OUTPUT_DIRECTORY ${CMAKE_SOURCE_DIR}
    LIBRARY_OUTPUT_DIRECTORY ${CMAKE_SOURCE_DIR}
    ARCHIVE_OUTPUT_DIRECTORY ${CMAKE_SOURCE_DIR}
)

# 复制 DLL 到输出目录（Windows）
if(WIN32)
    add_custom_command(TARGET opengl_renderer POST_BUILD
        COMMAND ${CMAKE_COMMAND} -E copy_if_different
            $<TARGET_FILE:opengl_renderer>
            ${CMAKE_SOURCE_DIR}/
    )
endif()

# 打印配置信息
message(STATUS "OpenGL Renderer Build Configuration:")
message(STATUS "  Build type: ${CMAKE_BUILD_TYPE}")
message(STATUS "  Output directory: ${CMAKE_SOURCE_DIR}")
