#pragma once

// 多个测试类共用一个可执行文件时的入口声明。
//
// Qt 的 QTEST_MAIN 宏会生成 main()，一个可执行文件里只能有一个。
// 所以每个测试文件导出一个 runner 函数，由 test_main.cpp 统一驱动。

int runSseParserTests(int argc, char *argv[]);
int runMjpegParserTests(int argc, char *argv[]);
