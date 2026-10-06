#include "HistoryView.h"

#include "models/HistoryModel.h"
#include "models/HistoryProxy.h"
#include "ImageCanvas.h"
#include "widgets/PageHeader.h"
#include "core/BackendClient.h"

#include <QCheckBox>
#include <QHBoxLayout>
#include <QHeaderView>
#include <QLabel>
#include <QLineEdit>
#include <QMessageBox>
#include <QPushButton>
#include <QSplitter>
#include <QTableView>
#include <QTimer>
#include <QVBoxLayout>

namespace fmd {

HistoryView::HistoryView(BackendClient *client, QWidget *parent)
    : QWidget(parent)
    , m_client(client)
    , m_model(new HistoryModel(this))
    , m_proxy(new HistoryProxy(this))
{
    m_proxy->setSourceModel(m_model);
    buildUi();

    connect(m_client, &BackendClient::historyReceived, this, &HistoryView::onHistoryReceived);
    connect(m_client, &BackendClient::recordReceived,  this, &HistoryView::onRecordReceived);
    connect(m_client, &BackendClient::imageReceived,   this, &HistoryView::onImageReceived);
    connect(m_client, &BackendClient::recordDeleted,   this, &HistoryView::onRecordDeleted);
    connect(m_client, &BackendClient::requestFailed,   this, &HistoryView::onRequestFailed);
}

void HistoryView::buildUi()
{
    auto *outer = new QVBoxLayout(this);
    outer->setContentsMargins(12, 12, 12, 12);
    outer->setSpacing(10);

    outer->addWidget(new PageHeader(
        tr("历史记录"),
        tr("每次检测都会自动入库。支持按文件名、时间、ID 搜索，也可以只看存在违规的记录。\n选中一行可在下方查看该次检测的标注结果。")));

    auto *root = new QVBoxLayout;
    root->setSpacing(8);
    outer->addLayout(root, 1);

    // ---------------- 工具栏 ----------------
    auto *toolbar = new QHBoxLayout;

    m_refreshButton = new QPushButton(tr("刷新"), this);
    toolbar->addWidget(m_refreshButton);

    m_search = new QLineEdit(this);
    m_search->setPlaceholderText(tr("搜索文件名 / 时间 / ID…"));
    m_search->setClearButtonEnabled(true);
    m_search->setMaximumWidth(320);
    toolbar->addWidget(m_search);

    m_onlyViolations = new QCheckBox(tr("只看违规"), this);
    m_onlyViolations->setToolTip(
        tr("筛选出存在「未佩戴口罩」或「佩戴不规范」的记录"));
    toolbar->addWidget(m_onlyViolations);

    toolbar->addStretch();

    m_summary = new QLabel(QStringLiteral("—"), this);
    toolbar->addWidget(m_summary);

    m_deleteButton = new QPushButton(tr("删除选中"), this);
    m_deleteButton->setEnabled(false);
    toolbar->addWidget(m_deleteButton);

    root->addLayout(toolbar);

    // ---------------- 表格 + 详情 ----------------
    auto *splitter = new QSplitter(Qt::Vertical, this);

    m_table = new QTableView(splitter);
    m_table->setModel(m_proxy);
    m_table->setSortingEnabled(true);
    m_table->setSelectionBehavior(QAbstractItemView::SelectRows);
    m_table->setSelectionMode(QAbstractItemView::SingleSelection);
    m_table->setEditTriggers(QAbstractItemView::NoEditTriggers);
    m_table->setAlternatingRowColors(true);
    m_table->verticalHeader()->setVisible(false);
    m_table->verticalHeader()->setDefaultSectionSize(24);
    // 列宽策略：文件名吃掉剩余空间，其余按内容收窄。
    // 文件名用「中间省略」，因为这类名字是 mask_weared_incorrect_<md5>.jpg，
    // 头尾都有信息量，从右边截会把扩展名也截掉。
    m_table->setTextElideMode(Qt::ElideMiddle);
    m_table->horizontalHeader()->setStretchLastSection(false);
    for (int col = 0; col < HistoryModel::ColumnCount; ++col)
        m_table->horizontalHeader()->setSectionResizeMode(col, QHeaderView::ResizeToContents);
    m_table->horizontalHeader()->setSectionResizeMode(HistoryModel::ColFile,
                                                     QHeaderView::Stretch);
    m_table->horizontalHeader()->setMinimumSectionSize(56);
    m_table->sortByColumn(HistoryModel::ColId, Qt::DescendingOrder);
    splitter->addWidget(m_table);

    auto *detailBox = new QWidget(splitter);
    auto *detailLayout = new QVBoxLayout(detailBox);
    detailLayout->setContentsMargins(0, 0, 0, 0);

    m_detail = new QLabel(tr("选中一行查看详情"), detailBox);
    m_detail->setWordWrap(true);
    m_detail->setTextInteractionFlags(Qt::TextSelectableByMouse);
    detailLayout->addWidget(m_detail);

    m_canvas = new ImageCanvas(detailBox);
    m_canvas->setMinimumHeight(220);
    detailLayout->addWidget(m_canvas, 1);

    splitter->addWidget(detailBox);
    splitter->setStretchFactor(0, 3);
    splitter->setStretchFactor(1, 2);
    root->addWidget(splitter, 1);

    // ---------------- 连接 ----------------
    connect(m_refreshButton, &QPushButton::clicked, this, &HistoryView::refresh);
    connect(m_deleteButton,  &QPushButton::clicked, this, &HistoryView::deleteSelected);
    connect(m_search, &QLineEdit::textChanged, this, [this](const QString &text) {
        m_proxy->setKeyword(text);
        applyFilter();
    });
    connect(m_onlyViolations, &QCheckBox::toggled, this, [this](bool on) {
        m_proxy->setOnlyViolations(on);
        applyFilter();
    });
    connect(m_table->selectionModel(), &QItemSelectionModel::selectionChanged,
            this, &HistoryView::onSelectionChanged);
}

int HistoryView::visibleRowCount() const
{
    return m_proxy->rowCount();
}

int HistoryView::loadedRowCount() const
{
    return m_model->rowCount();
}

bool HistoryView::detailHasImage() const
{
    return m_canvas && m_canvas->hasImage();
}

int HistoryView::detailDetectionCount() const
{
    return m_canvas ? m_canvas->detectionCount() : 0;
}

void HistoryView::selectFirstRow()
{
    if (m_proxy->rowCount() > 0)
        m_table->selectRow(0);
}

void HistoryView::applyFilter()
{
    m_summary->setText(tr("显示 %1 / 共 %2 条")
                           .arg(m_proxy->rowCount()).arg(m_model->totalCount()));
}

void HistoryView::refresh()
{
    m_client->fetchHistory(500, 0);
}

void HistoryView::onHistoryReceived(int total, const QVector<HistoryRecord> &items)
{
    m_model->setRecords(items);
    m_model->setTotal(total);
    applyFilter();
    emit statusMessage(tr("已加载 %1 条历史记录（共 %2 条）")
                           .arg(items.size()).arg(total));
}

int HistoryView::currentRecordId() const
{
    const QModelIndex proxyIndex = m_table->currentIndex();
    if (!proxyIndex.isValid())
        return -1;
    const QModelIndex sourceIndex = m_proxy->mapToSource(proxyIndex);
    const HistoryRecord *record = m_model->recordAt(sourceIndex.row());
    return record ? record->id : -1;
}

void HistoryView::onSelectionChanged()
{
    const int id = currentRecordId();
    m_deleteButton->setEnabled(id > 0);
    m_currentDetections.clear();
    if (id <= 0) {
        m_detail->setText(tr("选中一行查看详情"));
        m_canvas->clearAll();
        return;
    }
    m_detail->setText(tr("正在加载记录 #%1 …").arg(id));
    m_client->fetchRecord(id);
}

void HistoryView::onRecordReceived(const HistoryRecord &record)
{
    m_detail->setText(
        QStringLiteral("记录 #%1 ｜ %2 ｜ %3×%4 ｜ 模型 %5\n"
                       "目标 %6（正确 %7 / 未佩戴 %8 / 不规范 %9）｜ 推理 %10 ms ｜ 排队 %11 ms\n"
                       "时间 %12")
            .arg(record.id).arg(record.fileName)
            .arg(record.imageWidth).arg(record.imageHeight)
            .arg(record.modelName)
            .arg(record.totalDetections).arg(record.withMask)
            .arg(record.withoutMask).arg(record.incorrectMask)
            .arg(record.processingTime * 1000.0, 0, 'f', 0)
            .arg(record.queueWait * 1000.0, 0, 'f', 0)
            .arg(record.createdAt));

    // 详情接口才有检测框，必须在这里存下来 —— 列表模型里的 detections 是空的
    m_currentDetections = record.detections;

    m_loadedImageId = record.id;
    m_canvas->clearAll();
    m_client->fetchImage(record.id);
}

void HistoryView::onImageReceived(int id, const QByteArray &data)
{
    if (id != m_loadedImageId)
        return;      // 用户已经切到别的记录了，丢弃过期响应

    const QImage image = QImage::fromData(data);
    if (image.isNull())
        return;

    m_canvas->setImage(image);

    // 叠加详情接口拿到的检测框（此前误用了列表模型，那里是空的）
    if (!m_currentDetections.isEmpty()) {
        m_canvas->setDetections(m_currentDetections);
        m_canvas->fitToWindow();
    }
}

void HistoryView::deleteSelected()
{
    const int id = currentRecordId();
    if (id <= 0)
        return;

    const auto answer = QMessageBox::question(
        this, tr("确认删除"),
        tr("确定要删除记录 #%1 吗？此操作不可撤销。").arg(id),
        QMessageBox::Yes | QMessageBox::No, QMessageBox::No);
    if (answer != QMessageBox::Yes)
        return;

    m_client->deleteRecord(id);
}

void HistoryView::onRecordDeleted(int id)
{
    m_model->removeRecordById(id);
    m_canvas->clearAll();
    m_detail->setText(tr("记录 #%1 已删除").arg(id));
    applyFilter();
    emit statusMessage(tr("已删除记录 #%1").arg(id));
}

void HistoryView::onRequestFailed(const QString &operation, const QString &error)
{
    if (operation == QLatin1String("history") || operation == QLatin1String("record")
        || operation == QLatin1String("deleteRecord")) {
        emit statusMessage(tr("%1 失败：%2").arg(operation, error));
    }
}

} // namespace fmd
