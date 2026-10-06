#include "ModelsView.h"

#include <QGroupBox>
#include <QHBoxLayout>
#include <QHeaderView>
#include <QLabel>
#include <QPushButton>
#include <QSettings>
#include <QTableWidget>
#include <QVBoxLayout>

namespace fmd {

ModelsView::ModelsView(QWidget *parent)
    : QWidget(parent)
{
    buildUi();
    m_defaultModel = QSettings().value(QStringLiteral("infer/model")).toString();
    m_currentDefault->setText(m_defaultModel.isEmpty()
                                  ? QStringLiteral("（自动选择 *_best.pt）")
                                  : m_defaultModel);
}

void ModelsView::buildUi()
{
    auto *root = new QVBoxLayout(this);
    root->setContentsMargins(8, 8, 8, 8);

    auto *header = new QGroupBox(QStringLiteral("当前默认模型"), this);
    auto *headerLayout = new QHBoxLayout(header);
    m_currentDefault = new QLabel(header);
    m_currentDefault->setTextInteractionFlags(Qt::TextSelectableByMouse);
    QFont f = m_currentDefault->font();
    f.setBold(true);
    m_currentDefault->setFont(f);
    headerLayout->addWidget(m_currentDefault, 1);
    root->addWidget(header);

    auto *toolbar = new QHBoxLayout;
    auto *refresh = new QPushButton(QStringLiteral("重新扫描"), this);
    m_setDefaultButton = new QPushButton(QStringLiteral("设为默认"), this);
    m_setDefaultButton->setEnabled(false);
    toolbar->addWidget(refresh);
    toolbar->addWidget(m_setDefaultButton);
    toolbar->addStretch();
    m_summary = new QLabel(QStringLiteral("—"), this);
    toolbar->addWidget(m_summary);
    root->addLayout(toolbar);

    m_table = new QTableWidget(0, 3, this);
    m_table->setHorizontalHeaderLabels({ QStringLiteral("权重文件"),
                                         QStringLiteral("体积 (MB)"),
                                         QStringLiteral("修改时间") });
    m_table->horizontalHeader()->setSectionResizeMode(0, QHeaderView::Stretch);
    m_table->horizontalHeader()->setSectionResizeMode(1, QHeaderView::ResizeToContents);
    m_table->horizontalHeader()->setSectionResizeMode(2, QHeaderView::ResizeToContents);
    m_table->setSelectionBehavior(QAbstractItemView::SelectRows);
    m_table->setSelectionMode(QAbstractItemView::SingleSelection);
    m_table->setEditTriggers(QAbstractItemView::NoEditTriggers);
    m_table->setAlternatingRowColors(true);
    m_table->verticalHeader()->setVisible(false);
    root->addWidget(m_table, 1);

    auto *hint = new QLabel(
        QStringLiteral("把训练好的 .pt 放进 yoloserver/models/checkpoints/ 后点「重新扫描」即可出现。\n"
                       "留空（自动）时服务端会优先选 *_best.pt。"), this);
    hint->setStyleSheet(QStringLiteral("color: #777;"));
    root->addWidget(hint);

    connect(refresh, &QPushButton::clicked, this, &ModelsView::refreshRequested);
    connect(m_setDefaultButton, &QPushButton::clicked, this, &ModelsView::setSelectedAsDefault);
    connect(m_table, &QTableWidget::itemSelectionChanged, this, &ModelsView::onSelectionChanged);
}

void ModelsView::setModels(const QVector<ModelInfo> &models)
{
    m_table->setRowCount(0);
    for (const ModelInfo &m : models) {
        const int row = m_table->rowCount();
        m_table->insertRow(row);

        auto *nameItem = new QTableWidgetItem(m.name);
        nameItem->setData(Qt::UserRole, m.name);
        nameItem->setToolTip(m.name);
        m_table->setItem(row, 0, nameItem);

        auto *sizeItem = new QTableWidgetItem(QString::number(m.sizeMb, 'f', 2));
        sizeItem->setTextAlignment(Qt::AlignCenter);
        m_table->setItem(row, 1, sizeItem);

        auto *timeItem = new QTableWidgetItem(m.modified);
        timeItem->setTextAlignment(Qt::AlignCenter);
        m_table->setItem(row, 2, timeItem);

        // 默认模型高亮
        if (!m_defaultModel.isEmpty() && m.name == m_defaultModel) {
            QFont bold = nameItem->font();
            bold.setBold(true);
            nameItem->setFont(bold);
            nameItem->setForeground(QBrush(QColor(26, 127, 55)));
        }
    }
    m_summary->setText(QStringLiteral("共 %1 个权重").arg(models.size()));
}

int ModelsView::modelCount() const
{
    return m_table->rowCount();
}

void ModelsView::onSelectionChanged()
{
    m_setDefaultButton->setEnabled(m_table->currentRow() >= 0);
}

int ModelsView::rowOfModel(const QString &name) const
{
    for (int row = 0; row < m_table->rowCount(); ++row) {
        const QTableWidgetItem *item = m_table->item(row, 0);
        if (item && item->data(Qt::UserRole).toString() == name)
            return row;
    }
    return -1;
}

void ModelsView::setSelectedAsDefault()
{
    const int row = m_table->currentRow();
    if (row < 0)
        return;

    const QString name = m_table->item(row, 0)->data(Qt::UserRole).toString();
    m_defaultModel = name;

    QSettings settings;
    settings.setValue(QStringLiteral("infer/model"), name);
    settings.sync();

    m_currentDefault->setText(name);
    setModelsFromCurrentTable();          // 刷新加粗高亮
    emit defaultModelChanged(name);
    emit statusMessage(QStringLiteral("默认模型已切换为 %1").arg(name));
}

void ModelsView::setModelsFromCurrentTable()
{
    // 重新着色：先收集再回填，避免清表导致选中丢失
    QVector<ModelInfo> models;
    for (int row = 0; row < m_table->rowCount(); ++row) {
        ModelInfo info;
        info.name     = m_table->item(row, 0)->data(Qt::UserRole).toString();
        info.sizeMb   = m_table->item(row, 1)->text().toDouble();
        info.modified = m_table->item(row, 2)->text();
        models.append(info);
    }
    setModels(models);
}

} // namespace fmd
