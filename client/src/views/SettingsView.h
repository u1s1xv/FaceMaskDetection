#pragma once

// 设置页：连接配置 + 默认推理参数，持久化到 QSettings。
// 底部嵌入服务诊断面板（BackendStatusView），复用而不是重造。

#include <QVector>
#include <QWidget>

#include "core/Protocol.h"

class QComboBox;
class QDoubleSpinBox;
class QLineEdit;
class QSpinBox;
class QPushButton;

namespace fmd {

class BackendStatusView;

class SettingsView : public QWidget
{
    Q_OBJECT
public:
    explicit SettingsView(QWidget *parent = nullptr);

    BackendStatusView *statusView() const { return m_statusView; }

    // 启动时由 MainWindow 读取，用于拉起后端
    static quint16 configuredPort();
    static QString configuredPython();
    static QString configuredScript();

public slots:
    void setModels(const QVector<fmd::ModelInfo> &models);
    void loadFromSettings();

signals:
    void saved(bool restartRequested);

private slots:
    void save();
    void saveAndRestart();
    void browsePython();
    void browseScript();

private:
    void buildUi();

    QSpinBox       *m_port   = nullptr;
    QLineEdit      *m_python = nullptr;
    QLineEdit      *m_script = nullptr;
    QComboBox      *m_modelCombo = nullptr;
    QDoubleSpinBox *m_confSpin   = nullptr;
    QDoubleSpinBox *m_iouSpin    = nullptr;
    QComboBox      *m_imgszCombo = nullptr;
    QPushButton    *m_saveButton = nullptr;

    BackendStatusView *m_statusView = nullptr;
};

} // namespace fmd
