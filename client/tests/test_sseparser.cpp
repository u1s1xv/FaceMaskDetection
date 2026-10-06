// SseParser 单元测试。
//
// 重点覆盖"半帧"：TCP 是字节流，事件边界和 read() 的返回边界没有任何关系。
// 这是真实线上最容易出错、又最难靠手工点击复现的地方，所以必须用单测钉死。

#include <QtTest>

#include "core/SseParser.h"

#include "test_runner.h"

class TestSseParser : public QObject
{
    Q_OBJECT

private slots:
    void singleFrame();
    void multipleFramesInOneChunk();
    void frameSplitAcrossChunks();
    void splitAtDelimiterBoundary();
    void crlfLineEndings();
    void malformedJsonIsSkipped();
    void commentLinesIgnored();
    void resetClearsPendingBuffer();
    void byteByByteFeed();
};

namespace {
QByteArray frame(const QByteArray &json) { return "data: " + json + "\n\n"; }
}

void TestSseParser::singleFrame()
{
    fmd::SseParser parser;
    const auto events = parser.feed(frame(R"({"type":"content","text":"hello"})"));
    QCOMPARE(events.size(), 1);
    QCOMPARE(events.at(0).type, QStringLiteral("content"));
    QCOMPARE(events.at(0).text, QStringLiteral("hello"));
    QCOMPARE(parser.pendingBytes(), 0);
}

void TestSseParser::multipleFramesInOneChunk()
{
    fmd::SseParser parser;
    QByteArray chunk;
    chunk += frame(R"({"type":"start","model":"m","mock":true})");
    chunk += frame(R"({"type":"content","text":"a"})");
    chunk += frame(R"({"type":"content","text":"b"})");
    chunk += frame(R"({"type":"done"})");

    const auto events = parser.feed(chunk);
    QCOMPARE(events.size(), 4);
    QCOMPARE(events.at(0).type, QStringLiteral("start"));
    QCOMPARE(events.at(1).text, QStringLiteral("a"));
    QCOMPARE(events.at(2).text, QStringLiteral("b"));
    QCOMPARE(events.at(3).type, QStringLiteral("done"));
}

// 一个完整帧被拆成两次 feed —— 第一次不该吐出任何事件
void TestSseParser::frameSplitAcrossChunks()
{
    fmd::SseParser parser;
    const QByteArray whole = frame(R"({"type":"content","text":"split"})");
    const int cut = whole.size() / 2;

    const auto first = parser.feed(whole.left(cut));
    QCOMPARE(first.size(), 0);
    QVERIFY(parser.pendingBytes() > 0);

    const auto second = parser.feed(whole.mid(cut));
    QCOMPARE(second.size(), 1);
    QCOMPARE(second.at(0).text, QStringLiteral("split"));
    QCOMPARE(parser.pendingBytes(), 0);
}

// 正好在 "\n\n" 分隔符中间断开：第一块以 \n 结尾，第二块以 \n 开头
void TestSseParser::splitAtDelimiterBoundary()
{
    fmd::SseParser parser;
    const QByteArray whole = frame(R"({"type":"content","text":"x"})");
    QVERIFY(whole.endsWith("\n\n"));

    const auto first = parser.feed(whole.left(whole.size() - 1));   // 只剩一个 \n
    QCOMPARE(first.size(), 0);

    const auto second = parser.feed("\n");
    QCOMPARE(second.size(), 1);
    QCOMPARE(second.at(0).text, QStringLiteral("x"));
}

void TestSseParser::crlfLineEndings()
{
    fmd::SseParser parser;
    const auto events = parser.feed("data: {\"type\":\"content\",\"text\":\"crlf\"}\r\n\r\n");
    QCOMPARE(events.size(), 1);
    QCOMPARE(events.at(0).text, QStringLiteral("crlf"));
}

// 坏帧必须被丢弃，且不能影响后面的正常帧
void TestSseParser::malformedJsonIsSkipped()
{
    fmd::SseParser parser;
    QByteArray chunk;
    chunk += frame("{ this is not json");
    chunk += frame(R"({"type":"content","text":"good"})");

    const auto events = parser.feed(chunk);
    QCOMPARE(events.size(), 1);
    QCOMPARE(events.at(0).text, QStringLiteral("good"));
}

void TestSseParser::commentLinesIgnored()
{
    fmd::SseParser parser;
    const auto events = parser.feed(": keep-alive\n\ndata: {\"type\":\"done\"}\n\n");
    QCOMPARE(events.size(), 1);
    QCOMPARE(events.at(0).type, QStringLiteral("done"));
}

void TestSseParser::resetClearsPendingBuffer()
{
    fmd::SseParser parser;
    parser.feed("data: {\"type\":\"cont");
    QVERIFY(parser.pendingBytes() > 0);
    parser.reset();
    QCOMPARE(parser.pendingBytes(), 0);

    const auto events = parser.feed(frame(R"({"type":"done"})"));
    QCOMPARE(events.size(), 1);
}

// 极端情况：一次只喂一个字节，模拟最碎的 TCP 分片
void TestSseParser::byteByByteFeed()
{
    fmd::SseParser parser;
    QByteArray chunk;
    chunk += frame(R"({"type":"content","text":"abc"})");
    chunk += frame(R"({"type":"done"})");

    int contentCount = 0;
    int doneCount = 0;
    for (int i = 0; i < chunk.size(); ++i) {
        for (const fmd::SseParser::Event &event : parser.feed(chunk.mid(i, 1))) {
            if (event.type == QLatin1String("content")) {
                ++contentCount;
                QCOMPARE(event.text, QStringLiteral("abc"));
            } else if (event.type == QLatin1String("done")) {
                ++doneCount;
            }
        }
    }
    QCOMPARE(contentCount, 1);
    QCOMPARE(doneCount, 1);
}

int runSseParserTests(int argc, char *argv[])
{
    TestSseParser test;
    return QTest::qExec(&test, argc, argv);
}

#include "test_sseparser.moc"
