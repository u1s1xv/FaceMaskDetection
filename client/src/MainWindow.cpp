#include "MainWindow.h"

#include "core/BackendClient.h"
#include "core/BackendProcess.h"
#include "core/Protocol.h"
#include "views/BackendStatusView.h"
#include "views/BatchView.h"
#include "views/DetectView.h"
#include "views/HistoryView.h"
#include "views/ModelsView.h"
#include "views/SettingsView.h"

#include <QCloseEvent>
#include <QLabel>
#include <QListWidget>
#include <QSplitter>
#include <QStackedWidget>
#include <QStatusBar>
#include <QTimer>
#include <QVBoxLayout>

namespace fmd {

namespace {
constexpr int kHealthIntervalMs = 1000;
constexpr int kHealthIdleMs     = 15000;
constexpr int kHealthMaxTries   = 90;   // 冷启动要导入 torch，给足 90 秒
}

MainWindow::MainWindow(QWidget *parent)
    : QMainWindow(parent)
    , m_proc(new BackendProcess(this))
    , m_client(new BackendClient(this))
    , m_healthTimer(new QTimer(this))
{
    // 必须早于 setBaseUrl：端口决定客户端要连的地址
    applyStoredSettings();
    buildUi();

    m_client->setBaseUrl(m_proc->baseUrl());

    connect(m_proc, &BackendProcess::started,       this, &MainWindow::onBackendStarted);
    connect(m_proc, &BackendProcess::crashed,       this, &MainWindow::onBackendCrashed);
    connect(m_proc, &BackendProcess::errorOccurred, this, &MainWindow::onBackendError);
    connect(m_proc, &BackendProcess::logMessage,    m_statusView, &BackendStatusView::appendLog);

    connect(m_client, &BackendClient::healthReceived, this, &MainWindow::onHealth);
    connect(m_client, &BackendClient::modelsReceived, m_statusView, &BackendStatusView::setModels);
    connect(m_client, &BackendClient::modelsReceived, m_detectView, &DetectView::setModels);
    connect(m_client, &BackendClient::modelsReceived, m_batchView,  &BatchView::setModels);
    connect(m_client, &BackendClient::modelsReceived, m_modelsView, &ModelsView::setModels);
    connect(m_client, &BackendClient::modelsReceived, m_settingsView, &SettingsView::setModels);

    connect(m_modelsView, &ModelsView::statusMessage, this, [this](const QString &message) {
        statusBar()->showMessage(message);
    });
    connect(m_modelsView, &ModelsView::refreshRequested, m_client, &BackendClient::fetchModels);
    connect(m_modelsView, &ModelsView::defaultModelChanged, m_detectView, &DetectView::setCurrentModel);

    // 设置保存后：重新应用到进程与客户端；要求重启则重启服务
    connect(m_settingsView, &SettingsView::saved, this, [this](bool restartRequested) {
        applyStoredSettings();
        m_client->setBaseUrl(m_proc->baseUrl());
        if (restartRequested) {
            m_connected = false;
            m_proc->restart();
            m_healthAttempts = 0;
            m_healthTimer->start(kHealthIntervalMs);
        }
    });

    // 批量页双击某行 → 跳到单图页并加载该图（跨页信号路由）
    connect(m_batchView, &BatchView::requestOpenImage, this, [this](const QString &path) {
        m_nav->setCurrentRow(0);
        m_detectView->loadImage(path);
    });
    connect(m_batchView, &BatchView::statusMessage, this, [this](const QString &message) {
        statusBar()->showMessage(message);
    });
    connect(m_historyView, &HistoryView::statusMessage, this, [this](const QString &message) {
        statusBar()->showMessage(message);
    });

    // 切到历史页时自动刷新（检测完再切过去就能看到刚产生的记录）
    connect(m_nav, &QListWidget::currentRowChanged, this, [this](int row) {
        if (row == 2 && m_historyView)
            m_historyView->refresh();
        else if (row == 3 && m_modelsView)
            m_client->fetchModels();
    });
    // QStatusBar::showMessage 有第二个 timeout 参数，参数多于信号，不能直接当槽用
    connect(m_detectView, &DetectView::statusMessage, this, [this](const QString &message) {
        statusBar()->showMessage(message);
    });
    connect(m_client, &BackendClient::requestFailed, this,
            [this](const QString &op, const QString &err) {
                if (op == QLatin1String("health"))
                    return;   // 启动期间连接失败属正常，继续轮询
                m_statusView->appendLog(QStringLiteral("[错误] %1 请求失败: %2").arg(op, err));
            });

    connect(m_statusView, &BackendStatusView::refreshRequested, this, [this]() {
        m_client->checkHealth();
        m_client->fetchModels();
    });
    connect(m_statusView, &BackendStatusView::restartRequested, this, [this]() {
        m_statusView->appendLog(QStringLiteral("[守护] 手动重启服务…"));
        m_connected = false;
        m_proc->restart();
        m_healthAttempts = 0;
        m_healthTimer->start(kHealthIntervalMs);
    });

    connect(m_healthTimer, &QTimer::timeout, this, &MainWindow::pollHealth);

    m_statusView->setConnecting();
    m_healthTimer->start(kHealthIntervalMs);
    m_proc->start();
}

MainWindow::~MainWindow() = default;

void MainWindow::applyStoredSettings()
{
    m_proc->setPort(SettingsView::configuredPort());

    const QString python = SettingsView::configuredPython();
    if (!python.isEmpty())
        m_proc->setPythonExecutable(python);

    const QString script = SettingsView::configuredScript();
    if (!script.isEmpty())
        m_proc->setServerScript(script);
}

void MainWindow::buildUi()
{
    setWindowTitle(QStringLiteral("FaceMaskDetection — 智能口罩检测系统"));
    resize(1280, 820);

    m_nav = new QListWidget(this);
    m_nav->setObjectName(QStringLiteral("navList"));   // 供 QSS 精确选中
    m_nav->addItem(QStringLiteral("检测"));
    m_nav->addItem(QStringLiteral("批量检测"));
    m_nav->addItem(QStringLiteral("历史记录"));
    m_nav->addItem(QStringLiteral("模型管理"));
    m_nav->addItem(QStringLiteral("设置"));
    m_nav->setFixedWidth(160);
    m_nav->setCurrentRow(0);

    m_pages = new QStackedWidget(this);

    // 诊断面板只创建一次，嵌在设置页里复用
    m_settingsView = new SettingsView(this);
    m_statusView   = m_settingsView->statusView();

    m_detectView  = new DetectView(m_client, this);
    m_batchView   = new BatchView(m_client, this);
    m_historyView = new HistoryView(m_client, this);
    m_modelsView  = new ModelsView(this);

    m_pages->addWidget(m_detectView);
    m_pages->addWidget(m_batchView);
    m_pages->addWidget(m_historyView);
    m_pages->addWidget(m_modelsView);
    m_pages->addWidget(m_settingsView);

    connect(m_nav, &QListWidget::currentRowChanged, m_pages, &QStackedWidget::setCurrentIndex);

    auto *splitter = new QSplitter(Qt::Horizontal, this);
    splitter->addWidget(m_nav);
    splitter->addWidget(m_pages);
    splitter->setStretchFactor(0, 0);
    splitter->setStretchFactor(1, 1);
    splitter->setCollapsible(1, false);

    setCentralWidget(splitter);

    m_statusIndicator = new QLabel(QStringLiteral("后端：未连接"), this);
    statusBar()->addPermanentWidget(m_statusIndicator);
    statusBar()->showMessage(QStringLiteral("就绪"));
}

void MainWindow::setStatusText(const QString &text, bool ok)
{
    m_statusIndicator->setText(text);
    m_statusIndicator->setStyleSheet(ok ? QStringLiteral("color: #1a7f37;")
                                         : QStringLiteral("color: #b42318;"));
}

void MainWindow::onBackendStarted()
{
    statusBar()->showMessage(QStringLiteral("推理服务已拉起（%1）").arg(m_proc->pythonExecutable()));
}

void MainWindow::onBackendCrashed(int exitCode, const QString &reason)
{
    m_connected = false;
    setStatusText(QStringLiteral("后端：%1").arg(reason), false);
    m_statusView->appendLog(QStringLiteral("[守护] %1 (exit=%2)").arg(reason).arg(exitCode));
    m_healthAttempts = 0;
    m_healthTimer->start(kHealthIntervalMs);
}

void MainWindow::onBackendError(const QString &error)
{
    setStatusText(QStringLiteral("后端：启动失败"), false);
    m_statusView->appendLog(QStringLiteral("[错误] %1").arg(error));
    statusBar()->showMessage(error);
}

void MainWindow::pollHealth()
{
    ++m_healthAttempts;
    if (!m_connected && m_healthAttempts > kHealthMaxTries) {
        m_healthTimer->stop();
        setStatusText(QStringLiteral("后端：未就绪"), false);
        m_statusView->setConnectionError(QStringLiteral("多次探测未响应，请查看日志"));
        return;
    }
    m_client->checkHealth();
}

void MainWindow::onHealth(const HealthInfo &info)
{
    if (!info.ok) {
        m_statusView->setHealth(info);
        return;
    }

    m_statusView->setHealth(info);

    if (!m_connected) {
        m_connected = true;
        setStatusText(QStringLiteral("后端：已连接 (%1)").arg(info.device));
        statusBar()->showMessage(
            QStringLiteral("推理服务就绪：%1 / PyTorch %2").arg(info.device, info.torch));
        m_client->fetchModels();
        m_healthTimer->start(kHealthIdleMs);   // 连上后降低探测频率
    }
}

void MainWindow::closeEvent(QCloseEvent *event)
{
    m_healthTimer->stop();
    if (m_proc)
        m_proc->stop();
    event->accept();
}

} // namespace fmd