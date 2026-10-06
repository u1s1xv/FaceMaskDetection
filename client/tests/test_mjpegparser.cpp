#include <QtTest>

#include "core/MjpegParser.h"

#include "test_runner.h"

using namespace fmd;

namespace {

// 造一帧：--boundary CRLF Content-Type CRLF Content-Length CRLF CRLF <body>
QByteArray makePart(const QByteArray &boundary, const QByteArray &body)
{
    QByteArray part;
    part += "--" + boundary + "\r\n";
    part += "Content-Type: image/jpeg\r\n";
    part += "Content-Length: " + QByteArray::number(body.size()) + "\r\n";
    part += "\r\n";
    part += body;
    part += "\r\n";
    return part;
}

// 一个"看起来像 JPEG"的载荷：SOI ... EOI
QByteArray fakeJpeg(int payloadBytes, char fill = 'J')
{
    QByteArray body;
    body += char(0xFF); body += char(0xD8);
    body += QByteArray(payloadBytes, fill);
    body += char(0xFF); body += char(0xD9);
    return body;
}

} // namespace

class TestMjpegParser : public QObject
{
    Q_OBJECT

private slots:

    // ---- 基本形态 ----

    void singleFrameInOneFeed()
    {
        MjpegParser parser;
        const QByteArray jpeg = fakeJpeg(100);
        const auto frames = parser.feed(makePart("fmd_frame", jpeg));
        QCOMPARE(frames.size(), 1);
        QCOMPARE(frames.first(), jpeg);
        QCOMPARE(parser.frameCount(), 1);
    }

    void multipleFramesInOneFeed()
    {
        MjpegParser parser;
        QByteArray stream;
        for (int i = 0; i < 5; ++i)
            stream += makePart("fmd_frame", fakeJpeg(50 + i, char('A' + i)));

        const auto frames = parser.feed(stream);
        QCOMPARE(frames.size(), 5);
        for (int i = 0; i < 5; ++i)
            QCOMPARE(frames.at(i), fakeJpeg(50 + i, char('A' + i)));
    }

    // ---- 边界：TCP 拆包。这是整个类存在的理由 ----

    void frameSplitByteByByte()
    {
        MjpegParser parser;
        const QByteArray jpeg = fakeJpeg(200);
        const QByteArray stream = makePart("fmd_frame", jpeg);

        QVector<QByteArray> got;
        for (int i = 0; i < stream.size(); ++i)
            got += parser.feed(stream.mid(i, 1));   // 一次一个字节

        QCOMPARE(got.size(), 1);
        QCOMPARE(got.first(), jpeg);
    }

    void framesSplitAtEveryChunkSize()
    {
        // 用多种分块大小切同一段流，结果必须一致
        const QByteArray jpeg1 = fakeJpeg(120, 'X');
        const QByteArray jpeg2 = fakeJpeg(300, 'Y');
        const QByteArray stream = makePart("fmd_frame", jpeg1)
                                + makePart("fmd_frame", jpeg2);

        for (int chunk : { 1, 2, 3, 7, 13, 64, 100, 512, 1000 }) {
            MjpegParser parser;
            QVector<QByteArray> got;
            for (int pos = 0; pos < stream.size(); pos += chunk)
                got += parser.feed(stream.mid(pos, chunk));
            QCOMPARE(got.size(), 2);
            QCOMPARE(got.at(0), jpeg1);
            QCOMPARE(got.at(1), jpeg2);
        }
    }

    void splitInsideHeader()
    {
        MjpegParser parser;
        const QByteArray jpeg = fakeJpeg(80);
        const QByteArray stream = makePart("fmd_frame", jpeg);
        const int cut = stream.indexOf("Content-Length") + 5;   // 切在字段名中间

        QVERIFY(parser.feed(stream.left(cut)).isEmpty());
        const auto frames = parser.feed(stream.mid(cut));
        QCOMPARE(frames.size(), 1);
        QCOMPARE(frames.first(), jpeg);
    }

    void splitInsideBoundary()
    {
        MjpegParser parser;
        const QByteArray jpeg = fakeJpeg(80);
        const QByteArray stream = makePart("fmd_frame", jpeg);

        QVERIFY(parser.feed(stream.left(4)).isEmpty());   // "--fm"
        const auto frames = parser.feed(stream.mid(4));
        QCOMPARE(frames.size(), 1);
    }

    void splitInsideBody()
    {
        MjpegParser parser;
        const QByteArray jpeg = fakeJpeg(400);
        const QByteArray stream = makePart("fmd_frame", jpeg);
        const int bodyStart = stream.indexOf("\r\n\r\n") + 4;

        QVERIFY(parser.feed(stream.left(bodyStart + 100)).isEmpty());
        const auto frames = parser.feed(stream.mid(bodyStart + 100));
        QCOMPARE(frames.size(), 1);
        QCOMPARE(frames.first(), jpeg);
    }

    // ---- 内容里的"陷阱" ----

    void bodyContainingCrlfAndBoundaryBytes()
    {
        // 真实 JPEG 的熵编码数据里完全可能撞上 "--fmd_frame" 或 CRLF。
        // 因为用 Content-Length 定界，这些字节不应该影响解析。
        MjpegParser parser;
        QByteArray tricky = fakeJpeg(20);
        tricky += "\r\n--fmd_frame\r\nContent-Length: 999\r\n\r\n";
        tricky += fakeJpeg(30);

        const auto frames = parser.feed(makePart("fmd_frame", tricky));
        QCOMPARE(frames.size(), 1);
        QCOMPARE(frames.first(), tricky);
    }

    // ---- 异常与容错 ----

    void preambleBeforeFirstBoundary()
    {
        MjpegParser parser;
        const QByteArray jpeg = fakeJpeg(60);
        const auto frames = parser.feed("garbage line\r\n" + makePart("fmd_frame", jpeg));
        QCOMPARE(frames.size(), 1);
        QCOMPARE(frames.first(), jpeg);
    }

    void finalBoundaryEndsStream()
    {
        MjpegParser parser;
        const QByteArray jpeg = fakeJpeg(60);
        QByteArray stream = makePart("fmd_frame", jpeg);
        stream += "--fmd_frame--\r\n";

        const auto frames = parser.feed(stream);
        QCOMPARE(frames.size(), 1);
        QCOMPARE(parser.bufferedBytes(), 0);   // 结束标记被吃掉，没有残留
    }

    void missingContentLengthDoesNotHang()
    {
        // 没有 Content-Length 就无法定界。必须丢弃并继续，而不是卡死。
        MjpegParser parser;
        QByteArray bad = "--fmd_frame\r\nContent-Type: image/jpeg\r\n\r\n"
                         "no length here\r\n";
        const QByteArray good = fakeJpeg(70);

        const auto frames = parser.feed(bad + makePart("fmd_frame", good));
        QCOMPARE(frames.size(), 1);
        QCOMPARE(frames.first(), good);
    }

    void nonJpegBytesStillParsedByLength()
    {
        // 解析器只认 Content-Length，不校验 JPEG 魔数。
        // 校验交给上层（解码失败会返回空 QImage）。
        MjpegParser parser;
        const QByteArray body = "not a jpeg at all";
        const auto frames = parser.feed(makePart("fmd_frame", body));
        QCOMPARE(frames.size(), 1);
        QCOMPARE(frames.first(), body);
    }

    void emptyAndIrrelevantFeeds()
    {
        MjpegParser parser;
        QVERIFY(parser.feed(QByteArray()).isEmpty());
        QVERIFY(parser.feed("hello world").isEmpty());
        QCOMPARE(parser.frameCount(), 0);
        // 无关数据不能无限堆在缓冲里
        QVERIFY(parser.bufferedBytes() < 64);
    }

    void bufferDoesNotGrowUnbounded()
    {
        MjpegParser parser;
        for (int i = 0; i < 100; ++i)
            parser.feed(QByteArray(1024, 'z'));    // 没有任何分隔符的数据
        QVERIFY(parser.bufferedBytes() < 64);
    }

    // ---- 接口行为 ----

    void boundaryAcceptsWithOrWithoutDashes()
    {
        const QByteArray jpeg = fakeJpeg(40);
        for (const QByteArray &b : { QByteArray("fmd_frame"), QByteArray("--fmd_frame") }) {
            MjpegParser parser(b);
            const auto frames = parser.feed(makePart("fmd_frame", jpeg));
            QCOMPARE(frames.size(), 1);
        }
    }

    void resetClearsState()
    {
        MjpegParser parser;
        parser.feed(makePart("fmd_frame", fakeJpeg(50)));
        QCOMPARE(parser.frameCount(), 1);
        parser.reset();
        QCOMPARE(parser.frameCount(), 0);
        QCOMPARE(parser.bufferedBytes(), 0);
        QCOMPARE(parser.bytesReceived(), 0);
    }

    void byteAccounting()
    {
        // 这里断言的是**不变量**而不是某个具体数字：
        // 每帧体之后还有一个 CRLF，它要等下一个分隔符到达才会被消费，
        // 所以流末尾必然有少量字节留在缓冲里 —— 这是正常的，不是 bug。
        //   已接收 == 已消费 + 仍在缓冲
        MjpegParser parser;
        const QByteArray stream = makePart("fmd_frame", fakeJpeg(100))
                                + makePart("fmd_frame", fakeJpeg(100));
        parser.feed(stream);

        QCOMPARE(parser.bytesReceived(), qint64(stream.size()));
        QCOMPARE(parser.bytesParsed() + parser.bufferedBytes(),
                 parser.bytesReceived());
        QCOMPARE(parser.frameCount(), 2);
        // 残留不应超过一个分隔符的长度
        QVERIFY(parser.bufferedBytes() <= 16);
    }

    void byteAccountingInvariantHoldsAcrossChunks()
    {
        // 同样的不变量，在任意分块下都必须成立
        const QByteArray stream = makePart("fmd_frame", fakeJpeg(90))
                                + makePart("fmd_frame", fakeJpeg(150))
                                + makePart("fmd_frame", fakeJpeg(60));
        for (int chunk : { 1, 5, 32, 200, 4096 }) {
            MjpegParser parser;
            for (int pos = 0; pos < stream.size(); pos += chunk)
                parser.feed(stream.mid(pos, chunk));
            QCOMPARE(parser.bytesParsed() + parser.bufferedBytes(),
                     parser.bytesReceived());
            QCOMPARE(parser.frameCount(), 3);
        }
    }
};

int runMjpegParserTests(int argc, char *argv[])
{
    TestMjpegParser test;
    return QTest::qExec(&test, argc, argv);
}

#include "test_mjpegparser.moc"
