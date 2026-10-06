#include "core/MjpegParser.h"

#include <QList>

namespace fmd {

namespace {
// 头部最长允许多少字节。正常只有两三行，超过说明流已经乱了，
// 不如丢弃重建，免得缓冲无限增长。
constexpr int kMaxHeaderBytes = 8192;
constexpr char kCrLf[] = "\r\n";
}

MjpegParser::MjpegParser(const QByteArray &boundary)
{
    setBoundary(boundary);
}

void MjpegParser::setBoundary(const QByteArray &boundary)
{
    // 允许调用方传 "fmd_frame" 或 "--fmd_frame"，统一带上前置的 --
    QByteArray b = boundary;
    if (!b.startsWith("--"))
        b.prepend("--");
    m_boundary = b;
    reset();
}

void MjpegParser::reset()
{
    m_buffer.clear();
    m_frameCount    = 0;
    m_bytesReceived = 0;
    m_bytesParsed   = 0;
}

QByteArray MjpegParser::bufferedPreview(int maxBytes) const
{
    return m_buffer.left(maxBytes);
}

QVector<QByteArray> MjpegParser::feed(const QByteArray &data)
{
    QVector<QByteArray> frames;
    if (m_boundary.isEmpty())
        return frames;

    m_bytesReceived += data.size();
    m_buffer.append(data);

    while (true) {
        // ---- 1) 定位分隔符 ----
        const int bpos = m_buffer.indexOf(m_boundary);
        if (bpos < 0) {
            // 缓冲里没有完整分隔符。尾部可能是被截断的分隔符，必须留着；
            // 其余部分已经不可能组成帧了，丢掉以免缓冲无限增长。
            const int keep = m_boundary.size() - 1;
            if (m_buffer.size() > keep) {
                const int drop = m_buffer.size() - keep;
                m_bytesParsed += drop;
                m_buffer.remove(0, drop);
            }
            break;
        }

        // 分隔符之前是前导垃圾或上一帧尾部的 CRLF，丢弃
        if (bpos > 0) {
            m_bytesParsed += bpos;
            m_buffer.remove(0, bpos);
        }

        // ---- 2) 结束标记 "--boundary--" ----
        if (m_buffer.size() >= m_boundary.size() + 2
            && m_buffer.startsWith(m_boundary + "--")) {
            m_bytesParsed += m_buffer.size();
            m_buffer.clear();
            break;
        }

        int headerStart = m_boundary.size();
        if (m_buffer.size() < headerStart + 2)
            break;                       // 连分隔符后的 CRLF 都还没收全
        if (m_buffer.mid(headerStart, 2) == kCrLf)
            headerStart += 2;

        // ---- 3) 头部结束（空行）----
        const int headerEnd = m_buffer.indexOf("\r\n\r\n", headerStart);
        if (headerEnd < 0) {
            if (m_buffer.size() > kMaxHeaderBytes) {
                // 头部异常地长，说明流已经错位；丢弃到分隔符之后重建
                m_bytesParsed += headerStart;
                m_buffer.remove(0, headerStart);
                continue;
            }
            break;                       // 头部还没收全，等下一次
        }

        const QByteArray headers = m_buffer.mid(headerStart, headerEnd - headerStart);

        // ---- 4) 解析 Content-Length ----
        int contentLength = -1;
        const QList<QByteArray> lines = headers.split('\n');
        for (const QByteArray &line : lines) {
            const QByteArray trimmed = line.trimmed();
            if (trimmed.toLower().startsWith("content-length:")) {
                bool ok = false;
                const int value = trimmed.mid(15).trimmed().toInt(&ok);
                if (ok && value >= 0)
                    contentLength = value;
                break;
            }
        }

        if (contentLength < 0) {
            // 没有长度字段就无法定位帧尾。丢掉这段头部继续找下一个分隔符，
            // 而不是卡死在这里 —— 流已经不符合预期，但不能让客户端失去响应。
            const int drop = headerEnd + 4;
            m_bytesParsed += drop;
            m_buffer.remove(0, drop);
            continue;
        }

        // ---- 5) 帧体 ----
        const int bodyStart = headerEnd + 4;
        if (m_buffer.size() < bodyStart + contentLength)
            break;                       // 帧还没收全，等下一次

        frames.append(m_buffer.mid(bodyStart, contentLength));
        const int consumed = bodyStart + contentLength;
        m_bytesParsed += consumed;
        m_buffer.remove(0, consumed);
        ++m_frameCount;
    }

    return frames;
}

} // namespace fmd
