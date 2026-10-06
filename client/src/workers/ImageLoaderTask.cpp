#include "ImageLoaderTask.h"

#include <QElapsedTimer>
#include <QFile>
#include <QFileInfo>
#include <QImageReader>

namespace fmd {

ImageLoaderTask::ImageLoaderTask(const QString &filePath, bool decodeImage, QObject *parent)
    : QObject(parent)
    , m_filePath(filePath)
    , m_decodeImage(decodeImage)
{
    setAutoDelete(true);   // 线程池负责 delete
}

void ImageLoaderTask::run()
{
    QElapsedTimer timer;
    timer.start();

    QFile file(m_filePath);
    if (!file.open(QIODevice::ReadOnly)) {
        emit failed(m_filePath, QStringLiteral("无法打开文件：%1").arg(file.errorString()));
        return;
    }
    const QByteArray raw = file.readAll();
    file.close();

    if (raw.isEmpty()) {
        emit failed(m_filePath, QStringLiteral("文件为空"));
        return;
    }

    if (!m_decodeImage) {
        emit loaded(m_filePath, QImage(), raw, timer.elapsed());
        return;
    }

    QImageReader reader(m_filePath);
    reader.setAutoTransform(true);
    const QImage image = reader.read();
    if (image.isNull()) {
        emit failed(m_filePath,
                    QStringLiteral("图片解码失败：%1").arg(reader.errorString()));
        return;
    }

    emit loaded(m_filePath, image, raw, timer.elapsed());
}

} // namespace fmd
