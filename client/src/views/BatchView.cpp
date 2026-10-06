#include "BatchView.h"

#include "ImageCanvas.h"
#include "widgets/PageHeader.h"
#include "core/BackendClient.h"
#include "workers/BatchController.h"
#include "workers/ImageLoaderTask.h"

#include <QComboBox>
#include <QDir>
#include <QDoubleSpinBox>
#include <QFileDialog>
#include <QFileInfo>
#include <QFormLayout>
#include <QGroupBox>
#include <QHBoxLayout>
#include <QHeaderView>
#include <QLabel>
#include <QProgressBar>
#include <QListWidget>
#include <QPushButton>
#include <QSpinBox>
#include <QSplitter>
#include <QTableWidget>
#include <QThreadPool>
#include <QVBoxLayout>

namespace fmd {

namespace {
const QStringList kImageSuffixes = { "jpg", "jpeg", "png", "bmp", "webp" };

bool isSupportedImage(const QString &filePath)
{
    return kImageSuffixes.contains(QFileInfo(filePath).suffix().toLower());
}
} // namespace

BatchView::BatchView(BackendClient *client, QWidget *parent)
    : QWidget(parent)
    , m_client(client)
    , m_controller(new BatchController(client, this))
    , m_pool(new QThreadPool(this))
{
    m_pool->setMaxThreadCount(qMax(2, QThread::idealThreadCount() - 1));
    buildUi();

    connect(m_controller, &BatchController::jobFinished,    this, &BatchView::onJobFinished);
    connect(m_controller, &BatchController::jobFailed,      this, &BatchView::onJobFailed);
    connect(m_controller, &BatchController::progressChanged, this, &BatchView::onProgress);
    connect(m_controller, &BatchController::batchFinished,  this, &BatchView::onBatchFinished);
    connect(m_controller, &BatchController::logMessage,     this, &BatchView::onLog);
}

void BatchView::buildUi()
{
    auto *outer = new QVBoxLayout(this);
    outer->setContentsMargins(12, 12, 12, 12);
    outer->setSpacing(10);

    outer->addWidget(new PageHeader(
        tr("批量检测"),
        tr("一次添加多张图片或整个文件夹，客户端按设定并发数排队调度，服务端串行推理。\n双击结果表中的任意一行可跳转到单图页查看原图。")));

    auto *root = new QVBoxLayout;
    root->setSpacing(8);
    outer->addLayout(root, 1);

    // ---------------- 参数区 ----------------
    auto *paramBox = new QGroupBox(tr("批量参数"), this);
    auto *paramRow = new QHBoxLayout(paramBox);

    m_modelCombo = new QComboBox(paramBox);
    m_modelCombo->setMinimumWidth(230);
    paramRow->addWidget(new QLabel(tr("模型"), paramBox));
    paramRow->addWidget(m_modelCombo);

    m_confSpin = new QDoubleSpinBox(paramBox);
    m_confSpin->setRange(0.01, 0.99);
    m_confSpin->setSingleStep(0.05);
    m_confSpin->setValue(0.25);
    paramRow->addWidget(new QLabel(tr("置信度"), paramBox));
    paramRow->addWidget(m_confSpin);

    m_iouSpin = new QDoubleSpinBox(paramBox);
    m_iouSpin->setRange(0.01, 0.99);
    m_iouSpin->setSingleStep(0.05);
    m_iouSpin->setValue(0.45);
    paramRow->addWidget(new QLabel(QStringLiteral("IOU"), paramBox));
    paramRow->addWidget(m_iouSpin);

    m_imgszCombo = new QComboBox(paramBox);
    m_imgszCombo->addItem(QStringLiteral("320"), 320);
    m_imgszCombo->addItem(QStringLiteral("640"), 640);
    m_imgszCombo->addItem(QStringLiteral("1280"), 1280);
    m_imgszCombo->setCurrentIndex(1);
    paramRow->addWidget(new QLabel(tr("尺寸"), paramBox));
    paramRow->addWidget(m_imgszCombo);

    m_concurrencySpin = new QSpinBox(paramBox);
    m_concurrencySpin->setRange(1, 16);
    m_concurrencySpin->setValue(4);
    m_concurrencySpin->setToolTip(QStringLiteral(
        "同时在途的请求数上限。服务端推理是串行的，调太大只会排队，\n"
        "建议 2~6；可用它做并发调优对比测试。"));
    paramRow->addWidget(new QLabel(tr("并发"), paramBox));
    paramRow->addWidget(m_concurrencySpin);

    paramRow->addStretch();
    root->addWidget(paramBox);

    // ---------------- 操作区 ----------------
    auto *actionRow = new QHBoxLayout;
    m_addFilesButton  = new QPushButton(tr("添加图片…"), this);
    m_addFolderButton = new QPushButton(tr("添加文件夹…"), this);
    m_startButton     = new QPushButton(tr("开始批量检测"), this);
    m_cancelButton    = new QPushButton(tr("取消"), this);
    m_clearButton     = new QPushButton(tr("清空列表"), this);
    m_cancelButton->setEnabled(false);
    m_startButton->setEnabled(false);

    actionRow->addWidget(m_addFilesButton);
    actionRow->addWidget(m_addFolderButton);
    actionRow->addWidget(m_clearButton);
    actionRow->addStretch();
    actionRow->addWidget(m_cancelButton);
    actionRow->addWidget(m_startButton);
    root->addLayout(actionRow);

    m_progress = new QProgressBar(this);
    // 还没有文件时不应该显示 "0 / 100" 这种无意义的总量
    m_progress->setRange(0, 1);
    m_progress->setValue(0);
    m_progress->setFormat(QStringLiteral("%v / %m"));
    m_progress->setEnabled(false);
    m_progress->setVisible(false);   // 没有任务时不占位
    root->addWidget(m_progress);

    m_summary = new QLabel(tr("尚未添加文件"), this);
    root->addWidget(m_summary);

    // ---------------- 结果表 ----------------
    // 这里用 QTableWidget 而不是自定义 Model：批量结果是一次性生成、
    // 条目量有限，也不需要反复筛选排序。历史记录页才是 Model/View 的用武之地。
    m_table = new QTableWidget(0, ColumnCount, this);
    m_table->setHorizontalHeaderLabels({ tr("文件"), tr("状态"),
                                         tr("目标数"), tr("正确"),
                                         tr("未佩戴"), tr("不规范"),
                                         tr("耗时") });
    m_table->horizontalHeader()->setSectionResizeMode(ColFile, QHeaderView::Stretch);
    m_table->setSelectionBehavior(QAbstractItemView::SelectRows);
    m_table->setEditTriggers(QAbstractItemView::NoEditTriggers);
    m_table->setAlternatingRowColors(true);
    m_table->verticalHeader()->setVisible(false);

    // ---------------- 右侧：选中行的结果预览 ----------------
    // 批量请求为了省带宽不返回标注图，所以预览是"本地原图 + 服务端检测框"客户端重绘，
    // 与单图页、历史页用的是同一套 ImageCanvas。
    auto *previewBox = new QWidget(this);
    auto *previewLayout = new QVBoxLayout(previewBox);
    previewLayout->setContentsMargins(0, 0, 0, 0);

    m_previewInfo = new QLabel(tr("选中左侧任意一行，查看该图片的检测结果"), previewBox);
    m_previewInfo->setWordWrap(true);
    m_previewInfo->setTextInteractionFlags(Qt::TextSelectableByMouse);
    previewLayout->addWidget(m_previewInfo);

    m_preview = new ImageCanvas(previewBox);
    m_preview->setMinimumWidth(320);
    previewLayout->addWidget(m_preview, 1);

    m_previewList = new QListWidget(previewBox);
    m_previewList->setMaximumHeight(150);
    m_previewList->setAlternatingRowColors(true);
    previewLayout->addWidget(m_previewList);

    m_splitter = new QSplitter(Qt::Horizontal, this);
    m_splitter->addWidget(m_table);
    m_splitter->addWidget(previewBox);
    // 表格要放 7 列，优先给它空间；预览给一个感知上够用的固定区间即可
    m_splitter->setStretchFactor(0, 1);
    m_splitter->setStretchFactor(1, 0);
    m_splitter->setCollapsible(0, false);
    previewBox->setMinimumWidth(300);
    previewBox->setMaximumWidth(430);
    root->addWidget(m_splitter, 1);

    // ---------------- 连接 ----------------
    connect(m_addFilesButton,  &QPushButton::clicked, this, &BatchView::addFiles);
    connect(m_addFolderButton, &QPushButton::clicked, this, &BatchView::addFolder);
    connect(m_startButton,     &QPushButton::clicked, this, &BatchView::startBatch);
    connect(m_cancelButton,    &QPushButton::clicked, this, &BatchView::cancelBatch);
    connect(m_clearButton,     &QPushButton::clicked, this, &BatchView::clearList);
    connect(m_table, &QTableWidget::cellDoubleClicked, this, &BatchView::openRowInDetectPage);
    connect(m_table, &QTableWidget::itemSelectionChanged, this, &BatchView::onSelectionChanged);
}

void BatchView::setModels(const QVector<ModelInfo> &models)
{
    const QString previous = m_modelCombo->currentText();
    m_modelCombo->clear();
    m_modelCombo->addItem(tr("（自动选择 best）"), QString());
    for (const ModelInfo &m : models)
        m_modelCombo->addItem(m.name, m.name);
    const int idx = m_modelCombo->findText(previous);
    if (idx > 0)
        m_modelCombo->setCurrentIndex(idx);
}

void BatchView::addFiles()
{
    const QStringList paths = QFileDialog::getOpenFileNames(
        this, tr("选择图片（可多选）"), QString(),
        tr("图片 (*.jpg *.jpeg *.png *.bmp *.webp)"));
    appendRows(paths);
}

void BatchView::addFolder()
{
    const QString dir = QFileDialog::getExistingDirectory(
        this, tr("选择包含图片的文件夹"));
    if (dir.isEmpty())
        return;

    const QFileInfoList entries = QDir(dir).entryInfoList(QDir::Files, QDir::Name);
    QStringList paths;
    for (const QFileInfo &info : entries) {
        if (isSupportedImage(info.absoluteFilePath()))
            paths.append(info.absoluteFilePath());
    }
    appendRows(paths);
}

void BatchView::appendRows(const QStringList &paths)
{
    if (paths.isEmpty())
        return;

    m_controller->addFiles(paths);

    const QStringList all = m_controller->filePaths();
    m_table->setRowCount(0);
    for (const QString &path : all) {
        const int row = m_table->rowCount();
        m_table->insertRow(row);

        auto *fileItem = new QTableWidgetItem(QFileInfo(path).fileName());
        fileItem->setData(Qt::UserRole, path);
        fileItem->setToolTip(path);
        m_table->setItem(row, ColFile, fileItem);

        for (int col = ColStatus; col < ColumnCount; ++col) {
            auto *item = new QTableWidgetItem(col == ColStatus ? tr("待处理")
                                                               : QStringLiteral("—"));
            item->setTextAlignment(Qt::AlignCenter);
            m_table->setItem(row, col, item);
        }
    }

    m_summary->setText(tr("已添加 %1 个文件（双击某行可在单图页查看）").arg(all.size()));
    m_progress->setVisible(!all.isEmpty());
    m_progress->setRange(0, qMax(1, all.size()));
    m_progress->setValue(0);
    updateButtons();
}

int BatchView::rowOf(const QString &filePath) const
{
    for (int row = 0; row < m_table->rowCount(); ++row) {
        const QTableWidgetItem *item = m_table->item(row, ColFile);
        if (item && item->data(Qt::UserRole).toString() == filePath)
            return row;
    }
    return -1;
}

void BatchView::setRowStatus(int row, const QString &text, const QColor &color)
{
    QTableWidgetItem *item = m_table->item(row, ColStatus);
    if (!item)
        return;
    item->setText(text);
    item->setForeground(color);
}

void BatchView::startBatch()
{
    if (m_controller->totalCount() == 0) {
        emit statusMessage(tr("请先添加图片"));
        return;
    }

    m_controller->setMaxConcurrent(m_concurrencySpin->value());
    m_controller->setInferenceParams(m_modelCombo->currentData().toString(),
                                     m_confSpin->value(),
                                     m_iouSpin->value(),
                                     m_imgszCombo->currentData().toInt());

    for (int row = 0; row < m_table->rowCount(); ++row) {
        setRowStatus(row, tr("排队中"), QColor(120, 120, 120));
        for (int col = ColTotal; col < ColumnCount; ++col)
            m_table->item(row, col)->setText(QStringLiteral("—"));
    }

    m_progress->setVisible(true);
    m_progress->setRange(0, qMax(1, m_controller->totalCount()));
    m_progress->setValue(0);
    m_controller->start();
    updateButtons();
}

void BatchView::enqueueFiles(const QStringList &paths)
{
    appendRows(paths);
}

void BatchView::cancelBatch()
{
    m_controller->cancel();
    updateButtons();
}

void BatchView::clearList()
{
    m_controller->clear();
    m_results.clear();
    m_previewPath.clear();
    if (m_preview) {
        m_preview->clearAll();
        m_previewList->clear();
        m_previewInfo->setText(tr("选中左侧任意一行，查看该图片的检测结果"));
    }
    m_table->setRowCount(0);
    m_progress->setRange(0, 1);
    m_progress->setValue(0);
    m_progress->setEnabled(false);
    m_progress->setVisible(false);
    m_summary->setText(tr("尚未添加文件"));
    updateButtons();
}

void BatchView::updateButtons()
{
    const bool running = m_controller->isRunning();
    m_startButton->setEnabled(!running && m_controller->totalCount() > 0);
    m_cancelButton->setEnabled(running);
    m_clearButton->setEnabled(!running);
    m_addFilesButton->setEnabled(!running);
    m_addFolderButton->setEnabled(!running);
}

void BatchView::onJobFinished(const QString &filePath, const DetectionResult &result)
{
    // 存下结果供预览使用：批量模式下服务端不返回标注图，只回结构化数据
    RowResult stored;
    stored.ok         = true;
    stored.recordId   = result.recordId;
    stored.detections = result.detections;
    m_results.insert(filePath, stored);

    const int row = rowOf(filePath);
    if (row < 0)
        return;

    setRowStatus(row, tr("完成"), QColor(26, 127, 55));
    m_table->item(row, ColTotal)->setText(QString::number(result.totalDetections));
    m_table->item(row, ColWith)->setText(
        QString::number(result.counts.value(QStringLiteral("with_mask"))));
    m_table->item(row, ColWithout)->setText(
        QString::number(result.counts.value(QStringLiteral("without_mask"))));
    m_table->item(row, ColWrong)->setText(
        QString::number(result.counts.value(QStringLiteral("mask_weared_incorrect"))));
    m_table->item(row, ColTime)->setText(
        QStringLiteral("%1 ms").arg(result.processingTime * 1000.0, 0, 'f', 0));
}

void BatchView::onJobFailed(const QString &filePath, const QString &error)
{
    const int row = rowOf(filePath);
    if (row < 0)
        return;
    setRowStatus(row, tr("失败"), QColor(180, 35, 24));
    if (QTableWidgetItem *item = m_table->item(row, ColFile))
        item->setToolTip(tr("%1\n错误：%2").arg(filePath, error));
    emit jobFailedWithReason(filePath, error);
}

void BatchView::onProgress(int finished, int succeeded, int failed, int total)
{
    m_progress->setRange(0, qMax(1, total));
    m_progress->setValue(finished);
    m_summary->setText(tr("进度 %1/%2 — 成功 %3，失败 %4")
                           .arg(finished).arg(total).arg(succeeded).arg(failed));
}

void BatchView::onBatchFinished(int succeeded, int failed, bool cancelled)
{
    updateButtons();
    m_summary->setText(tr("%1 — 成功 %2，失败 %3")
                           .arg(cancelled ? tr("已取消") : tr("批量完成"))
                           .arg(succeeded).arg(failed));
    emit statusMessage(m_summary->text());
    emit batchCompleted(succeeded, failed, cancelled);
}

void BatchView::onLog(const QString &message)
{
    emit statusMessage(message);
}

void BatchView::openRowInDetectPage(int row, int)
{
    QTableWidgetItem *item = m_table->item(row, ColFile);
    if (item)
        emit requestOpenImage(item->data(Qt::UserRole).toString());
}

void BatchView::selectRow(int row)
{
    if (row >= 0 && row < m_table->rowCount())
        m_table->selectRow(row);
}

bool BatchView::previewHasImage() const
{
    return m_preview && m_preview->hasImage();
}

int BatchView::previewDetectionCount() const
{
    return m_preview ? m_preview->detectionCount() : 0;
}

void BatchView::onSelectionChanged()
{
    showPreviewForRow(m_table->currentRow());
}

void BatchView::showPreviewForRow(int row)
{
    if (row < 0 || !m_table->item(row, ColFile)) {
        m_previewPath.clear();
        m_preview->clearAll();
        m_previewList->clear();
        m_previewInfo->setText(tr("选中左侧任意一行，查看该图片的检测结果"));
        return;
    }

    const QString filePath = m_table->item(row, ColFile)->data(Qt::UserRole).toString();
    m_previewPath = filePath;

    const auto it = m_results.constFind(filePath);
    if (it == m_results.constEnd() || !it->ok) {
        m_preview->clearAll();
        m_previewList->clear();
        m_previewInfo->setText(tr("%1\n\n该图片还没有检测结果（未处理或已失败）")
                                   .arg(QFileInfo(filePath).fileName()));
        return;
    }

    // 结果明细
    m_previewList->clear();
    for (const Detection &d : it->detections) {
        m_previewList->addItem(tr("#%1  %2  置信度 %3  框(%4,%5)-(%6,%7)")
                                   .arg(d.classId)
                                   .arg(d.className)
                                   .arg(d.confidence, 0, 'f', 3)
                                   .arg(d.x1, 0, 'f', 0).arg(d.y1, 0, 'f', 0)
                                   .arg(d.x2, 0, 'f', 0).arg(d.y2, 0, 'f', 0));
    }
    if (it->detections.isEmpty())
        m_previewList->addItem(tr("（未检测到目标）"));

    m_previewInfo->setText(tr("%1 ｜ 共 %2 个目标 ｜ 记录 #%3")
                               .arg(QFileInfo(filePath).fileName())
                               .arg(it->detections.size())
                               .arg(it->recordId));

    // 图片解码放到线程池，避免大图卡住界面；与单图页用的是同一个任务类
    auto *task = new ImageLoaderTask(filePath, /*decodeImage=*/true);
    connect(task, &ImageLoaderTask::loaded, this, &BatchView::onPreviewLoaded);
    connect(task, &ImageLoaderTask::failed, this, &BatchView::onPreviewFailed);
    m_pool->start(task);
}

void BatchView::onPreviewLoaded(const QString &filePath, const QImage &image,
                                const QByteArray &, qint64)
{
    if (filePath != m_previewPath)
        return;              // 用户已切到别的行，丢弃过期结果

    m_preview->setImage(image);

    const auto it = m_results.constFind(filePath);
    if (it != m_results.constEnd())
        m_preview->setDetections(it->detections);
}

void BatchView::onPreviewFailed(const QString &filePath, const QString &error)
{
    if (filePath != m_previewPath)
        return;
    m_preview->clearAll();
    m_previewInfo->setText(tr("无法加载预览：%1").arg(error));
}

} // namespace fmd
