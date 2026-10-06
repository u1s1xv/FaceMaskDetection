#include "BackendStatusView.h"

#include <QFormLayout>
#include <QGroupBox>
#include <QHBoxLayout>
#include <QLabel>
#include <QListWidget>
#include <QPlainTextEdit>
#include <QPushButton>
#include <QVBoxLayout>

namespace fmd {

BackendStatusView::BackendStatusView(QWidget *parent)
    : QWidget(parent)
{
    buildUi();
}

QLabel *BackendStatusView::addRow(QFormLayout *form, const QString &label)
{
    auto *value = new QLabel(QStringLiteral("—"));
    value->setTextInteractionFlags(Qt::TextSelectableByMouse);
    value->setWordWrap(true);
    form->addRow(label, value);
    return value;
}

void BackendStatusView::buildUi()
{
    auto *root = new QVBoxLayout(this);

    // ---- 服务状态 ----
    auto *statusBox = new QGroupBox(tr("推理服务状态"), this);
    auto *form = new QFormLayout(statusBox);
    m_state       = addRow(form, tr("连接状态"));
    m_device      = addRow(form, tr("计算设备"));
    m_gpu         = addRow(form, QStringLiteral("GPU"));
    m_torch       = addRow(form, QStringLiteral("PyTorch"));
    m_ultralytics = addRow(form, QStringLiteral("Ultralytics"));
    m_modelDir    = addRow(form, tr("模型目录"));
    root->addWidget(statusBox);

    // ---- 模型列表 ----
    auto *modelsBox = new QGroupBox(tr("可用模型"), this);
    auto *modelsLayout = new QVBoxLayout(modelsBox);
    m_models = new QListWidget(modelsBox);
    m_models->setMaximumHeight(120);
    modelsLayout->addWidget(m_models);
    root->addWidget(modelsBox);

    // ---- 操作 ----
    auto *buttons = new QHBoxLayout;
    auto *refresh = new QPushButton(tr("刷新状态"), this);
    auto *restart = new QPushButton(tr("重启服务"), this);
    buttons->addWidget(refresh);
    buttons->addWidget(restart);
    buttons->addStretch();
    root->addLayout(buttons);

    connect(refresh, &QPushButton::clicked, this, &BackendStatusView::refreshRequested);
    connect(restart, &QPushButton::clicked, this, &BackendStatusView::restartRequested);

    // ---- 日志 ----
    auto *logBox = new QGroupBox(tr("服务端日志"), this);
    auto *logLayout = new QVBoxLayout(logBox);
    m_log = new QPlainTextEdit(logBox);
    m_log->setReadOnly(true);
    m_log->setMaximumBlockCount(500);   // 防止长时间运行内存膨胀
    m_log->setStyleSheet(QStringLiteral("font-family: Consolas, monospace; font-size: 12px;"));
    logLayout->addWidget(m_log);
    root->addWidget(logBox, 1);
}

void BackendStatusView::setConnecting()
{
    m_state->setText(tr("正在连接…"));
}

void BackendStatusView::setHealth(const HealthInfo &info)
{
    if (!info.ok) {
        setConnectionError(info.error.isEmpty() ? tr("服务未就绪") : info.error);
        return;
    }
    m_state->setText(tr("已连接"));
    m_device->setText(info.device);
    m_gpu->setText(info.gpu.isEmpty() ? QStringLiteral("—") : info.gpu);
    m_torch->setText(info.torch);
    m_ultralytics->setText(info.ultralytics);
    m_modelDir->setText(info.modelDir);
}

void BackendStatusView::setModels(const QVector<ModelInfo> &models)
{
    m_models->clear();
    for (const ModelInfo &m : models) {
        m_models->addItem(QStringLiteral("%1    %2 MB    %3")
                              .arg(m.name)
                              .arg(m.sizeMb, 0, 'f', 2)
                              .arg(m.modified));
    }
    if (models.isEmpty())
        m_models->addItem(tr("（模型目录中没有 .pt 文件）"));
}

void BackendStatusView::setConnectionError(const QString &error)
{
    m_state->setText(tr("连接失败：%1").arg(error));
}

void BackendStatusView::appendLog(const QString &line)
{
    m_log->appendPlainText(line);
}

} // namespace fmd
