#include "SseParser.h"

#include <QJsonDocument>

namespace fmd {

namespace {
// SSE 规范里事件之间用空行分隔；兼容 \n\n 与 \r\n\r\n 两种换行
int findFrameEnd(const QByteArray &buffer, int *frameLength)
{
    const int lf = buffer.indexOf("\n\n");
    const int crlf = buffer.indexOf("\r\n\r\n");

    if (lf < 0 && crlf < 0)
        return -1;
    if (crlf >= 0 && (lf < 0 || crlf < lf)) {
        *frameLength = crlf + 4;
        return crlf;
    }
    *frameLength = lf + 2;
    return lf;
}
} // namespace

void SseParser::reset()
{
    m_buffer.clear();
}

QVector<SseParser::Event> SseParser::feed(const QByteArray &chunk)
{
    QVector<Event> events;
    m_buffer.append(chunk);

    for (;;) {
        int frameLength = 0;
        const int frameEnd = findFrameEnd(m_buffer, &frameLength);
        if (frameEnd < 0)
            break;                      // 剩下的是半帧，留在缓冲里等下一块

        const QByteArray frame = m_buffer.left(frameEnd);
        m_buffer.remove(0, frameLength);

        // 一个 frame 里可能有多个 "data:" 行，按规范用换行拼接
        QByteArray payload;
        for (const QByteArray &line : frame.split('\n')) {
            const QByteArray trimmed = line.trimmed();
            if (!trimmed.startsWith("data:"))
                continue;               // 忽略注释行(:开头)与其它字段
            if (!payload.isEmpty())
                payload.append('\n');
            payload.append(trimmed.mid(5).trimmed());
        }
        if (payload.isEmpty())
            continue;

        QJsonParseError parseError{};
        const QJsonDocument doc = QJsonDocument::fromJson(payload, &parseError);
        if (parseError.error != QJsonParseError::NoError || !doc.isObject())
            continue;                   // 坏帧直接丢弃，不能因为一个坏帧中断整条流

        Event event;
        event.data = doc.object();
        event.type = event.data.value(QStringLiteral("type")).toString();
        event.text = event.data.value(QStringLiteral("text")).toString();
        events.append(event);
    }

    return events;
}

} // namespace fmd
