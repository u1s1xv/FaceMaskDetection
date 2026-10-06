#pragma once

// SSE（Server-Sent Events）增量解析器。
//
// 核心难点是**半帧**：TCP 是字节流，一次 readyRead 拿到的数据可能
//   * 只有半个事件（"data: {\"type\":\"cont"）
//   * 包含多个完整事件
//   * 正好在分隔符中间断开
// 所以必须自己缓冲：把不完整的尾巴留在 buffer 里，等下一个数据块再拼。
// 这个类刻意不依赖 Qt 网络模块，只吃字节、吐事件，方便单独写单元测试。

#include <QByteArray>
#include <QJsonObject>
#include <QString>
#include <QVector>

namespace fmd {

class SseParser
{
public:
    struct Event {
        QString     type;      // start / content / done / error
        QString     text;      // type==content 时的文本片段
        QJsonObject data;      // 原始 JSON
    };

    // 喂入任意长度的字节块，返回这次能完整解析出来的事件（可能 0 个或多个）
    QVector<Event> feed(const QByteArray &chunk);

    void reset();
    int  pendingBytes() const { return m_buffer.size(); }

private:
    QByteArray m_buffer;
};

} // namespace fmd
