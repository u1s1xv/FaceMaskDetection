#pragma once

// 主窗口：左侧导航 + 右侧页面栈，并负责后端进程的生命周期。

#include <QMainWindow>

class QLabel;
class QListWidget;
class QStackedWidget;
class QTimer;

namespace fmd {

class BackendClient;
class BackendProcess;
class BackendStatusView;
class BatchView;
class DetectView;
class HistoryView;
class ModelsView;
class SettingsView;
struct HealthInfo;

class MainWindow : public QMainWindow
{
    Q_OBJECT
public:
    explicit MainWindow(QWidget *parent = nullptr);
    ~MainWindow() override;

    // 供自动化冒烟测试使用
    DetectView    *detectView() const { return m_detectView; }
    BatchView     *batchView() const { return m_batchView; }
    HistoryView   *historyView() const { return m_historyView; }
    ModelsView    *modelsView() const { return m_modelsView; }
    BackendClient *client() const { return m_client; }
    bool isBackendConnected() const { return m_connected; }

protected:
    void closeEvent(QCloseEvent *event) override;

private slots:
    void onBackendStarted();
    void onBackendCrashed(int exitCode, const QString &reason);
    void onBackendError(const QString &error);
    void pollHealth();
    void onHealth(const fmd::HealthInfo &info);

private:
    void buildUi();
    void applyStoredSettings();
    void setStatusText(const QString &text, bool ok = true);

    BackendProcess    *m_proc   = nullptr;
    BackendClient     *m_client = nullptr;
    BackendStatusView *m_statusView = nullptr;
    DetectView        *m_detectView = nullptr;
    BatchView         *m_batchView  = nullptr;
    HistoryView       *m_historyView = nullptr;
    ModelsView        *m_modelsView  = nullptr;
    SettingsView      *m_settingsView = nullptr;

    QListWidget    *m_nav   = nullptr;
    QStackedWidget *m_pages = nullptr;
    QLabel         *m_statusIndicator = nullptr;
    QTimer         *m_healthTimer = nullptr;
    int             m_healthAttempts = 0;
    bool            m_connected = false;
};

} // namespace fmd
