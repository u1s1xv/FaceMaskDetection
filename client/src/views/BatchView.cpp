#include "BatchView.h"

#include "core/BackendClient.h"
#include "workers/BatchController.h"

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
#include <QPushButton>
#include <QSpinBox>
#include <QTableWidget>
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
{
    buildUi();

    connect(m_controller, &BatchController::jobFinished,    this, &BatchView::onJobFinished);
    connect(m_controller, &BatchController::jobFailed,      this, &BatchView::onJobFailed);
    connect(m_controller, &BatchController::progressChanged, this, &BatchView::onProgress);
    connect(m_controller, &BatchController::batchFinished,  this, &BatchView::onBatchFinished);
    connect(m_controller, &BatchController::logMessage,     this, &BatchView::onLog);
}

void BatchView::buildUi()
{
    auto *root = new QVBoxLayout(this);
    root->setContentsMargins(8, 8, 8, 8);

    // ---------------- 参数区 ----------------
    auto *paramBox = new QGroupBox(QStringLiteral("批量参数"), this);
    auto *paramRow = new QHBoxLayout(paramBox);

    m_modelCombo = new QComboBox(paramBox);
    m_modelCombo->setMinimumWidth(230);
    paramRow->addWidget(new QLabel(QStringLiteral("模型"), paramBox));
    paramRow->addWidget(m_modelCombo);

    m_confSpin = new QDoubleSpinBox(paramBox);
    m_confSpin->setRange(0.01, 0.99);
    m_confSpin->setSingleStep(0.05);
    m_confSpin->setValue(0.25);
    paramRow->addWidget(new QLabel(QStringLiteral("置信度"), paramBox));
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
    paramRow->addWidget(new QLabel(QStringLiteral("尺寸"), paramBox));
    paramRow->addWidget(m_imgszCombo);

    m_concurrencySpin = new QSpinBox(paramBox);
    m_concurrencySpin->setRange(1, 16);
    m_concurrencySpin->setValue(4);
    m_concurrencySpin->setToolTip(QStringLiteral(
        "同时在途的请求数上限。服务端推理是串行的，调太大只会排队，\n"
        "建议 2~6；可用它做并发调优对比测试。"));
    paramRow->addWidget(new QLabel(QStringLiteral("并发"), paramBox));
    paramRow->addWidget(m_concurrencySpin);

    paramRow->addStretch();
    root->addWidget(paramBox);

    // ---------------- 操作区 ----------------
    auto *actionRow = new QHBoxLayout;
    m_addFilesButton  = new QPushButton(QStringLiteral("添加图片…"), this);
    m_addFolderButton = new QPushButton(QStringLiteral("添加文件夹…"), this);
    m_startButton     = new QPushButton(QStringLiteral("开始批量检测"), this);
    m_cancelButton    = new QPushButton(QStringLiteral("取消"), this);
    m_clearButton     = new QPushButton(QStringLiteral("清空列表"), this);
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
    m_progress->setRange(0, 100);
    m_progress->setValue(0);
    m_progress->setFormat(QStringLiteral("%v / %m"));
    root->addWidget(m_progress);

    m_summary = new QLabel(QStringLiteral("尚未添加文件"), this);
    root->addWidget(m_summary);

    // ---------------- 结果表 ----------------
    // 这里用 QTableWidget 而不是自定义 Model：批量结果是一次性生成、
    // 条目量有限，也不需要反复筛选排序。历史记录页才是 Model/View 的用武之地。
    m_table = new QTableWidget(0, ColumnCount, this);
    m_table->setHorizontalHeaderLabels({ QStringLiteral("文件"), QStringLiteral("状态"),
                                         QStringLiteral("目标数"), QStringLiteral("正确"),
                                         QStringLiteral("未佩戴"), QStringLiteral("不规范"),
                                         QStringLiteral("耗时") });
    m_table->horizontalHeader()->setSectionResizeMode(ColFile, QHeaderView::Stretch);
    m_table->setSelectionBehavior(QAbstractItemView::SelectRows);
    m_table->setEditTriggers(QAbstractItemView::NoEditTriggers);
    m_table->setAlternatingRowColors(true);
    m_table->verticalHeader()->setVisible(false);
    root->addWidget(m_table, 1);

    // ---------------- 连接 ----------------
    connect(m_addFilesButton,  &QPushButton::clicked, this, &BatchView::addFiles);
    connect(m_addFolderButton, &QPushButton::clicked, this, &BatchView::addFolder);
    connect(m_startButton,     &QPushButton::clicked, this, &BatchView::startBatch);
    connect(m_cancelButton,    &QPushButton::clicked, this, &BatchView::cancelBatch);
    connect(m_clearButton,     &QPushButton::clicked, this, &BatchView::clearList);
    connect(m_table, &QTableWidget::cellDoubleClicked, this, &BatchView::openRowInDetectPage);
}

void BatchView::setModels(const QVector<ModelInfo> &models)
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

void BatchView::addFiles()
{
    const QStringList paths = QFileDialog::getOpenFileNames(
        this, QStringLiteral("选择图片（可多选）"), QString(),
        QStringLiteral("图片 (*.jpg *.jpeg *.png *.bmp *.webp)"));
    appendRows(paths);
}

void BatchView::addFolder()
{
    const QString dir = QFileDialog::getExistingDirectory(
        this, QStringLiteral("选择包含图片的文件夹"));
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
            auto *item = new QTableWidgetItem(col == ColStatus ? QStringLiteral("待处理")
                                                               : QStringLiteral("—"));
            item->setTextAlignment(Qt::AlignCenter);
            m_table->setItem(row, col, item);
        }
    }

    m_summary->setText(QStringLiteral("已添加 %1 个文件（双击某行可在单图页查看）").arg(all.size()));
    m_progress->setRange(0, all.size());
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
        emit statusMessage(QStringLiteral("请先添加图片"));
        return;
    }

    m_controller->setMaxConcurrent(m_concurrencySpin->value());
    m_controller->setInferenceParams(m_modelCombo->currentData().toString(),
                                     m_confSpin->value(),
                                     m_iouSpin->value(),
                                     m_imgszCombo->currentData().toInt());

    for (int row = 0; row < m_table->rowCount(); ++row) {
        setRowStatus(row, QStringLiteral("排队中"), QColor(120, 120, 120));
        for (int col = ColTotal; col < ColumnCount; ++col)
            m_table->item(row, col)->setText(QStringLiteral("—"));
    }

    m_progress->setRange(0, m_controller->totalCount());
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
    m_table->setRowCount(0);
    m_progress->setRange(0, 100);
    m_progress->setValue(0);
    m_summary->setText(QStringLiteral("尚未添加文件"));
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
    const int row = rowOf(filePath);
    if (row < 0)
        return;

    setRowStatus(row, QStringLiteral("完成"), QColor(26, 127, 55));
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
    setRowStatus(row, QStringLiteral("失败"), QColor(180, 35, 24));
    if (QTableWidgetItem *item = m_table->item(row, ColFile))
        item->setToolTip(QStringLiteral("%1\n错误：%2").arg(filePath, error));
    emit jobFailedWithReason(filePath, error);
}

void BatchView::onProgress(int finished, int succeeded, int failed, int total)
{
    m_progress->setRange(0, qMax(1, total));
    m_progress->setValue(finished);
    m_summary->setText(QStringLiteral("进度 %1/%2 — 成功 %3，失败 %4")
                           .arg(finished).arg(total).arg(succeeded).arg(failed));
}

void BatchView::onBatchFinished(int succeeded, int failed, bool cancelled)
{
    updateButtons();
    m_summary->setText(QStringLiteral("%1 — 成功 %2，失败 %3")
                           .arg(cancelled ? QStringLiteral("已取消") : QStringLiteral("批量完成"))
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

} // namespace fmd
