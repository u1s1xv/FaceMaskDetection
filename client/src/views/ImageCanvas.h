#pragma once

// 检测结果画布：QGraphicsView + 自定义图元。
// 支持滚轮缩放、拖拽平移、检测框悬停高亮。

#include <QGraphicsView>
#include <QVector>

#include "core/Protocol.h"

class QGraphicsPixmapItem;
class QGraphicsScene;

namespace fmd {

class ImageCanvas : public QGraphicsView
{
    Q_OBJECT
public:
    explicit ImageCanvas(QWidget *parent = nullptr);

    void setImage(const QImage &image);
    void setDetections(const QVector<Detection> &detections);
    void clearAll();
    void fitToWindow();

    bool hasImage() const;

protected:
    void wheelEvent(QWheelEvent *event) override;
    void drawBackground(QPainter *painter, const QRectF &rect) override;
    void resizeEvent(QResizeEvent *event) override;

private:
    void clearDetectionItems();

    QGraphicsScene      *m_scene   = nullptr;
    QGraphicsPixmapItem *m_pixmap  = nullptr;
    QVector<QGraphicsItem *> m_detectionItems;
    double m_zoom = 1.0;
    bool   m_fitOnNextResize = false;
};

} // namespace fmd
