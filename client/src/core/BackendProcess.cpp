#include "BackendProcess.h"

#include <QCoreApplication>
#include <QDir>
#include <QFileInfo>
#include <QProcessEnvironment>
#include <QSettings>
#include <QTimer>
#include <QUrl>
#include <QDebug>

namespace fmd {

BackendProcess::BackendProcess(QObject *parent)
    : QObject(parent)
    , m_proc(new QProcess(this))
    , m_python(resolvePython())
    , m_script(resolveServerScript())
{
    m_proc->setProcessChannelMode(QProcess::SeparateChannels);
    m_proc->setWorkingDirectory(QFileInfo(m_script).absolutePath());

    connect(m_proc, &QProcess::readyReadStandardOutput,
            this, &BackendProcess::onReadyReadStandardOutput);
    connect(m_proc, &QProcess::readyReadStandardError,
            this, &BackendProcess::onReadyReadStandardError);
    connect(m_proc, QOverload<int, QProcess::ExitStatus>::of(&QProcess::finished),
            this, &BackendProcess::onFinished);
    connect(m_proc, &QProcess::errorOccurred,
            this, &BackendProcess::onErrorOccurred);
}

BackendProcess::~BackendProcess()
{
    stop();
}

QString BackendProcess::resolvePython()
{
    // 1) 环境变量优先级最高（便于在别的机器上跑）
    const QString fromEnv = qEnvironmentVariable("FMD_PYTHON");
    if (!fromEnv.isEmpty() && QFileInfo::exists(fromEnv))
        return fromEnv;

    // 2) 用户配置
    const QString fromSettings =
        QSettings().value(QStringLiteral("backend/python")).toString();
    if (!fromSettings.isEmpty() && QFileInfo::exists(fromSettings))
        return fromSettings;

    // 3) 常见 conda 环境探测（本项目实测可用的就是 med-yolo）
    const QStringList candidates = {
        QStringLiteral("C:/Users/25735/anaconda3/envs/med-yolo/python.exe"),
        QStringLiteral("C:/Users/25735/anaconda3/python.exe"),
    };
    for (const QString &c : candidates) {
        if (QFileInfo::exists(c))
            return c;
    }

    // 4) 兜底交给 PATH
    return QStringLiteral("python");
}

QString BackendProcess::resolveServerScript()
{
    const QString fromEnv = qEnvironmentVariable("FMD_SERVER_SCRIPT");
    if (!fromEnv.isEmpty() && QFileInfo::exists(fromEnv))
        return QFileInfo(fromEnv).absoluteFilePath();

    const QDir appDir(QCoreApplication::applicationDirPath());
    const QStringList candidates = {
        QStringLiteral("../../server/app.py"),   // 从 client/build 往上找仓库根
        QStringLiteral("../server/app.py"),
        QStringLiteral("server/app.py"),
    };
    for (const QString &rel : candidates) {
        const QString path = QDir::cleanPath(appDir.absoluteFilePath(rel));
        if (QFileInfo::exists(path))
            return path;
    }
    return QString();
}

void BackendProcess::setPythonExecutable(const QString &path)
{
    m_python = path;
}

void BackendProcess::setServerScript(const QString &path)
{
    m_script = path;
    if (!path.isEmpty())
        m_proc->setWorkingDirectory(QFileInfo(path).absolutePath());
}

QUrl BackendProcess::baseUrl() const
{
    return QUrl(QStringLiteral("http://127.0.0.1:%1").arg(m_port));
}

bool BackendProcess::isRunning() const
{
    return m_proc->state() == QProcess::Running;
}

void BackendProcess::start()
{
    if (isRunning()) {
        emit started();
        return;
    }
    if (m_script.isEmpty() || !QFileInfo::exists(m_script)) {
        emit errorOccurred(tr("找不到服务端脚本 server/app.py，请检查路径或设置 FMD_SERVER_SCRIPT"));
        return;
    }

    m_stopping = false;

    // Python 3 默认用系统本地编码写 stdout/stderr（中文机器上是 GBK），
    // 而客户端按 UTF-8 解码子进程输出，不强制的话中文日志必然乱码。
    QProcessEnvironment env = QProcessEnvironment::systemEnvironment();
    env.insert(QStringLiteral("PYTHONUTF8"), QStringLiteral("1"));
    env.insert(QStringLiteral("PYTHONIOENCODING"), QStringLiteral("utf-8"));
    m_proc->setProcessEnvironment(env);

    const QStringList args = { m_script, QStringLiteral("--port"), QString::number(m_port) };

    emit logMessage(tr("[启动] %1 %2").arg(m_python, args.join(QLatin1Char(' '))));
    m_proc->start(m_python, args);

    if (!m_proc->waitForStarted(10000)) {
        emit errorOccurred(tr("服务进程启动失败: %1").arg(m_proc->errorString()));
        return;
    }
    emit started();
}

void BackendProcess::stop()
{
    if (m_proc->state() == QProcess::NotRunning)
        return;

    m_stopping = true;
    m_proc->terminate();
    if (!m_proc->waitForFinished(5000)) {
        m_proc->kill();
        m_proc->waitForFinished(3000);
    }
}

void BackendProcess::restart()
{
    stop();
    m_restartCount = 0;
    start();
}

void BackendProcess::drainChannel(QProcess::ProcessChannel channel)
{
    m_proc->setReadChannel(channel);
    while (m_proc->canReadLine()) {
        const QString line = QString::fromUtf8(m_proc->readLine()).trimmed();
        if (!line.isEmpty())
            emit logMessage(line);
    }
}

void BackendProcess::onReadyReadStandardOutput()
{
    drainChannel(QProcess::StandardOutput);
}

void BackendProcess::onReadyReadStandardError()
{
    drainChannel(QProcess::StandardError);
}

void BackendProcess::onErrorOccurred(QProcess::ProcessError error)
{
    if (error == QProcess::FailedToStart)
        emit errorOccurred(tr("无法启动服务进程: %1").arg(m_proc->errorString()));
}

void BackendProcess::onFinished(int exitCode, QProcess::ExitStatus status)
{
    drainChannel(QProcess::StandardError);
    drainChannel(QProcess::StandardOutput);

    if (m_stopping) {
        emit stopped();
        return;
    }

    const QString reason = (status == QProcess::CrashExit)
        ? tr("进程崩溃")
        : tr("进程退出，退出码 %1").arg(exitCode);
    emit crashed(exitCode, reason);

    // 自动重启：首次立即重试，之后退避，避免疯狂重启拖垮系统
    if (m_autoRestart && m_restartCount < 5) {
        const int delay = m_restartDelayMs * (m_restartCount + 1);
        ++m_restartCount;
        emit logMessage(tr("[守护] %1，%2 ms 后自动重启（第 %3 次）")
                            .arg(reason).arg(delay).arg(m_restartCount));
        QTimer::singleShot(delay, this, [this]() {
            if (!m_stopping)
                start();
        });
    } else if (m_restartCount >= 5) {
        emit logMessage(tr("[守护] 连续重启超过 5 次，停止自动重启"));
    }
}

} // namespace fmd
