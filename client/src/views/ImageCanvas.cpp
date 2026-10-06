#include "ImageCanvas.h"

#include "DetectionItem.h"

#include <QGraphicsPixmapItem>
#include <QGraphicsScene>
#include <QFont>
#include <QPainter>
#include <QResizeEvent>
#include <QWheelEvent>

namespace fmd {

namespace {
constexpr double kZoomStep   = 1.15;
constexpr double kZoomMin    = 0.05;
constexpr double kZoomMax    = 40.0;
}

ImageCanvas::ImageCanvas(QWidget *parent)
    : QGraphicsView(parent)
    , m_scene(new QGraphicsScene(this))
{
    setScene(m_scene);
    setRenderHints(QPainter::Antialiasing | QPainter::SmoothPixmapTransform);
    setDragMode(QGraphicsView::ScrollHandDrag);      // 左键拖拽平移
    setTransformationAnchor(QGraphicsView::AnchorUnderMouse);
    setResizeAnchor(QGraphicsView::AnchorViewCenter);
    setAlignment(Qt::AlignCenter);
    setFrameShape(QFrame::NoFrame);
    setMinimumSize(320, 240);
}

bool ImageCanvas::hasImage() const
{
    return m_pixmap != nullptr && !m_pixmap->pixmap().isNull();
}

void ImageCanvas::setImage(const QImage &image)
{
    clearAll();
    if (image.isNull())
        return;

    m_pixmap = m_scene->addPixmap(QPixmap::fromImage(image));
    m_pixmap->setZValue(0);
    m_scene->setSceneRect(m_pixmap->boundingRect());
    m_fitOnNextResize = true;
    fitToWindow();
}

void ImageCanvas::clearDetectionItems()
{
    for (QGraphicsItem *item : m_detectionItems)
        m_scene->removeItem(item), delete item;
    m_detectionItems.clear();
}

void ImageCanvas::setDetections(const QVector<Detection> &detections)
{
    clearDetectionItems();
    for (const Detection &d : detections) {
        auto *item = new DetectionItem(d);
        m_scene->addItem(item);
        m_detectionItems.append(item);
    }
}

void ImageCanvas::clearAll()
{
    clearDetectionItems();
    m_scene->clear();          // clear() 会连同 m_pixmap 一起销毁
    m_pixmap = nullptr;
    m_zoom = 1.0;
    resetTransform();
}

void ImageCanvas::fitToWindow()
{
    if (!hasImage())
        return;
    fitInView(m_pixmap->boundingRect(), Qt::KeepAspectRatio);
    m_zoom = transform().m11();
}

void ImageCanvas::resizeEvent(QResizeEvent *event)
{
    QGraphicsView::resizeEvent(event);
    if (m_fitOnNextResize && hasImage()) {
        m_fitOnNextResize = false;
        fitToWindow();
    }
}

void ImageCanvas::wheelEvent(QWheelEvent *event)
{
    if (!hasImage()) {
        QGraphicsView::wheelEvent(event);
        return;
    }

    const double factor = event->angleDelta().y() > 0 ? kZoomStep : (1.0 / kZoomStep);
    const double next = m_zoom * factor;
    if (next < kZoomMin || next > kZoomMax) {
        event->accept();
        return;
    }

    m_zoom = next;
    scale(factor, factor);
    event->accept();
}

void ImageCanvas::drawBackground(QPainter *painter, const QRectF &rect)
{
    // 深色背景，放图片和框对比度更好
    painter->fillRect(rect, QColor(38, 40, 44));
}

void ImageCanvas::setEmptyHint(const QString &title, const QString &detail)
{
    m_emptyTitle  = title;
    m_emptyDetail = detail;
    viewport()->update();
}

void ImageCanvas::drawForeground(QPainter *painter, const QRectF &rect)
{
    QGraphicsView::drawForeground(painter, rect);
    if (hasImage() || m_emptyTitle.isEmpty())
        return;

    // 用视口对应的场景矩形定位，保证文案始终居中且不随缩放漂移
    const QRectF viewRect = mapToScene(viewport()->rect()).boundingRect();

    QFont titleFont = painter->font();
    titleFont.setPointSizeF(13.0);
    painter->setFont(titleFont);
    painter->setPen(QColor(152, 160, 170));
    painter->drawText(viewRect.adjusted(0, -18, 0, -18), Qt::AlignCenter, m_emptyTitle);

    if (!m_emptyDetail.isEmpty()) {
        QFont detailFont = painter->font();
        detailFont.setPointSizeF(10.5);
        painter->setFont(detailFont);
        painter->setPen(QColor(108, 116, 126));
        painter->drawText(viewRect.adjusted(0, 16, 0, 16), Qt::AlignCenter, m_emptyDetail);
    }
}

} // namespace fmd
