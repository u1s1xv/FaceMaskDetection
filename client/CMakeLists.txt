cmake_minimum_required(VERSION 3.16)
project(FaceMaskClient VERSION 0.1.0 LANGUAGES CXX)

# 统一产物目录。Visual Studio 生成器是多配置的，默认会放到 build/Release、build/Debug，
# 路径随配置变化。这里固定成 build/bin，脚本和文档都只认一个路径。
set(CMAKE_RUNTIME_OUTPUT_DIRECTORY              ${CMAKE_BINARY_DIR}/bin)
set(CMAKE_RUNTIME_OUTPUT_DIRECTORY_DEBUG        ${CMAKE_BINARY_DIR}/bin)
set(CMAKE_RUNTIME_OUTPUT_DIRECTORY_RELEASE      ${CMAKE_BINARY_DIR}/bin)
set(CMAKE_RUNTIME_OUTPUT_DIRECTORY_RELWITHDEBINFO ${CMAKE_BINARY_DIR}/bin)
set(CMAKE_RUNTIME_OUTPUT_DIRECTORY_MINSIZEREL   ${CMAKE_BINARY_DIR}/bin)

# ---- C++ 标准 ----
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# ---- Qt 自动化工具（moc/rcc/uic）----
set(CMAKE_AUTOMOC ON)
set(CMAKE_AUTORCC ON)
set(CMAKE_AUTOUIC ON)

# ---- Qt5 (工业上位机主流版本) ----
find_package(Qt5 5.15 REQUIRED COMPONENTS Widgets Network LinguistTools)

set(FMD_SOURCES
    resources/resources.qrc
    src/main.cpp
    src/MainWindow.h
    src/MainWindow.cpp
    src/core/Protocol.h
    src/core/Protocol.cpp
    src/core/BackendClient.h
    src/core/BackendClient.cpp
    src/core/SseParser.h
    src/core/SseParser.cpp
    src/core/MjpegParser.h
    src/core/MjpegParser.cpp
    src/core/BackendProcess.h
    src/core/BackendProcess.cpp
    src/core/ChildProcessJob.h
    src/core/ChildProcessJob.cpp
    src/views/BackendStatusView.h
    src/views/BackendStatusView.cpp
    src/views/DetectView.h
    src/views/DetectView.cpp
    src/views/BatchView.h
    src/views/BatchView.cpp
    src/workers/BatchController.h
    src/workers/BatchController.cpp
    src/models/HistoryModel.h
    src/models/HistoryModel.cpp
    src/models/HistoryProxy.h
    src/models/HistoryProxy.cpp
    src/views/HistoryView.h
    src/views/HistoryView.cpp
    src/views/ModelsView.h
    src/views/ModelsView.cpp
    src/views/SettingsView.h
    src/views/SettingsView.cpp
    src/views/LlmAnalysisDialog.h
    src/views/LlmAnalysisDialog.cpp
    src/views/ImageCanvas.h
    src/views/ImageCanvas.cpp
    src/views/DetectionItem.h
    src/views/DetectionItem.cpp
    src/views/VideoWidget.h
    src/views/VideoWidget.cpp
    src/views/LiveView.h
    src/views/LiveView.cpp
    src/widgets/PageHeader.h
    src/widgets/PageHeader.cpp
    src/widgets/StatCard.h
    src/widgets/StatCard.cpp
    src/workers/ImageLoaderTask.h
    src/workers/ImageLoaderTask.cpp
)

# ---- 国际化 ----
# qt5_create_translation 会先跑 lupdate 从源码抽取 tr() 字符串更新 .ts，
# 再跑 lrelease 生成 .qm。.ts 是给人改的（进版本库），.qm 是运行时用的（构建产物）。
set(FMD_TS_FILES
    ${CMAKE_CURRENT_SOURCE_DIR}/resources/i18n/fmd_zh_CN.ts
    ${CMAKE_CURRENT_SOURCE_DIR}/resources/i18n/fmd_en.ts
)
qt5_create_translation(FMD_QM_FILES ${CMAKE_CURRENT_SOURCE_DIR}/src ${FMD_TS_FILES})

add_executable(fmd_client ${FMD_SOURCES} ${FMD_QM_FILES})

# .qm 是运行时从可执行文件同级的 i18n/ 目录加载的
add_custom_command(TARGET fmd_client POST_BUILD
    COMMAND ${CMAKE_COMMAND} -E make_directory "$<TARGET_FILE_DIR:fmd_client>/i18n"
    COMMAND ${CMAKE_COMMAND} -E copy_if_different ${FMD_QM_FILES}
            "$<TARGET_FILE_DIR:fmd_client>/i18n"
)

target_include_directories(fmd_client PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/src)

target_link_libraries(fmd_client PRIVATE
    Qt5::Widgets
    Qt5::Network
)

# ---- 把 Qt 运行时部署到可执行文件旁边 ----
#
# 为什么必需：Windows 加载 DLL 的顺序是「exe 所在目录 > 系统目录 > PATH」。
# 本机 PATH 上有 D:\Qt\5.15.2\mingw81_64\bin（MinGW 版 Qt），与 MSVC 构建的 exe
# ABI 不兼容。若 exe 旁边没有 Qt DLL，裸跑就会加载到 MinGW 那套，报
# 「无法定位程序输入点 ?viewportSizeHint@QTableView@@...」。
# 把自己的 Qt 放在 exe 旁边，即可稳定压过 PATH 上的任何其它 Qt。
if (WIN32)
    get_target_property(_qt_core_location Qt5::Core IMPORTED_LOCATION_RELEASE)
    if (NOT _qt_core_location)
        get_target_property(_qt_core_location Qt5::Core IMPORTED_LOCATION)
    endif()
    get_filename_component(FMD_QT_BIN_DIR "${_qt_core_location}" DIRECTORY)
    set(FMD_WINDEPLOYQT "${FMD_QT_BIN_DIR}/windeployqt.exe")

    if (EXISTS "${FMD_WINDEPLOYQT}")
        add_custom_command(TARGET fmd_client POST_BUILD
            COMMAND "${CMAKE_COMMAND}" -E env "PATH=${FMD_QT_BIN_DIR};$ENV{PATH}"
                    "${FMD_WINDEPLOYQT}"
                    "$<$<CONFIG:Debug>:--debug>$<$<NOT:$<CONFIG:Debug>>:--release>"
                    --no-translations --no-compiler-runtime --no-opengl-sw
                    "$<TARGET_FILE:fmd_client>"
            COMMENT "部署 Qt 运行时到 $<TARGET_FILE_DIR:fmd_client>")
    else()
        message(WARNING "未找到 windeployqt: ${FMD_WINDEPLOYQT}，构建产物可能无法直接运行")
    endif()

    # windeployqt 默认只部署 qwindows.dll。无头验证（--selftest / --smoke-* 配合
    # QT_QPA_PLATFORM=offscreen）还需要 qoffscreen.dll，否则会以 "no Qt platform
    # plugin could be initialized" 直接崩掉。这个插件很小，一并带上。
    set(FMD_QT_PLUGIN_DIR "${FMD_QT_BIN_DIR}/../plugins")
    if (EXISTS "${FMD_QT_PLUGIN_DIR}/platforms/qoffscreen.dll")
        add_custom_command(TARGET fmd_client POST_BUILD
            COMMAND ${CMAKE_COMMAND} -E make_directory
                    "$<TARGET_FILE_DIR:fmd_client>/platforms"
            COMMAND ${CMAKE_COMMAND} -E copy_if_different
                    "${FMD_QT_PLUGIN_DIR}/platforms/qoffscreen.dll"
                    "$<TARGET_FILE_DIR:fmd_client>/platforms"
            COMMENT "部署 offscreen 平台插件（供无头验证使用）")
    endif()
endif()

# MSVC: UTF-8 源码 + 中文不乱码
if (MSVC)
    target_compile_options(fmd_client PRIVATE /utf-8)
endif()
