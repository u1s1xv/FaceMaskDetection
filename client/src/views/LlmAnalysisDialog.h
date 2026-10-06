#pragma once

// 大模型分析对话框：流式显示分析结果。

#include <QDialog>

class QComboBox;
class QLabel;
class QPlainTextEdit;
class QPushButton;

namespace fmd {

class BackendClient;

class LlmAnalysisDialog : public QDialog
{
    Q_OBJECT
public:
    explicit LlmAnalysisDialog(BackendClient *client, int recordId,
                               QWidget *parent = nullptr);

private slots:
    void startAnalysis();
    void onModelsReceived(const QStringList &models, const QString &defaultModel,
                          bool keyConfigured);
    void onAnalysisStarted(const QString &model, bool mockMode);
    void onAnalysisChunk(const QString &text);
    void onAnalysisFinished();
    void onAnalysisFailed(const QString &error);
    void saveAsText();

private:
    void buildUi();
    void setBusy(bool busy);

    BackendClient *m_client = nullptr;
    int            m_recordId = 0;

    QComboBox      *m_modelCombo = nullptr;
    QPlainTextEdit *m_promptEdit = nullptr;
    QPlainTextEdit *m_output     = nullptr;
    QPushButton    *m_startButton = nullptr;
    QPushButton    *m_saveButton  = nullptr;
    QLabel         *m_hint        = nullptr;
    bool            m_received    = false;
};

} // namespace fmd
