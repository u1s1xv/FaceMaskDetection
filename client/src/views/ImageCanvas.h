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
    int  detectionCount() const { return m_detectionItems.size(); }

    // 没有图片时画在画面正中的引导文案（比挂在底部角落显眼得多）
    void setEmptyHint(const QString &title, const QString &detail = QString());

protected:
    void wheelEvent(QWheelEvent *event) override;
    void drawBackground(QPainter *painter, const QRectF &rect) override;
    void drawForeground(QPainter *painter, const QRectF &rect) override;
    void resizeEvent(QResizeEvent *event) override;

private:
    void clearDetectionItems();

    QGraphicsScene      *m_scene   = nullptr;
    QGraphicsPixmapItem *m_pixmap  = nullptr;
    QVector<QGraphicsItem *> m_detectionItems;
    double m_zoom = 1.0;
    bool   m_fitOnNextResize = false;
    QString m_emptyTitle;
    QString m_emptyDetail;
};

} // namespace fmd
