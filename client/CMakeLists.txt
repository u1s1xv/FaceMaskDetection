cmake_minimum_required(VERSION 3.16)
project(FaceMaskClient VERSION 0.1.0 LANGUAGES CXX)

# ---- C++ 标准 ----
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# ---- Qt 自动化工具（moc/rcc/uic）----
set(CMAKE_AUTOMOC ON)
set(CMAKE_AUTORCC ON)
set(CMAKE_AUTOUIC ON)

# ---- Qt5 (工业上位机主流版本) ----
find_package(Qt5 5.15 REQUIRED COMPONENTS Widgets Network)

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
    src/core/BackendProcess.h
    src/core/BackendProcess.cpp
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
    src/workers/ImageLoaderTask.h
    src/workers/ImageLoaderTask.cpp
)

add_executable(fmd_client ${FMD_SOURCES})

target_include_directories(fmd_client PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/src)

target_link_libraries(fmd_client PRIVATE
    Qt5::Widgets
    Qt5::Network
)

# MSVC: UTF-8 源码 + 中文不乱码
if (MSVC)
    target_compile_options(fmd_client PRIVATE /utf-8)
endif()
