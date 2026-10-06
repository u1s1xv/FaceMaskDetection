cmake_minimum_required(VERSION 3.16)
project(FaceMaskClientTests LANGUAGES CXX)

set(CMAKE_RUNTIME_OUTPUT_DIRECTORY         ${CMAKE_BINARY_DIR}/bin)
set(CMAKE_RUNTIME_OUTPUT_DIRECTORY_DEBUG   ${CMAKE_BINARY_DIR}/bin)
set(CMAKE_RUNTIME_OUTPUT_DIRECTORY_RELEASE ${CMAKE_BINARY_DIR}/bin)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_AUTOMOC ON)

find_package(Qt5 5.15 REQUIRED COMPONENTS Core Test)

enable_testing()

add_executable(fmd_tests
    test_sseparser.cpp
    ../src/core/SseParser.h
    ../src/core/SseParser.cpp
)

target_include_directories(fmd_tests PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/../src)
target_link_libraries(fmd_tests PRIVATE Qt5::Core Qt5::Test)

if (MSVC)
    target_compile_options(fmd_tests PRIVATE /utf-8)
endif()

# 测试可执行文件同样是独立进程，也需要自带 Qt 运行时。
# 否则它会沿 PATH 加载到 D:\Qt\5.15.2\mingw81_64\bin 那套 MinGW 版 Qt
# （与 MSVC 构建不兼容），表现为测试程序直接崩溃、没有任何输出。
if (WIN32)
    get_target_property(_qt_core_location Qt5::Core IMPORTED_LOCATION_RELEASE)
    if (NOT _qt_core_location)
        get_target_property(_qt_core_location Qt5::Core IMPORTED_LOCATION)
    endif()
    get_filename_component(FMD_QT_BIN_DIR "${_qt_core_location}" DIRECTORY)
    set(FMD_WINDEPLOYQT "${FMD_QT_BIN_DIR}/windeployqt.exe")

    if (EXISTS "${FMD_WINDEPLOYQT}")
        add_custom_command(TARGET fmd_tests POST_BUILD
            COMMAND "${CMAKE_COMMAND}" -E env "PATH=${FMD_QT_BIN_DIR};$ENV{PATH}"
                    "${FMD_WINDEPLOYQT}"
                    "$<$<CONFIG:Debug>:--debug>$<$<NOT:$<CONFIG:Debug>>:--release>"
                    --no-translations --no-compiler-runtime --no-opengl-sw
                    "$<TARGET_FILE:fmd_tests>"
            COMMENT "部署 Qt 运行时到测试可执行文件旁")
    endif()
endif()

add_test(NAME sse_parser COMMAND fmd_tests)

# Visual Studio 生成器是多配置的，ctest 需要知道测哪个配置
set_tests_properties(sse_parser PROPERTIES ENVIRONMENT "QT_QPA_PLATFORM=offscreen")
