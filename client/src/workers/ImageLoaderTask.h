#pragma once

// 图片加载任务：文件读取 + 解码放在线程池里，避免大图冻结界面。
//
// 设计取舍：网络 I/O 由 QNetworkAccessManager 异步负责（事件驱动，本身不阻塞），
// 而文件解码是真正的 CPU 密集操作，才需要丢进 QThreadPool。

#include <QByteArray>
#include <QImage>
#include <QObject>
#include <QRunnable>
#include <QString>

namespace fmd {

class ImageLoaderTask : public QObject, public QRunnable
{
    Q_OBJECT
public:
    // decodeImage=false 时只读取字节（批量推理不需要 QImage，解码纯属浪费 CPU）
    explicit ImageLoaderTask(const QString &filePath, bool decodeImage = true,
                             QObject *parent = nullptr);

    void run() override;

signals:
    void loaded(const QString &filePath, const QImage &image,
                const QByteArray &rawBytes, qint64 elapsedMs);
    void failed(const QString &filePath, const QString &error);

private:
    QString m_filePath;
    bool    m_decodeImage = true;
};

} // namespace fmd
