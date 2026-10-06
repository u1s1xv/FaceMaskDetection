#pragma once

// 实时画面显示控件。
//
// 为什么不用 ImageCanvas（单图页那个）：那个是为"静态图 + 交互"设计的 ——
// QGraphicsView 场景、可缩放平移、每个检测框是一个图元对象、支持悬停。
// 实时画面每秒换 25 次，重建图元是纯浪费；而且这里不需要交互。
//
// 本控件只做一件事：把最新一帧按比例缩放居中画出来。
// 缩放放在 paintEvent 里做，避免每帧都生成一张缩放后的 QImage。

#include <QImage>
#include <QWidget>

namespace fmd {

class VideoWidget : public QWidget
{
    Q_OBJECT
public:
    explicit VideoWidget(QWidget *parent = nullptr);

    void setFrame(const QImage &frame);
    void clearFrame();

    bool  hasFrame()  const { return !m_frame.isNull(); }
    QSize frameSize() const { return m_frame.size(); }

protected:
    void paintEvent(QPaintEvent *event) override;

private:
    QImage m_frame;
};

} // namespace fmd
