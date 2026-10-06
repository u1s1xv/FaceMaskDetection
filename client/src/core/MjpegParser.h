#pragma once

// MJPEG 流增量解析器。
//
// 服务端以 multipart/x-mixed-replace 推流，格式如下：
//
//   --fmd_frame(CRLF)
//   Content-Type: image/jpeg(CRLF)
//   Content-Length: 28741(CRLF)
//   (CRLF)
//   <28741 字节的 JPEG>(CRLF)
//   --fmd_frame(CRLF)
//   ...
//
// 难点不在格式，而在**边界**：QNetworkReply 的 readyRead 到达时机是任意的，
// 一次可能只有半个头部、半个 JPEG，也可能一次来三帧。所以必须自己缓冲、
// 用状态机推进，不能假设"一次 readyRead 等于一帧"。
//
// 这与 SseParser 是同一类问题（增量协议解析 + TCP 半包），
// 只是分隔符与长度语义不同：SSE 以空行分隔且没有长度字段，
// 这里以 boundary 分隔且头部带 Content-Length。

#include <QByteArray>
#include <QVector>

namespace fmd {

class MjpegParser
{
public:
    explicit MjpegParser(const QByteArray &boundary = QByteArrayLiteral("fmd_frame"));

    // 投喂一段原始字节；返回本次能完整解析出的所有 JPEG 帧
    // （通常是 0 或 1 个，但网络突发时可能一次拿到多个）。
    QVector<QByteArray> feed(const QByteArray &data);

    void reset();
    void setBoundary(const QByteArray &boundary);

    int    frameCount()    const { return m_frameCount; }
    qint64 bytesReceived() const { return m_bytesReceived; }
    qint64 bytesParsed()   const { return m_bytesParsed; }
    int    bufferedBytes() const { return m_buffer.size(); }

    // 诊断用：解析中途卡住时，看看缓冲里积了什么
    QByteArray bufferedPreview(int maxBytes = 64) const;

private:
    QByteArray m_boundary;      // 完整分隔符，形如 --fmd_frame
    QByteArray m_buffer;
    int    m_frameCount    = 0;
    qint64 m_bytesReceived = 0;
    qint64 m_bytesParsed   = 0;
};

} // namespace fmd
