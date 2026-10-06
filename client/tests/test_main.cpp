// 测试可执行文件入口。
//
// 依次运行各个测试类，累加失败码。任一类失败则整体退出码非 0，
// 这样才能被 ctest / CI 判定为失败。

#include <QCoreApplication>
#include <QtTest>

#include "test_runner.h"

int main(int argc, char *argv[])
{
    QCoreApplication app(argc, argv);

    int failed = 0;
    failed += runSseParserTests(argc, argv);
    failed += runMjpegParserTests(argc, argv);

    return failed;
}
