#pragma once

// Python 推理服务进程的生命周期管理。
// 职责：拉起、监控、异常退出自动重启、把服务端日志转发到界面。

#include <QObject>
#include <QProcess>
#include <QString>

#include "ChildProcessJob.h"

namespace fmd {

class BackendProcess : public QObject
{
    Q_OBJECT
public:
    explicit BackendProcess(QObject *parent = nullptr);
    ~BackendProcess() override;

    // 不显式设置时按候选列表自动探测
    static QString resolvePython();
    static QString resolveServerScript();

    void setPythonExecutable(const QString &path);
    void setServerScript(const QString &path);
    void setPort(quint16 port) { m_port = port; }
    quint16 port() const { return m_port; }
    void setAutoRestart(bool on) { m_autoRestart = on; }

    bool isRunning() const;
    QString pythonExecutable() const { return m_python; }
    QString serverScript() const { return m_script; }

    QUrl baseUrl() const;

public slots:
    void start();
    void stop();
    void restart();

signals:
    void logMessage(const QString &line);
    void started();
    void stopped();
    void crashed(int exitCode, const QString &reason);
    void errorOccurred(const QString &error);

private slots:
    void onReadyReadStandardOutput();
    void onReadyReadStandardError();
    void onFinished(int exitCode, QProcess::ExitStatus status);
    void onErrorOccurred(QProcess::ProcessError error);

private:
    void drainChannel(QProcess::ProcessChannel channel);

    QProcess *m_proc = nullptr;

    // 保证子进程不会在客户端异常退出后变成孤儿（见 ChildProcessJob 注释）
    ChildProcessJob m_job;
    QString   m_python;
    QString   m_script;
    quint16   m_port = 8756;
    bool      m_autoRestart = true;
    bool      m_stopping = false;
    int       m_restartCount = 0;
    int       m_restartDelayMs = 2000;
};

} // namespace fmd
