cmake_minimum_required(VERSION 3.16)
project(FaceMaskClientTests LANGUAGES CXX)

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

add_test(NAME sse_parser COMMAND fmd_tests)
