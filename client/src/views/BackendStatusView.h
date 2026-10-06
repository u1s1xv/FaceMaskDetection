#pragma once

// 后端连接诊断面板：显示服务健康状态、可用模型、服务端日志。

#include <QWidget>

#include "core/Protocol.h"

class QFormLayout;
class QLabel;
class QListWidget;
class QPlainTextEdit;
class QPushButton;

namespace fmd {

class BackendStatusView : public QWidget
{
    Q_OBJECT
public:
    explicit BackendStatusView(QWidget *parent = nullptr);

public slots:
    void setConnecting();
    void setHealth(const fmd::HealthInfo &info);
    void setModels(const QVector<fmd::ModelInfo> &models);
    void setConnectionError(const QString &error);
    void appendLog(const QString &line);

signals:
    void refreshRequested();
    void restartRequested();

private:
    void buildUi();
    QLabel *addRow(QFormLayout *form, const QString &label);

    QLabel *m_state       = nullptr;
    QLabel *m_device      = nullptr;
    QLabel *m_torch       = nullptr;
    QLabel *m_ultralytics = nullptr;
    QLabel *m_gpu         = nullptr;
    QLabel *m_modelDir    = nullptr;
    QListWidget    *m_models = nullptr;
    QPlainTextEdit *m_log    = nullptr;
};

} // namespace fmd
