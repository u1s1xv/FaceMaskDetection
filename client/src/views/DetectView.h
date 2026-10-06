#pragma once

// 单图检测页：拖拽/打开图片 → 后台推理 → 标注展示。

#include <QByteArray>
#include <QImage>
#include <QVector>
#include <QWidget>

#include "core/Protocol.h"

class QCheckBox;
class QComboBox;
class QDoubleSpinBox;
class QLabel;
class QListWidget;
class QProgressBar;
class QPushButton;
class QThreadPool;

namespace fmd {

class BackendClient;
class ImageCanvas;
class StatCard;

class DetectView : public QWidget
{
    Q_OBJECT
public:
    explicit DetectView(BackendClient *client, QWidget *parent = nullptr);

public slots:
    void setModels(const QVector<fmd::ModelInfo> &models);
    void openImageDialog();
    void loadImage(const QString &filePath);
    void startDetection();
    void setCurrentModel(const QString &modelName);
    void openLlmAnalysis();

signals:
    void statusMessage(const QString &message);

protected:
    void dragEnterEvent(QDragEnterEvent *event) override;
    void dropEvent(QDropEvent *event) override;

private slots:
    void onImageLoaded(const QString &filePath, const QImage &image,
                       const QByteArray &rawBytes, qint64 elapsedMs);
    void onImageLoadFailed(const QString &filePath, const QString &error);
    void onDetectionFinished(const QString &tag, const fmd::DetectionResult &result);
    void onRequestFailed(const QString &operation, const QString &error);

private:
    void buildUi();
    void setBusy(bool busy);
    void resetResults();
    void showResultSummary(const DetectionResult &result);

    BackendClient *m_client = nullptr;
    QThreadPool   *m_pool   = nullptr;

    ImageCanvas    *m_canvas     = nullptr;
    QLabel         *m_hint       = nullptr;
    QComboBox      *m_modelCombo = nullptr;
    QDoubleSpinBox *m_confSpin   = nullptr;
    QDoubleSpinBox *m_iouSpin    = nullptr;
    QComboBox      *m_imgszCombo = nullptr;
    QCheckBox      *m_serverRenderCheck = nullptr;
    QPushButton    *m_detectButton = nullptr;
    QPushButton    *m_openButton   = nullptr;
    QPushButton    *m_llmButton    = nullptr;
    QProgressBar   *m_progress     = nullptr;

    QLabel      *m_fileLabel    = nullptr;
    StatCard    *m_cardWith    = nullptr;
    StatCard    *m_cardWithout = nullptr;
    StatCard    *m_cardWrong   = nullptr;
    QLabel      *m_totalLabel   = nullptr;
    QLabel      *m_timeLabel    = nullptr;
    QListWidget *m_detectionList = nullptr;

    QString    m_currentPath;
    QByteArray m_currentBytes;
    QImage     m_currentImage;
    DetectionResult m_lastResult;
    bool       m_busy = false;
};

} // namespace fmd
