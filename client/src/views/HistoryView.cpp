#include "HistoryView.h"

#include "models/HistoryModel.h"
#include "models/HistoryProxy.h"
#include "ImageCanvas.h"
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
    auto *root = new QVBoxLayout(this);
    root->setContentsMargins(8, 8, 8, 8);

    // ---------------- 工具栏 ----------------
    auto *toolbar = new QHBoxLayout;

    m_refreshButton = new QPushButton(QStringLiteral("刷新"), this);
    toolbar->addWidget(m_refreshButton);

    m_search = new QLineEdit(this);
    m_search->setPlaceholderText(QStringLiteral("搜索文件名 / 时间 / ID…"));
    m_search->setClearButtonEnabled(true);
    m_search->setMaximumWidth(320);
    toolbar->addWidget(m_search);

    m_onlyViolations = new QCheckBox(QStringLiteral("只看违规"), this);
    m_onlyViolations->setToolTip(
        QStringLiteral("筛选出存在「未佩戴口罩」或「佩戴不规范」的记录"));
    toolbar->addWidget(m_onlyViolations);

    toolbar->addStretch();

    m_summary = new QLabel(QStringLiteral("—"), this);
    toolbar->addWidget(m_summary);

    m_deleteButton = new QPushButton(QStringLiteral("删除选中"), this);
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
    m_table->horizontalHeader()->setStretchLastSection(true);
    m_table->horizontalHeader()->setSectionResizeMode(HistoryModel::ColFile,
                                                     QHeaderView::Stretch);
    m_table->sortByColumn(HistoryModel::ColId, Qt::DescendingOrder);
    splitter->addWidget(m_table);

    auto *detailBox = new QWidget(splitter);
    auto *detailLayout = new QVBoxLayout(detailBox);
    detailLayout->setContentsMargins(0, 0, 0, 0);

    m_detail = new QLabel(QStringLiteral("选中一行查看详情"), detailBox);
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

void HistoryView::applyFilter()
{
    m_summary->setText(QStringLiteral("显示 %1 / 共 %2 条")
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
    emit statusMessage(QStringLiteral("已加载 %1 条历史记录（共 %2 条）")
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
    if (id <= 0) {
        m_detail->setText(QStringLiteral("选中一行查看详情"));
        m_canvas->clearAll();
        return;
    }
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

    // 重新拉原图并在客户端画框（复用单图页的 ImageCanvas）
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

    // 用当前选中记录的检测框叠加
    const QModelIndex proxyIndex = m_table->currentIndex();
    if (!proxyIndex.isValid())
        return;
    const QModelIndex sourceIndex = m_proxy->mapToSource(proxyIndex);
    const HistoryRecord *record = m_model->recordAt(sourceIndex.row());
    if (record)
        m_canvas->setDetections(record->detections);
}

void HistoryView::deleteSelected()
{
    const int id = currentRecordId();
    if (id <= 0)
        return;

    const auto answer = QMessageBox::question(
        this, QStringLiteral("确认删除"),
        QStringLiteral("确定要删除记录 #%1 吗？此操作不可撤销。").arg(id),
        QMessageBox::Yes | QMessageBox::No, QMessageBox::No);
    if (answer != QMessageBox::Yes)
        return;

    m_client->deleteRecord(id);
}

void HistoryView::onRecordDeleted(int id)
{
    m_model->removeRecordById(id);
    m_canvas->clearAll();
    m_detail->setText(QStringLiteral("记录 #%1 已删除").arg(id));
    applyFilter();
    emit statusMessage(QStringLiteral("已删除记录 #%1").arg(id));
}

void HistoryView::onRequestFailed(const QString &operation, const QString &error)
{
    if (operation == QLatin1String("history") || operation == QLatin1String("record")
        || operation == QLatin1String("deleteRecord")) {
        emit statusMessage(QStringLiteral("%1 失败：%2").arg(operation, error));
    }
}

} // namespace fmd
