#include "VideoWidget.h"

#include <QPainter>

namespace fmd {

VideoWidget::VideoWidget(QWidget *parent)
    : QWidget(parent)
{
    setMinimumSize(320, 240);
    setSizePolicy(QSizePolicy::Expanding, QSizePolicy::Expanding);
}

void VideoWidget::setFrame(const QImage &frame)
{
    m_frame = frame;
    update();
}

void VideoWidget::clearFrame()
{
    m_frame = QImage();
    update();
}

void VideoWidget::paintEvent(QPaintEvent *)
{
    QPainter painter(this);
    painter.fillRect(rect(), QColor(38, 40, 44));

    if (m_frame.isNull()) {
        painter.setPen(QColor(120, 128, 138));
        QFont font = painter.font();
        font.setPointSizeF(11.0);
        painter.setFont(font);
        painter.drawText(rect(), Qt::AlignCenter,
                         tr("尚未开始实时预览\n选择摄像头后点击「打开」"));
        return;
    }

    // 等比缩放居中（letterbox），不拉伸变形
    const QSize target = m_frame.size().scaled(size(), Qt::KeepAspectRatio);
    const QRect dst(QPoint((width() - target.width()) / 2,
                           (height() - target.height()) / 2),
                    target);

    // 实时画面用快速变换：25fps 下平滑缩放的 CPU 开销没有意义，
    // 相机画面本身带噪点，视觉上也看不出差别。
    painter.setRenderHint(QPainter::SmoothPixmapTransform, false);
    painter.drawImage(dst, m_frame);
}

} // namespace fmd
