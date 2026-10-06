#pragma once

// 自定义检测框图元。
// 用 QGraphicsItem 子类而不是一堆 QGraphicsRectItem：
//   * 一个图元同时负责框、标签底衬、文字，绘制次数少
//   * 悬停高亮和命中测试可以自己控制

#include <QGraphicsItem>
#include <QString>

#include "core/Protocol.h"

namespace fmd {

class DetectionItem : public QGraphicsItem
{
public:
    explicit DetectionItem(const Detection &detection, QGraphicsItem *parent = nullptr);

    QRectF boundingRect() const override;
    void   paint(QPainter *painter, const QStyleOptionGraphicsItem *option,
                 QWidget *widget = nullptr) override;

    const Detection &detection() const { return m_detection; }

    static QColor colorFor(const QString &className);

protected:
    void hoverEnterEvent(QGraphicsSceneHoverEvent *event) override;
    void hoverLeaveEvent(QGraphicsSceneHoverEvent *event) override;

private:
    Detection m_detection;
    QRectF    m_rect;      // 场景坐标系下的框
    QRectF    m_labelRect; // 标签底衬
    QString   m_label;
    bool      m_hovered = false;
    qreal     m_scale = 1.0;
};

} // namespace fmd
