#include "LlmAnalysisDialog.h"

#include "core/BackendClient.h"

#include <QComboBox>
#include <QFileDialog>
#include <QFormLayout>
#include <QHBoxLayout>
#include <QLabel>
#include <QPlainTextEdit>
#include <QPushButton>
#include <QTextStream>
#include <QVBoxLayout>

namespace fmd {

LlmAnalysisDialog::LlmAnalysisDialog(BackendClient *client, int recordId, QWidget *parent)
    : QDialog(parent)
    , m_client(client)
    , m_recordId(recordId)
{
    buildUi();

    connect(m_client, &BackendClient::llmModelsReceived, this, &LlmAnalysisDialog::onModelsReceived);
    connect(m_client, &BackendClient::analysisStarted,   this, &LlmAnalysisDialog::onAnalysisStarted);
    connect(m_client, &BackendClient::analysisChunk,     this, &LlmAnalysisDialog::onAnalysisChunk);
    connect(m_client, &BackendClient::analysisFinished,  this, &LlmAnalysisDialog::onAnalysisFinished);
    connect(m_client, &BackendClient::analysisFailed,    this, &LlmAnalysisDialog::onAnalysisFailed);

    m_client->fetchLlmModels();
}

void LlmAnalysisDialog::buildUi()
{
    setWindowTitle(QStringLiteral("AI 智能分析 — 记录 #%1").arg(m_recordId));
    resize(760, 620);

    auto *root = new QVBoxLayout(this);

    auto *form = new QFormLayout;
    m_modelCombo = new QComboBox(this);
    m_modelCombo->setMinimumWidth(260);
    form->addRow(QStringLiteral("分析模型"), m_modelCombo);
    root->addLayout(form);

    root->addWidget(new QLabel(QStringLiteral("分析要求（可自定义提示词）"), this));
    m_promptEdit = new QPlainTextEdit(this);
    m_promptEdit->setPlainText(QStringLiteral("请分析本次口罩检测结果，评估合规性并给出改进建议。"));
    m_promptEdit->setMaximumHeight(80);
    root->addWidget(m_promptEdit);

    auto *buttons = new QHBoxLayout;
    m_startButton = new QPushButton(QStringLiteral("开始分析"), this);
    m_saveButton  = new QPushButton(QStringLiteral("另存为文本…"), this);
    m_saveButton->setEnabled(false);
    buttons->addWidget(m_startButton);
    buttons->addWidget(m_saveButton);
    buttons->addStretch();
    root->addLayout(buttons);

    m_hint = new QLabel(QStringLiteral("准备就绪"), this);
    m_hint->setStyleSheet(QStringLiteral("color: #666;"));
    root->addWidget(m_hint);

    m_output = new QPlainTextEdit(this);
    m_output->setReadOnly(true);
    m_output->setStyleSheet(QStringLiteral("font-family: \"Microsoft YaHei\", Consolas, monospace; font-size: 13px;"));
    root->addWidget(m_output, 1);

    connect(m_startButton, &QPushButton::clicked, this, &LlmAnalysisDialog::startAnalysis);
    connect(m_saveButton,  &QPushButton::clicked, this, &LlmAnalysisDialog::saveAsText);
}

void LlmAnalysisDialog::setBusy(bool busy)
{
    m_startButton->setEnabled(!busy);
    m_modelCombo->setEnabled(!busy);
    m_promptEdit->setEnabled(!busy);
}

void LlmAnalysisDialog::onModelsReceived(const QStringList &models, const QString &defaultModel,
                                        bool keyConfigured)
{
    m_modelCombo->clear();
    m_modelCombo->addItems(models);
    const int idx = m_modelCombo->findText(defaultModel);
    if (idx >= 0)
        m_modelCombo->setCurrentIndex(idx);

    if (!keyConfigured) {
        m_hint->setText(QStringLiteral(
            "未检测到 SILICONFLOW_API_KEY，将使用服务端模拟分析模式（链路完全相同，只是文本是本地生成的）"));
        m_hint->setStyleSheet(QStringLiteral("color: #b8860b;"));
    } else {
        m_hint->setText(QStringLiteral("已配置 API Key，将调用真实大模型"));
    }
    m_startButton->setEnabled(!models.isEmpty());
}

void LlmAnalysisDialog::startAnalysis()
{
    if (m_modelCombo->currentText().isEmpty())
        return;

    m_output->clear();
    m_received = false;
    setBusy(true);
    m_hint->setText(QStringLiteral("正在流式接收…"));

    m_client->analyzeStream(m_recordId,
                            m_promptEdit->toPlainText(),
                            m_modelCombo->currentText());
}

void LlmAnalysisDialog::onAnalysisStarted(const QString &model, bool mockMode)
{
    m_hint->setText(mockMode
                        ? QStringLiteral("流式接收中（模拟模式）— 模型 %1").arg(model)
                        : QStringLiteral("流式接收中 — 模型 %1").arg(model));
}

void LlmAnalysisDialog::onAnalysisChunk(const QString &text)
{
    // 逐块追加：效果是文字逐渐"打"出来，而不是等半天一次性弹出
    m_output->moveCursor(QTextCursor::End);
    m_output->insertPlainText(text);
    m_output->moveCursor(QTextCursor::End);
    m_received = true;
}

void LlmAnalysisDialog::onAnalysisFinished()
{
    setBusy(false);
    m_saveButton->setEnabled(m_received);
    m_hint->setText(QStringLiteral("分析完成"));
}

void LlmAnalysisDialog::onAnalysisFailed(const QString &error)
{
    setBusy(false);
    m_hint->setText(QStringLiteral("分析失败：%1").arg(error));
    m_hint->setStyleSheet(QStringLiteral("color: #b42318;"));
}

void LlmAnalysisDialog::saveAsText()
{
    const QString path = QFileDialog::getSaveFileName(
        this, QStringLiteral("保存分析结果"),
        QStringLiteral("analysis_record_%1.txt").arg(m_recordId),
        QStringLiteral("文本文件 (*.txt)"));
    if (path.isEmpty())
        return;

    QFile file(path);
    if (!file.open(QIODevice::WriteOnly | QIODevice::Text)) {
        m_hint->setText(QStringLiteral("保存失败：%1").arg(file.errorString()));
        return;
    }
    QTextStream stream(&file);
    stream.setCodec("UTF-8");            // Qt5 是 setCodec（Qt6 改成 setEncoding）
    stream << m_output->toPlainText();
    m_hint->setText(QStringLiteral("已保存到 %1").arg(path));
}

} // namespace fmd
