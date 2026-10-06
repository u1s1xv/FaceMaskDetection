#include "DetectionItem.h"

#include <QBrush>
#include <QFont>
#include <QFontMetricsF>
#include <QPainter>
#include <QPen>

namespace fmd {

namespace {
constexpr qreal kPenWidth      = 2.0;
constexpr qreal kLabelPadding  = 4.0;
constexpr qreal kLabelFontSize = 12.0;
}

QColor DetectionItem::colorFor(const QString &className)
{
    if (className == QLatin1String("with_mask"))            return QColor(0, 200, 83);
    if (className == QLatin1String("without_mask"))         return QColor(211, 47, 47);
    if (className == QLatin1String("mask_weared_incorrect")) return QColor(245, 175, 0);
    return QColor(158, 158, 158);
}

DetectionItem::DetectionItem(const Detection &detection, QGraphicsItem *parent)
    : QGraphicsItem(parent)
    , m_detection(detection)
{
    m_rect = QRectF(QPointF(detection.x1, detection.y1),
                    QPointF(detection.x2, detection.y2)).normalized();

    m_label = QStringLiteral("%1 %2%")
                  .arg(detection.className)
                  .arg(detection.confidence * 100.0, 0, 'f', 1);

    QFont font;
    font.setPointSizeF(kLabelFontSize);
    font.setBold(true);
    const QFontMetricsF fm(font);
    const QSizeF textSize = fm.size(Qt::TextSingleLine, m_label);

    qreal labelTop = m_rect.top() - textSize.height() - 2 * kLabelPadding;
    // 框贴到图片顶部时，标签改放到框内侧，避免画到画面外
    if (labelTop < 0)
        labelTop = m_rect.top();

    m_labelRect = QRectF(m_rect.left(), labelTop,
                         textSize.width() + 2 * kLabelPadding,
                         textSize.height() + 2 * kLabelPadding);

    setAcceptHoverEvents(true);
    setZValue(10);
    setToolTip(QStringLiteral("%1\n置信度 %2\n坐标 (%3, %4) - (%5, %6)")
                   .arg(detection.className)
                   .arg(detection.confidence, 0, 'f', 4)
                   .arg(detection.x1, 0, 'f', 1).arg(detection.y1, 0, 'f', 1)
                   .arg(detection.x2, 0, 'f', 1).arg(detection.y2, 0, 'f', 1));
}

QRectF DetectionItem::boundingRect() const
{
    return m_rect.united(m_labelRect).adjusted(-kPenWidth, -kPenWidth,
                                               kPenWidth, kPenWidth);
}

void DetectionItem::paint(QPainter *painter, const QStyleOptionGraphicsItem *, QWidget *)
{
    const QColor color = colorFor(m_detection.className);

    // 悬停时框加粗，方便在小目标上定位
    const qreal penWidth = m_hovered ? kPenWidth * 1.8 : kPenWidth;
    painter->setRenderHint(QPainter::Antialiasing, true);
    painter->setPen(QPen(color, penWidth));
    painter->setBrush(Qt::NoBrush);
    painter->drawRect(m_rect);

    painter->setPen(Qt::NoPen);
    painter->setBrush(color);
    painter->drawRect(m_labelRect);

    QFont font = painter->font();
    font.setPointSizeF(kLabelFontSize);
    font.setBold(true);
    painter->setFont(font);
    painter->setPen(Qt::white);
    painter->drawText(m_labelRect, Qt::AlignCenter, m_label);
}

void DetectionItem::hoverEnterEvent(QGraphicsSceneHoverEvent *event)
{
    m_hovered = true;
    update();
    QGraphicsItem::hoverEnterEvent(event);
}

void DetectionItem::hoverLeaveEvent(QGraphicsSceneHoverEvent *event)
{
    m_hovered = false;
    update();
    QGraphicsItem::hoverLeaveEvent(event);
}

} // namespace fmd
