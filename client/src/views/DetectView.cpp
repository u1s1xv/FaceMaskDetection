#include "DetectView.h"

#include "ImageCanvas.h"
#include "LlmAnalysisDialog.h"
#include "core/BackendClient.h"
#include "workers/ImageLoaderTask.h"

#include <QCheckBox>
#include <QComboBox>
#include <QDoubleSpinBox>
#include <QDragEnterEvent>
#include <QDropEvent>
#include <QFileDialog>
#include <QFileInfo>
#include <QFormLayout>
#include <QGroupBox>
#include <QHBoxLayout>
#include <QLabel>
#include <QListWidget>
#include <QMimeData>
#include <QProgressBar>
#include <QPushButton>
#include <QThreadPool>
#include <QVBoxLayout>

namespace fmd {

namespace {

// 支持的图片扩展名（小写，不带点）
const QStringList kImageSuffixes = { "jpg", "jpeg", "png", "bmp", "webp" };

bool isSupportedImage(const QString &filePath)
{
    return kImageSuffixes.contains(QFileInfo(filePath).suffix().toLower());
}

} // namespace

DetectView::DetectView(BackendClient *client, QWidget *parent)
    : QWidget(parent)
    , m_client(client)
    , m_pool(new QThreadPool(this))
{
    // 解码任务并发度：解码是 CPU 密集，超过核数没有收益
    m_pool->setMaxThreadCount(qMax(2, QThread::idealThreadCount() - 1));

    buildUi();
    setAcceptDrops(true);

    connect(m_client, &BackendClient::detectionFinished,
            this, &DetectView::onDetectionFinished);
    connect(m_client, &BackendClient::requestFailed,
            this, &DetectView::onRequestFailed);
}

void DetectView::buildUi()
{
    auto *root = new QHBoxLayout(this);
    root->setContentsMargins(8, 8, 8, 8);

    // ---------------- 左侧：画布 ----------------
    auto *canvasBox = new QGroupBox(QStringLiteral("图像"), this);
    auto *canvasLayout = new QVBoxLayout(canvasBox);

    m_canvas = new ImageCanvas(canvasBox);
    canvasLayout->addWidget(m_canvas, 1);

    m_hint = new QLabel(QStringLiteral("把图片拖到这里，或点击「打开图片」"), canvasBox);
    m_hint->setAlignment(Qt::AlignCenter);
    m_hint->setStyleSheet(QStringLiteral("color: #999; padding: 4px;"));
    canvasLayout->addWidget(m_hint);

    root->addWidget(canvasBox, 1);

    // ---------------- 右侧：参数与结果 ----------------
    auto *side = new QWidget(this);
    side->setFixedWidth(330);
    auto *sideLayout = new QVBoxLayout(side);
    sideLayout->setContentsMargins(0, 0, 0, 0);

    // 参数
    auto *paramBox = new QGroupBox(QStringLiteral("推理参数"), side);
    auto *paramForm = new QFormLayout(paramBox);

    m_modelCombo = new QComboBox(paramBox);
    m_modelCombo->setSizeAdjustPolicy(QComboBox::AdjustToMinimumContentsLengthWithIcon);
    paramForm->addRow(QStringLiteral("模型"), m_modelCombo);

    m_confSpin = new QDoubleSpinBox(paramBox);
    m_confSpin->setRange(0.01, 0.99);
    m_confSpin->setSingleStep(0.05);
    m_confSpin->setValue(0.25);
    paramForm->addRow(QStringLiteral("置信度阈值"), m_confSpin);

    m_iouSpin = new QDoubleSpinBox(paramBox);
    m_iouSpin->setRange(0.01, 0.99);
    m_iouSpin->setSingleStep(0.05);
    m_iouSpin->setValue(0.45);
    paramForm->addRow(QStringLiteral("IOU 阈值"), m_iouSpin);

    m_imgszCombo = new QComboBox(paramBox);
    m_imgszCombo->addItem(QStringLiteral("320"), 320);
    m_imgszCombo->addItem(QStringLiteral("640"), 640);
    m_imgszCombo->addItem(QStringLiteral("1280"), 1280);
    m_imgszCombo->setCurrentIndex(1);
    paramForm->addRow(QStringLiteral("推理尺寸"), m_imgszCombo);

    m_serverRenderCheck = new QCheckBox(QStringLiteral("使用服务端渲染图"), paramBox);
    m_serverRenderCheck->setToolTip(
        QStringLiteral("关闭（默认）：服务端只回结构化数据，客户端自绘检测框，载荷小、框可缩放悬停。\n"
                       "打开：服务端回已画好框的 PNG，用于对比测试。"));
    paramForm->addRow(QString(), m_serverRenderCheck);

    sideLayout->addWidget(paramBox);

    // 操作
    auto *actionRow = new QHBoxLayout;
    m_openButton = new QPushButton(QStringLiteral("打开图片"), side);
    m_detectButton = new QPushButton(QStringLiteral("开始检测"), side);
    m_detectButton->setObjectName(QStringLiteral("primaryButton"));
    m_detectButton->setEnabled(false);
    actionRow->addWidget(m_openButton);
    actionRow->addWidget(m_detectButton);
    sideLayout->addLayout(actionRow);

    m_progress = new QProgressBar(side);
    m_progress->setRange(0, 0);          // 不确定进度
    m_progress->setVisible(false);
    m_progress->setTextVisible(false);
    m_progress->setMaximumHeight(6);
    sideLayout->addWidget(m_progress);

    // 结果
    auto *resultBox = new QGroupBox(QStringLiteral("检测结果"), side);
    auto *resultLayout = new QVBoxLayout(resultBox);

    m_fileLabel = new QLabel(QStringLiteral("—"), resultBox);
    m_fileLabel->setWordWrap(true);
    m_fileLabel->setStyleSheet(QStringLiteral("color: #666;"));
    resultLayout->addWidget(m_fileLabel);

    auto *countForm = new QFormLayout;
    m_countWith    = new QLabel(QStringLiteral("0"), resultBox);
    m_countWithout = new QLabel(QStringLiteral("0"), resultBox);
    m_countWrong   = new QLabel(QStringLiteral("0"), resultBox);
    m_totalLabel   = new QLabel(QStringLiteral("0"), resultBox);
    m_timeLabel    = new QLabel(QStringLiteral("—"), resultBox);

    for (QLabel *lbl : { m_countWith, m_countWithout, m_countWrong, m_totalLabel }) {
        QFont f = lbl->font();
        f.setBold(true);
        f.setPointSize(f.pointSize() + 3);
        lbl->setFont(f);
    }
    m_countWith->setStyleSheet(QStringLiteral("color: #0a8f4d;"));
    m_countWithout->setStyleSheet(QStringLiteral("color: #c62828;"));
    m_countWrong->setStyleSheet(QStringLiteral("color: #b8860b;"));

    countForm->addRow(QStringLiteral("正确佩戴"), m_countWith);
    countForm->addRow(QStringLiteral("未佩戴"),   m_countWithout);
    countForm->addRow(QStringLiteral("佩戴不规范"), m_countWrong);
    countForm->addRow(QStringLiteral("目标总数"),  m_totalLabel);
    countForm->addRow(QStringLiteral("处理耗时"),  m_timeLabel);
    resultLayout->addLayout(countForm);

    m_llmButton = new QPushButton(QStringLiteral("AI 智能分析…"), resultBox);
    m_llmButton->setEnabled(false);
    m_llmButton->setToolTip(QStringLiteral("对当前这条检测记录调用大模型做合规性分析"));
    resultLayout->addWidget(m_llmButton);

    m_detectionList = new QListWidget(resultBox);
    m_detectionList->setAlternatingRowColors(true);
    resultLayout->addWidget(m_detectionList, 1);

    sideLayout->addWidget(resultBox, 1);
    root->addWidget(side);

    // ---------------- 连接 ----------------
    connect(m_openButton, &QPushButton::clicked, this, &DetectView::openImageDialog);
    connect(m_detectButton, &QPushButton::clicked, this, &DetectView::startDetection);
    connect(m_llmButton,    &QPushButton::clicked, this, &DetectView::openLlmAnalysis);
}

void DetectView::setModels(const QVector<ModelInfo> &models)
{
    const QString previous = m_modelCombo->currentText();
    m_modelCombo->clear();
    m_modelCombo->addItem(QStringLiteral("（自动选择 best）"), QString());
    for (const ModelInfo &m : models)
        m_modelCombo->addItem(m.name, m.name);

    const int idx = m_modelCombo->findText(previous);
    if (idx > 0)
        m_modelCombo->setCurrentIndex(idx);
}

void DetectView::setCurrentModel(const QString &modelName)
{
    const int idx = m_modelCombo->findData(modelName);
    if (idx >= 0)
        m_modelCombo->setCurrentIndex(idx);
}

void DetectView::dragEnterEvent(QDragEnterEvent *event)
{
    if (!event->mimeData()->hasUrls())
        return;
    for (const QUrl &url : event->mimeData()->urls()) {
        if (isSupportedImage(url.toLocalFile())) {
            event->acceptProposedAction();
            return;
        }
    }
}

void DetectView::dropEvent(QDropEvent *event)
{
    const QList<QUrl> urls = event->mimeData()->urls();
    if (urls.isEmpty())
        return;
    event->acceptProposedAction();
    loadImage(urls.first().toLocalFile());
}

void DetectView::openImageDialog()
{
    const QString path = QFileDialog::getOpenFileName(
        this, QStringLiteral("选择图片"), QString(),
        QStringLiteral("图片 (*.jpg *.jpeg *.png *.bmp *.webp);;所有文件 (*.*)"));
    if (!path.isEmpty())
        loadImage(path);
}

void DetectView::loadImage(const QString &filePath)
{
    if (filePath.isEmpty())
        return;
    if (m_busy) {
        emit statusMessage(QStringLiteral("正在推理中，请稍候…"));
        return;
    }

    resetResults();
    m_hint->setText(QStringLiteral("正在加载 %1 …").arg(QFileInfo(filePath).fileName()));

    auto *task = new ImageLoaderTask(filePath);
    connect(task, &ImageLoaderTask::loaded, this, &DetectView::onImageLoaded);
    connect(task, &ImageLoaderTask::failed, this, &DetectView::onImageLoadFailed);
    m_pool->start(task);       // 在后台线程解码
}

void DetectView::onImageLoaded(const QString &filePath, const QImage &image,
                               const QByteArray &rawBytes, qint64 elapsedMs)
{
    m_currentPath  = filePath;
    m_currentImage = image;
    m_currentBytes = rawBytes;

    m_canvas->setImage(image);
    m_fileLabel->setText(QStringLiteral("%1\n%2 × %3 像素，%4 KB")
                             .arg(QFileInfo(filePath).fileName())
                             .arg(image.width())
                             .arg(image.height())
                             .arg(rawBytes.size() / 1024.0, 0, 'f', 1));
    m_hint->setText(QStringLiteral("解码耗时 %1 ms — 点击「开始检测」").arg(elapsedMs));
    m_detectButton->setEnabled(true);

    emit statusMessage(QStringLiteral("已加载 %1").arg(QFileInfo(filePath).fileName()));
}

void DetectView::onImageLoadFailed(const QString &filePath, const QString &error)
{
    m_hint->setText(QStringLiteral("加载失败：%1").arg(error));
    emit statusMessage(QStringLiteral("加载 %1 失败：%2")
                           .arg(QFileInfo(filePath).fileName(), error));
}

void DetectView::startDetection()
{
    if (m_currentBytes.isEmpty()) {
        emit statusMessage(QStringLiteral("请先选择一张图片"));
        return;
    }

    const bool serverRender = m_serverRenderCheck->isChecked();

    // 服务端渲染时不需要客户端画框，交给服务端把框烧进图片
    m_canvas->setDetections({});

    setBusy(true);
    emit statusMessage(QStringLiteral("正在推理…（首次调用要加载模型，可能数秒）"));

    m_client->detect(m_currentBytes,
                     m_modelCombo->currentData().toString(),
                     m_confSpin->value(),
                     m_iouSpin->value(),
                     m_imgszCombo->currentData().toInt(),
                     serverRender,
                     QString(),                                   // tag：非批量，留空
                     QFileInfo(m_currentPath).fileName());        // 历史记录里显示的文件名
}

void DetectView::onDetectionFinished(const QString &tag, const DetectionResult &result)
{
    if (!tag.isEmpty())
        return;   // 带 tag 的响应属于批量任务，不是本页发起的

    setBusy(false);

    if (!result.success) {
        m_hint->setText(QStringLiteral("推理失败：%1").arg(result.error));
        emit statusMessage(QStringLiteral("推理失败：%1").arg(result.error));
        return;
    }

    m_lastResult = result;

    if (!result.annotatedPng.isEmpty()) {
        // 服务端渲染模式：直接用服务端画好的图
        const QImage annotated = QImage::fromData(result.annotatedPng, "PNG");
        if (!annotated.isNull()) {
            m_canvas->setImage(annotated);
            m_hint->setText(QStringLiteral("服务端渲染图（%1 KB）")
                                .arg(result.annotatedPng.size() / 1024.0, 0, 'f', 1));
        }
    } else {
        // 客户端渲染模式：原图 + 矢量检测框
        m_canvas->setDetections(result.detections);
        m_hint->setText(QStringLiteral("客户端自绘 %1 个检测框 — 滚轮缩放，悬停查看置信度")
                            .arg(result.detections.size()));
    }

    showResultSummary(result);
    emit statusMessage(QStringLiteral("检测完成：%1 个目标，耗时 %2 s")
                           .arg(result.totalDetections)
                           .arg(result.processingTime, 0, 'f', 3));
}

void DetectView::openLlmAnalysis()
{
    if (m_lastResult.recordId <= 0) {
        emit statusMessage(QStringLiteral("这条结果没有落库记录，无法做历史关联分析"));
        return;
    }
    LlmAnalysisDialog dialog(m_client, m_lastResult.recordId, this);
    dialog.exec();
}

void DetectView::showResultSummary(const DetectionResult &result)
{
    m_llmButton->setEnabled(result.recordId > 0);
    m_countWith->setText(QString::number(result.counts.value(QStringLiteral("with_mask"))));
    m_countWithout->setText(QString::number(result.counts.value(QStringLiteral("without_mask"))));
    m_countWrong->setText(QString::number(result.counts.value(QStringLiteral("mask_weared_incorrect"))));
    m_totalLabel->setText(QString::number(result.totalDetections));
    m_timeLabel->setText(QStringLiteral("%1 s").arg(result.processingTime, 0, 'f', 3));

    m_detectionList->clear();
    for (const Detection &d : result.detections) {
        m_detectionList->addItem(QStringLiteral("#%1  %2  置信度 %3")
                                     .arg(d.classId)
                                     .arg(d.className)
                                     .arg(d.confidence, 0, 'f', 3));
    }
    if (result.detections.isEmpty())
        m_detectionList->addItem(QStringLiteral("（未检测到目标）"));
}

void DetectView::resetResults()
{
    m_canvas->clearAll();
    m_detectionList->clear();
    m_countWith->setText(QStringLiteral("0"));
    m_countWithout->setText(QStringLiteral("0"));
    m_countWrong->setText(QStringLiteral("0"));
    m_totalLabel->setText(QStringLiteral("0"));
    m_timeLabel->setText(QStringLiteral("—"));
    m_fileLabel->setText(QStringLiteral("—"));
    m_currentBytes.clear();
    m_currentPath.clear();
    m_detectButton->setEnabled(false);
}

void DetectView::setBusy(bool busy)
{
    m_busy = busy;
    m_detectButton->setEnabled(!busy && !m_currentBytes.isEmpty());
    m_openButton->setEnabled(!busy);
    m_progress->setVisible(busy);
}

void DetectView::onRequestFailed(const QString &operation, const QString &error)
{
    // 只处理本页发起的请求（不带 tag），批量任务的错误由 BatchController 处理
    if (operation != QLatin1String("detect"))
        return;
    setBusy(false);
    m_hint->setText(QStringLiteral("请求失败：%1").arg(error));
    emit statusMessage(QStringLiteral("推理请求失败：%1").arg(error));
}

} // namespace fmd
