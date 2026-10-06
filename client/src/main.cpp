// FaceMaskDetection Qt5 客户端入口。
//
// 正常模式：   fmd_client.exe
// 自检模式：   fmd_client.exe --selftest [图片路径]
//              拉起后端 → 探测健康 → 列模型 → 跑一次推理，全部通过返回 0。
//              用于无人值守的端到端验证。

#include <QApplication>
#include <QDebug>

#include <cstdio>
#include <QDir>
#include <QElapsedTimer>
#include <QEventLoop>
#include <QFile>
#include <QLibraryInfo>
#include <QLocale>
#include <QTranslator>
#include <QDir>
#include <QFile>
#include <QFileInfo>
#include <QTimer>

#include "MainWindow.h"
#include "views/BatchView.h"
#include "views/DetectView.h"
#include "views/HistoryView.h"
#include "views/ModelsView.h"
#include <QSettings>
#include "core/BackendClient.h"
#include "core/BackendProcess.h"
#include "core/Protocol.h"

#ifdef Q_OS_WIN
#  include <windows.h>
#endif

namespace {

const QString kLanguageKey = QStringLiteral("ui/language");

/**
 * 解析当前界面语言，优先级：命令行 --lang > QSettings 用户选择 > 系统语言。
 * 源码本身写的是中文，所以中文无需翻译文件（Qt 会用源字符串兜底）。
 */
QString resolveLanguage(const QStringList &args)
{
    const int idx = args.indexOf(QStringLiteral("--lang"));
    if (idx >= 0 && idx + 1 < args.size())
        return args.at(idx + 1);

    const QString saved = QSettings().value(kLanguageKey).toString();
    if (!saved.isEmpty())
        return saved;

    const QString system = QLocale::system().name();          // 形如 zh_CN / en_US
    return system.startsWith(QLatin1String("zh")) ? QStringLiteral("zh_CN")
                                                  : QStringLiteral("en_US");
}

// 可用的界面语言（与 resources/i18n/*.ts 一一对应）
struct LanguageOption { const char *code; const char *label; };
const LanguageOption kLanguages[] = {
    { "zh_CN", "\u7b80\u4f53\u4e2d\u6587" },
    { "en_US", "English" },
};

/**
 * 安装翻译文件。.qm 由 lrelease 从 .ts 生成，构建后复制到可执行文件同级的 i18n/ 目录。
 * 注意 QTranslator 必须比 QApplication 活得久，所以挂在 app 上。
 */
bool installTranslator(QApplication &app, const QString &language)
{
    const QString dir = QCoreApplication::applicationDirPath() + QStringLiteral("/i18n");

    auto *translator = new QTranslator(&app);
    if (!translator->load(QStringLiteral("fmd_") + language, dir)) {
        delete translator;
        return false;
    }
    app.installTranslator(translator);
    return true;
}

// Qt 自带控件的内建翻译（对话框按钮等），属于 Qt 安装目录下的 qt_*.qm
void installQtTranslator(QApplication &app, const QString &language)
{
    auto *translator = new QTranslator(&app);
    const QString qtDir = QLibraryInfo::location(QLibraryInfo::TranslationsPath);
    if (translator->load(QStringLiteral("qt_") + language, qtDir))
        app.installTranslator(translator);
    else
        delete translator;
}

// Qt5 默认的消息处理器在 Windows 上用 toLocal8Bit()（系统本地编码，中文机器上是 GBK），
// 于是控制台、重定向文件、日志收集器三者拿到的编码互相不一致。
// 这里显式统一成 UTF-8：应用侧和 Python 侧都是 UTF-8，链路才干净。
void utf8MessageHandler(QtMsgType type, const QMessageLogContext &, const QString &msg)
{
    static const char *labels[] = { "DEBUG", "WARN ", "ERROR", "FATAL", "INFO " };
    const char *label = labels[qBound(0, int(type), 4)];

    QByteArray line;
    line.reserve(msg.size() * 3 + 16);
    line.append(label);
    line.append(": ");
    line.append(msg.toUtf8());
    line.append('\n');

    fwrite(line.constData(), 1, size_t(line.size()), stderr);
    fflush(stderr);

    if (type == QtFatalMsg)
        abort();
}

int runSelfTest(const QString &imagePath)
{
    using namespace fmd;

    BackendProcess proc;
    BackendClient  client;
    client.setBaseUrl(proc.baseUrl());

    QEventLoop loop;
    int  exitCode  = 1;
    bool healthOk  = false;
    bool finished  = false;

    auto finish = [&](int code) {
        if (finished)
            return;
        finished = true;
        exitCode = code;
        loop.quit();
    };

    QObject::connect(&proc, &BackendProcess::logMessage, [](const QString &line) {
        qInfo().noquote() << "  [svc]" << line;
    });
    QObject::connect(&proc, &BackendProcess::errorOccurred, [&](const QString &err) {
        qCritical().noquote() << "[FAIL] 后端进程:" << err;
        finish(1);
    });

    QObject::connect(&client, &BackendClient::healthReceived, [&](const HealthInfo &h) {
        if (!h.ok || healthOk)
            return;
        healthOk = true;
        qInfo().noquote() << "[OK] /health  设备=" << h.device
                          << "| torch=" << h.torch
                          << "| ultralytics=" << h.ultralytics
                          << "| gpu=" << h.gpu;
        client.fetchModels();
    });

    QObject::connect(&client, &BackendClient::modelsReceived, [&](const QVector<ModelInfo> &models) {
        qInfo().noquote() << "[OK] /models  可用模型" << models.size() << "个";
        for (const ModelInfo &m : models)
            qInfo().noquote() << "        -" << m.name << QString::number(m.sizeMb, 'f', 2) + " MB";

        if (imagePath.isEmpty() || !QFileInfo::exists(imagePath)) {
            qInfo().noquote() << "[SKIP] 未提供有效图片，跳过 /detect";
            finish(0);
            return;
        }

        QFile file(imagePath);
        if (!file.open(QIODevice::ReadOnly)) {
            qCritical().noquote() << "[FAIL] 无法读取图片:" << imagePath;
            finish(1);
            return;
        }
        const QByteArray bytes = file.readAll();
        qInfo().noquote() << "[..] /detect  上传" << bytes.size() << "字节:" << QFileInfo(imagePath).fileName();
        client.detect(bytes, QString(), 0.25, 0.45, 640, true);
    });

    QObject::connect(&client, &BackendClient::detectionFinished, [&](const QString &, const DetectionResult &r) {
        if (!r.success) {
            qCritical().noquote() << "[FAIL] /detect 返回失败:" << r.error;
            finish(1);
            return;
        }
        qInfo().noquote() << "[OK] /detect  目标数=" << r.totalDetections
                          << "| 耗时=" << QString::number(r.processingTime, 'f', 3) + "s"
                          << "| 图像=" << QString("%1x%2").arg(r.imageWidth).arg(r.imageHeight)
                          << "| 标注图=" << r.annotatedPng.size() << "字节";
        for (const Detection &d : r.detections) {
            qInfo().noquote() << "        -" << d.className
                              << QString("conf=%1").arg(d.confidence, 0, 'f', 3)
                              << QString("xyxy=[%1,%2,%3,%4]")
                                     .arg(d.x1, 0, 'f', 1).arg(d.y1, 0, 'f', 1)
                                     .arg(d.x2, 0, 'f', 1).arg(d.y2, 0, 'f', 1);
        }
        finish(0);
    });

    QObject::connect(&client, &BackendClient::requestFailed, [&](const QString &op, const QString &err) {
        if (op == QLatin1String("health"))
            return;   // 启动期连接失败属正常，继续轮询
        qCritical().noquote() << "[FAIL]" << op << "请求失败:" << err;
        finish(1);
    });

    // 每秒探测一次 /health，直到服务就绪
    QTimer poll;
    poll.setInterval(1000);
    QObject::connect(&poll, &QTimer::timeout, [&]() { client.checkHealth(); });
    poll.start();

    QTimer watchdog;
    watchdog.setSingleShot(true);
    QObject::connect(&watchdog, &QTimer::timeout, [&]() {
        qCritical().noquote() << "[FAIL] 自检超时（180 秒）";
        finish(1);
    });
    watchdog.start(180000);

    qInfo().noquote() << "=== 自检开始 ===";
    qInfo().noquote() << "python :" << proc.pythonExecutable();
    qInfo().noquote() << "server :" << proc.serverScript();
    qInfo().noquote() << "url    :" << proc.baseUrl().toString();

    QTimer::singleShot(0, &proc, &BackendProcess::start);
    loop.exec();
    proc.stop();

    qInfo().noquote() << (exitCode == 0 ? "=== 自检通过 ===" : "=== 自检失败 ===");
    return exitCode;
}

// UI 冒烟测试：构造真实主窗口，等后端连上后加载图片并触发检测，
// 验证「主窗口 → 线程池解码 → HTTP 推理 → 结果回填」整条链路。
int runUiSmokeTest(const QString &imagePath)
{
    fmd::MainWindow window;
    window.show();

    QEventLoop loop;
    int  exitCode = 1;
    bool finished = false;

    auto finish = [&](int code) {
        if (finished)
            return;
        finished = true;
        exitCode = code;
        loop.quit();
    };

    QObject::connect(window.client(), &fmd::BackendClient::detectionFinished,
                     [&](const QString &, const fmd::DetectionResult &r) {
        if (!r.success) {
            qCritical().noquote() << "[FAIL] 检测返回失败:" << r.error;
            finish(1);
            return;
        }
        qInfo().noquote() << "[OK] UI 链路打通  目标数=" << r.totalDetections
                          << "| 耗时=" << QString::number(r.processingTime, 'f', 3) + "s"
                          << "| 类别统计=" << r.counts;
        for (const fmd::Detection &d : r.detections)
            qInfo().noquote() << "        -" << d.className
                              << QString("conf=%1").arg(d.confidence, 0, 'f', 3);
        finish(0);
    });

    // 等后端连上，再喂图片
    auto *connectPoll = new QTimer(&window);
    connectPoll->setInterval(500);
    int ticks = 0;
    QObject::connect(connectPoll, &QTimer::timeout, [&]() {
        if (++ticks > 240) {
            qCritical().noquote() << "[FAIL] 等待后端连接超时";
            finish(1);
            return;
        }
        if (!window.isBackendConnected())
            return;

        connectPoll->stop();
        qInfo().noquote() << "[OK] 后端已连接，加载图片";
        window.detectView()->loadImage(imagePath);

        // 给线程池解码留一点时间，再触发检测
        QTimer::singleShot(2000, window.detectView(), &fmd::DetectView::startDetection);
    });
    connectPoll->start();

    QTimer watchdog;
    watchdog.setSingleShot(true);
    QObject::connect(&watchdog, &QTimer::timeout, [&]() {
        qCritical().noquote() << "[FAIL] UI 冒烟测试超时";
        finish(1);
    });
    watchdog.start(180000);

    qInfo().noquote() << "=== UI 冒烟测试开始（offscreen）===";
    loop.exec();
    qInfo().noquote() << (exitCode == 0 ? "=== UI 冒烟测试通过 ===" : "=== UI 冒烟测试失败 ===");
    return exitCode;
}

// 批量冒烟测试：从目录取若干图片，经 BatchController 调度跑完整批。
int runBatchSmokeTest(const QString &imageDir, int limit)
{
    const QDir dir(imageDir);
    if (!dir.exists()) {
        qCritical().noquote() << "[FAIL] 目录不存在:" << imageDir;
        return 1;
    }

    QStringList files;
    const QFileInfoList entries = dir.entryInfoList({ "*.jpg", "*.jpeg", "*.png", "*.bmp" },
                                                    QDir::Files, QDir::Name);
    for (const QFileInfo &info : entries) {
        files.append(info.absoluteFilePath());
        if (files.size() >= limit)
            break;
    }
    if (files.isEmpty()) {
        qCritical().noquote() << "[FAIL] 目录里没有可用图片:" << imageDir;
        return 1;
    }

    fmd::MainWindow window;
    window.show();

    QEventLoop loop;
    int  exitCode = 1;
    bool finished = false;

    auto finish = [&](int code) {
        if (finished)
            return;
        finished = true;
        exitCode = code;
        loop.quit();
    };

    QObject::connect(window.batchView(), &fmd::BatchView::jobFailedWithReason,
                     [](const QString &path, const QString &error) {
        qCritical().noquote() << "[FAIL] 文件" << QFileInfo(path).fileName() << ":" << error;
    });

    QObject::connect(window.batchView(), &fmd::BatchView::batchCompleted,
                     [&](int succeeded, int failed, bool cancelled) {
        qInfo().noquote() << "[OK] 批量结束  成功=" << succeeded
                          << "失败=" << failed << "取消=" << cancelled;
        finish(failed == 0 && succeeded == files.size() ? 0 : 1);
    });

    auto *connectPoll = new QTimer(&window);
    connectPoll->setInterval(500);
    int ticks = 0;
    QObject::connect(connectPoll, &QTimer::timeout, [&]() {
        if (++ticks > 240) {
            qCritical().noquote() << "[FAIL] 等待后端连接超时";
            finish(1);
            return;
        }
        if (!window.isBackendConnected())
            return;

        connectPoll->stop();
        qInfo().noquote() << "[OK] 后端已连接，入队" << files.size() << "个文件";
        window.batchView()->enqueueFiles(files);
        window.batchView()->startBatch();
    });
    connectPoll->start();

    QTimer watchdog;
    watchdog.setSingleShot(true);
    QObject::connect(&watchdog, &QTimer::timeout, [&]() {
        qCritical().noquote() << "[FAIL] 批量冒烟测试超时";
        finish(1);
    });
    watchdog.start(300000);

    qInfo().noquote() << "=== 批量冒烟测试开始（offscreen）===";
    loop.exec();
    qInfo().noquote() << (exitCode == 0 ? "=== 批量冒烟测试通过 ===" : "=== 批量冒烟测试失败 ===");
    return exitCode;
}

// 历史记录冒烟测试：走通「列表 → 详情 → 原图」三级数据链路，并验证视图行数。
int runHistorySmokeTest()
{
    fmd::MainWindow window;
    window.show();

    QEventLoop loop;
    int  exitCode = 1;
    bool finished = false;

    auto finish = [&](int code) {
        if (finished)
            return;
        finished = true;
        exitCode = code;
        loop.quit();
    };

    int firstId = -1;
    bool gotList = false;

    QObject::connect(window.client(), &fmd::BackendClient::historyReceived,
                     [&](int total, const QVector<fmd::HistoryRecord> &items) {
        if (gotList)
            return;
        gotList = true;
        qInfo().noquote() << "[OK] /history  总数=" << total << "本页=" << items.size();
        for (const fmd::HistoryRecord &r : items) {
            qInfo().noquote() << QString("        #%1 %2 目标=%3 正确=%4 未戴=%5 不规范=%6 推理=%7ms")
                                     .arg(r.id).arg(r.fileName).arg(r.totalDetections)
                                     .arg(r.withMask).arg(r.withoutMask).arg(r.incorrectMask)
                                     .arg(r.processingTime * 1000.0, 0, 'f', 0);
            if (firstId < 0)
                firstId = r.id;
        }
        if (firstId < 0) {
            qCritical().noquote() << "[FAIL] 历史为空，请先跑一次检测";
            finish(1);
            return;
        }
        qInfo().noquote() << "[..] 拉取详情 #" << firstId;
        window.client()->fetchRecord(firstId);
    });

    QObject::connect(window.client(), &fmd::BackendClient::recordReceived,
                     [&](const fmd::HistoryRecord &r) {
        qInfo().noquote() << "[OK] /history/" << r.id << " 详情检测框数=" << r.detections.size()
                          << "排队=" << QString::number(r.queueWait * 1000.0, 'f', 0) + "ms";
        qInfo().noquote() << "[..] 拉取原图 #" << r.id;
        window.client()->fetchImage(r.id);
    });

    QObject::connect(window.client(), &fmd::BackendClient::imageReceived,
                     [&](int id, const QByteArray &data) {
        const QImage image = QImage::fromData(data);
        qInfo().noquote() << "[OK] /image/" << id << "字节=" << data.size()
                          << "解码=" << (image.isNull() ? "失败" : "成功")
                          << QString("%1x%2").arg(image.width()).arg(image.height());
        if (image.isNull()) {
            finish(1);
            return;
        }
        // 验证视图侧：切到历史页会触发刷新
        window.historyView()->refresh();
        QTimer::singleShot(1500, [&]() {
            const int visible = window.historyView()->visibleRowCount();
            qInfo().noquote() << "[OK] HistoryView 可见行数=" << visible;
            finish(visible > 0 ? 0 : 1);
        });
    });

    QObject::connect(window.client(), &fmd::BackendClient::requestFailed,
                     [&](const QString &op, const QString &err) {
        qCritical().noquote() << "[FAIL]" << op << err;
        finish(1);
    });

    auto *poll = new QTimer(&window);
    poll->setInterval(500);
    int ticks = 0;
    QObject::connect(poll, &QTimer::timeout, [&]() {
        if (++ticks > 240) {
            qCritical().noquote() << "[FAIL] 等待后端超时";
            finish(1);
            return;
        }
        if (!window.isBackendConnected())
            return;
        poll->stop();
        qInfo().noquote() << "[OK] 后端已连接，开始验证历史链路";
        window.client()->fetchHistory(50, 0);
    });
    poll->start();

    QTimer watchdog;
    watchdog.setSingleShot(true);
    QObject::connect(&watchdog, &QTimer::timeout, [&]() {
        qCritical().noquote() << "[FAIL] 历史冒烟测试超时";
        finish(1);
    });
    watchdog.start(180000);

    qInfo().noquote() << "=== 历史冒烟测试开始 ===";
    loop.exec();
    qInfo().noquote() << (exitCode == 0 ? "=== 历史冒烟测试通过 ===" : "=== 历史冒烟测试失败 ===");
    return exitCode;
}

// 设置项冒烟测试：把端口写进 QSettings，验证 配置 → 进程 → 客户端 全链路生效。
int runSettingsSmokeTest(int port)
{
    QSettings settings;
    const QVariant previous = settings.value(QStringLiteral("backend/port"));
    settings.setValue(QStringLiteral("backend/port"), port);
    settings.sync();
    qInfo().noquote() << "[..] 已写入 QSettings backend/port =" << port;

    fmd::MainWindow window;
    window.show();

    QEventLoop loop;
    int  exitCode = 1;
    bool finished = false;

    auto finish = [&](int code) {
        if (finished)
            return;
        finished = true;
        exitCode = code;
        loop.quit();
    };

    QObject::connect(window.client(), &fmd::BackendClient::healthReceived,
                     [&](const fmd::HealthInfo &info) {
        if (!info.ok)
            return;
        qInfo().noquote() << "[OK] 通过配置端口连上后端  设备=" << info.device;
        QTimer::singleShot(1200, [&]() {
            const int models = window.modelsView()->modelCount();
            qInfo().noquote() << "[OK] ModelsView 行数=" << models
                              << "| 客户端 baseUrl=" << window.client()->baseUrl().toString();
            finish(models > 0 ? 0 : 1);
        });
    });

    QObject::connect(window.client(), &fmd::BackendClient::requestFailed,
                     [](const QString &op, const QString &err) {
        if (op != QLatin1String("health"))
            qCritical().noquote() << "[FAIL]" << op << err;
    });

    QTimer watchdog;
    watchdog.setSingleShot(true);
    QObject::connect(&watchdog, &QTimer::timeout, [&]() {
        qCritical().noquote() << "[FAIL] 设置冒烟测试超时（后端未在配置端口上就绪）";
        finish(1);
    });
    watchdog.start(120000);

    qInfo().noquote() << "=== 设置项冒烟测试开始 ===";
    loop.exec();

    // 还原配置，避免污染后续运行
    if (previous.isValid())
        settings.setValue(QStringLiteral("backend/port"), previous);
    else
        settings.remove(QStringLiteral("backend/port"));
    settings.sync();

    qInfo().noquote() << (exitCode == 0 ? "=== 设置项冒烟测试通过 ===" : "=== 设置项冒烟测试失败 ===");
    return exitCode;
}

// 流式分析冒烟测试：验证 SSE 增量解析（含半帧拼接）。
int runLlmSmokeTest()
{
    fmd::MainWindow window;
    window.show();

    QEventLoop loop;
    int  exitCode = 1;
    bool finished = false;

    auto finish = [&](int code) {
        if (finished)
            return;
        finished = true;
        exitCode = code;
        loop.quit();
    };

    int  chunkCount = 0;
    int  charCount  = 0;
    bool started    = false;
    bool mockMode   = false;

    QObject::connect(window.client(), &fmd::BackendClient::analysisStarted,
                     [&](const QString &model, bool mock) {
        started  = true;
        mockMode = mock;
        qInfo().noquote() << "[OK] SSE start 帧  模型=" << model << "模拟模式=" << mock;
    });

    QObject::connect(window.client(), &fmd::BackendClient::analysisChunk,
                     [&](const QString &text) {
        ++chunkCount;
        charCount += text.size();
    });

    QObject::connect(window.client(), &fmd::BackendClient::analysisFinished, [&]() {
        qInfo().noquote() << "[OK] SSE done 帧  收到内容块=" << chunkCount
                          << "总字符=" << charCount;
        // 流式解析成功的判据：确实分多块到达（说明不是一次性读完），且内容非空
        const bool ok = started && chunkCount > 3 && charCount > 50;
        if (!ok)
            qCritical().noquote() << "[FAIL] 流式解析异常：分块数或字符数不足";
        finish(ok ? 0 : 1);
    });

    QObject::connect(window.client(), &fmd::BackendClient::analysisFailed,
                     [&](const QString &error) {
        qCritical().noquote() << "[FAIL] 分析失败:" << error;
        finish(1);
    });

    QObject::connect(window.client(), &fmd::BackendClient::historyReceived,
                     [&](int, const QVector<fmd::HistoryRecord> &items) {
        if (items.isEmpty()) {
            qCritical().noquote() << "[FAIL] 历史为空，无法做分析（请先跑一次检测）";
            finish(1);
            return;
        }
        const int id = items.first().id;
        qInfo().noquote() << "[..] 对记录 #" << id << "发起流式分析";
        window.client()->fetchLlmModels();
        window.client()->analyzeStream(id, QStringLiteral("请评估合规性并给出改进建议"),
                                       QStringLiteral("Qwen/QwQ-32B"));
    });

    auto *poll = new QTimer(&window);
    poll->setInterval(500);
    int ticks = 0;
    QObject::connect(poll, &QTimer::timeout, [&]() {
        if (++ticks > 240) {
            qCritical().noquote() << "[FAIL] 等待后端超时";
            finish(1);
            return;
        }
        if (!window.isBackendConnected())
            return;
        poll->stop();
        qInfo().noquote() << "[OK] 后端已连接，开始验证流式分析";
        window.client()->fetchHistory(5, 0);
    });
    poll->start();

    QTimer watchdog;
    watchdog.setSingleShot(true);
    QObject::connect(&watchdog, &QTimer::timeout, [&]() {
        qCritical().noquote() << "[FAIL] 流式冒烟测试超时";
        finish(1);
    });
    watchdog.start(180000);

    qInfo().noquote() << "=== 流式分析冒烟测试开始 ===";
    loop.exec();
    qInfo().noquote() << (exitCode == 0 ? "=== 流式分析冒烟测试通过 ===" : "=== 流式分析冒烟测试失败 ===");
    return exitCode;
}

// ---------------------------------------------------------------------------
// 基准测试
// ---------------------------------------------------------------------------

// 同步跑一次推理并计时。
// 这里故意用嵌套事件循环阻塞等待——基准测试要的是"一次请求的净耗时"，
// 用状态机异步编排反而会把测量点搞乱。业务代码里绝不能这么写。
static bool runOneDetection(fmd::BackendClient *client, const QByteArray &bytes,
                            bool wantAnnotated, int imgsz,
                            fmd::DetectionResult *out, double *elapsedMs)
{
    QEventLoop loop;
    bool ok = false;

    auto c1 = QObject::connect(client, &fmd::BackendClient::detectionFinished,
        [&](const QString &tag, const fmd::DetectionResult &r) {
            if (!tag.isEmpty())
                return;                       // 属于批量任务的响应
            *out = r;
            ok = r.success;
            loop.quit();
        });
    auto c2 = QObject::connect(client, &fmd::BackendClient::requestFailed,
        [&](const QString &op, const QString &) {
            if (op == QLatin1String("detect"))
                loop.quit();
        });

    QElapsedTimer timer;
    timer.start();
    client->detect(bytes, QString(), 0.25, 0.45, imgsz, wantAnnotated,
                   QString(), QStringLiteral("bench.jpg"));

    QTimer::singleShot(180000, &loop, &QEventLoop::quit);
    loop.exec();

    QObject::disconnect(c1);
    QObject::disconnect(c2);
    *elapsedMs = timer.elapsed();
    return ok;
}

int runBenchmark(const QString &imagePath, int iterations)
{
    QFile file(imagePath);
    if (!file.open(QIODevice::ReadOnly)) {
        qCritical().noquote() << "[FAIL] 无法读取图片:" << imagePath;
        return 1;
    }
    const QByteArray imageBytes = file.readAll();

    fmd::MainWindow window;
    window.show();
    auto *client = window.client();

    // 等后端就绪
    {
        QEventLoop loop;
        QTimer poll;
        poll.setInterval(500);
        QObject::connect(&poll, &QTimer::timeout, [&]() {
            if (window.isBackendConnected())
                loop.quit();
        });
        poll.start();
        QTimer::singleShot(120000, &loop, &QEventLoop::quit);
        loop.exec();
    }
    if (!window.isBackendConnected()) {
        qCritical().noquote() << "[FAIL] 后端未就绪，无法基准测试";
        return 1;
    }

    qInfo().noquote() << "=== 基准测试 ===";
    qInfo().noquote() << "图片:" << QFileInfo(imagePath).fileName()
                      << "(" << imageBytes.size() / 1024.0 << "KB )"
                      << "| 每档迭代" << iterations << "次";

    fmd::DetectionResult result;
    double ms = 0;

    // 预热：第一次会触发 CUDA 上下文初始化，不计入统计
    runOneDetection(client, imageBytes, false, 640, &result, &ms);
    qInfo().noquote() << QString("预热一次完成（%1 ms，含 CUDA/模型初始化）").arg(ms, 0, 'f', 0);

    struct Row { QString label; double avgMs; double avgBytes; int detections; };
    QVector<Row> rows;

    auto measure = [&](const QString &label, bool wantAnnotated, int imgsz) {
        double total = 0;
        double totalBytes = 0;
        int    dets = 0;
        for (int i = 0; i < iterations; ++i) {
            double one = 0;
            if (!runOneDetection(client, imageBytes, wantAnnotated, imgsz, &result, &one)) {
                qCritical().noquote() << "[FAIL] 基准测试请求失败:" << label;
                return false;
            }
            total += one;
            totalBytes += result.annotatedPng.size();
            dets = result.totalDetections;
        }
        rows.append({ label, total / iterations, totalBytes / iterations, dets });
        return true;
    };

    // 核心对比：服务端把标注图烧进 PNG（base64 回传） vs 只回结构化数据由客户端画框
    if (!measure(QStringLiteral("服务端渲染图 (base64 回传)"), true, 640))
        return 1;
    if (!measure(QStringLiteral("客户端自绘 (仅结构化 JSON)"), false, 640))
        return 1;

    // 推理尺寸对耗时的影响
    measure(QStringLiteral("客户端自绘 @ imgsz=320"), false, 320);
    measure(QStringLiteral("客户端自绘 @ imgsz=1280"), false, 1280);

    // base64 的膨胀率：JSON 里是 base64 文本，比二进制大约 4/3
    qInfo().noquote() << "";
    qInfo().noquote() << "| 方案 | 平均端到端耗时 (ms) | 标注图体积 (KB) | base64 后约 (KB) |";
    qInfo().noquote() << "|---|---|---|---|";
    for (const Row &row : rows) {
        qInfo().noquote() << QString("| %1 | %2 | %3 | %4 |")
                                 .arg(row.label)
                                 .arg(row.avgMs, 0, 'f', 0)
                                 .arg(row.avgBytes / 1024.0, 0, 'f', 1)
                                 .arg(row.avgBytes * 4.0 / 3.0 / 1024.0, 0, 'f', 1);
    }
    qInfo().noquote() << "";
    qInfo().noquote() << QString("检测目标数（各档一致，验证结果未因渲染方式改变）: %1")
                             .arg(rows.isEmpty() ? 0 : rows.first().detections);
    qInfo().noquote() << "=== 基准测试结束 ===";
    return 0;
}

// 国际化验证：加载指定语言，检查若干关键字符串确实被翻译。
// 不依赖界面，可在无人环境跑，用于 CI 回归。
// sourceLanguage=true 表示被测语言就是源码语言（中文），此时"未翻译"是正确行为，
// 要验证的反而是能否优雅回退到源字符串。
int runI18nCheck(bool sourceLanguage)
{
    struct Probe { const char *context; const char *source; };
    const Probe probes[] = {
        { "fmd::MainWindow",   "\u68c0\u6d4b" },              // 检测
        { "fmd::MainWindow",   "\u5386\u53f2\u8bb0\u5f55" }, // 历史记录
        { "fmd::DetectView",   "\u5f00\u59cb\u68c0\u6d4b" }, // 开始检测
        { "fmd::SettingsView", "\u4fdd\u5b58" },              // 保存
        { "fmd::HistoryView",  "\u5237\u65b0" },              // 刷新
        { "fmd::BatchView",    "\u5f00\u59cb\u6279\u91cf\u68c0\u6d4b" }, // 开始批量检测
    };

    int  translated = 0;
    const int total = int(sizeof(probes) / sizeof(probes[0]));

    for (const Probe &probe : probes) {
        const QString source = QString::fromUtf8(probe.source);
        const QString result = QCoreApplication::translate(probe.context, probe.source);
        const bool changed = (result != source);
        if (changed)
            ++translated;
        qInfo().noquote() << QString("%1  [%2] %3  ->  %4")
                                 .arg(changed ? "OK  " : "MISS")
                                 .arg(QString::fromLatin1(probe.context))
                                 .arg(source, result);
    }

    qInfo().noquote() << QString("\u7ffb\u8bd1\u547d\u4e2d %1 / %2").arg(translated).arg(total);

    if (sourceLanguage) {
        const bool ok = (translated == 0);   // 源语言不应有翻译，且必须能回退
        qInfo().noquote() << (ok ? "\u6e90\u8bed\u8a00\uff1a\u5168\u90e8\u56de\u9000\u5230\u6e90\u5b57\u7b26\u4e32\uff08\u7b26\u5408\u9884\u671f\uff09"
                                     : "\u6e90\u8bed\u8a00\u4e0d\u5e94\u51fa\u73b0\u7ffb\u8bd1");
        return ok ? 0 : 1;
    }
    return translated == total ? 0 : 1;
}

} // namespace

int main(int argc, char *argv[])
{
#ifdef Q_OS_WIN
    // Windows 控制台默认 GBK 代码页，而 Qt 日志输出 UTF-8，
    // 不切到 UTF-8 的话中文日志全是乱码。
    SetConsoleOutputCP(CP_UTF8);
#endif
    qInstallMessageHandler(utf8MessageHandler);

    // Qt5 必须手动开启高 DPI（Qt6 已默认）
    QApplication::setAttribute(Qt::AA_EnableHighDpiScaling);
    QApplication::setAttribute(Qt::AA_UseHighDpiPixmaps);

    QApplication app(argc, argv);
    app.setApplicationName(QStringLiteral("FaceMaskDetection Client"));
    app.setOrganizationName(QStringLiteral("FMD"));
    app.setApplicationVersion(QStringLiteral("0.1.0"));

    const QStringList args = app.arguments();

    // 翻译要在任何界面构造之前装好
    const QString language = resolveLanguage(args);
    const bool loaded = installTranslator(app, language);
    installQtTranslator(app, language);

    if (args.contains(QStringLiteral("--check-i18n"))) {
        qInfo().noquote() << "语言 =" << language
                          << "| 翻译文件加载 =" << (loaded ? "成功" : "未找到（回退源字符串）");
        // 中文是源码语言，不能要求它"被翻译"——那时要验的是回退行为
        const bool isSourceLanguage = language.startsWith(QLatin1String("zh"));
        const int rc = runI18nCheck(isSourceLanguage);
        qInfo().noquote() << (rc == 0 ? "=== 国际化检查通过 ===" : "=== 国际化检查失败 ===");
        return rc;
    }

    if (args.contains(QStringLiteral("--list-langs"))) {
        for (const LanguageOption &option : kLanguages)
            qInfo().noquote() << QString("%1  %2")
                                     .arg(QString::fromLatin1(option.code), -8)
                                     .arg(QString::fromUtf8(option.label));
        return 0;
    }

    const int idx = args.indexOf(QStringLiteral("--selftest"));
    if (idx >= 0) {
        QString image;
        if (idx + 1 < args.size() && !args.at(idx + 1).startsWith(QLatin1String("--")))
            image = args.at(idx + 1);
        return runSelfTest(image);
    }

    const int smokeIdx = args.indexOf(QStringLiteral("--smoke-ui"));
    if (smokeIdx >= 0) {
        QString image;
        if (smokeIdx + 1 < args.size() && !args.at(smokeIdx + 1).startsWith(QLatin1String("--")))
            image = args.at(smokeIdx + 1);
        return runUiSmokeTest(image);
    }

    const int batchIdx = args.indexOf(QStringLiteral("--smoke-batch"));
    if (batchIdx >= 0) {
        QString dir;
        int limit = 6;
        if (batchIdx + 1 < args.size() && !args.at(batchIdx + 1).startsWith(QLatin1String("--")))
            dir = args.at(batchIdx + 1);
        if (batchIdx + 2 < args.size())
            limit = args.at(batchIdx + 2).toInt();
        return runBatchSmokeTest(dir, limit);
    }

    if (args.contains(QStringLiteral("--smoke-history")))
        return runHistorySmokeTest();

    const int settingsIdx = args.indexOf(QStringLiteral("--smoke-settings"));
    if (settingsIdx >= 0) {
        int port = 8899;
        if (settingsIdx + 1 < args.size())
            port = args.at(settingsIdx + 1).toInt();
        return runSettingsSmokeTest(port);
    }

    if (args.contains(QStringLiteral("--smoke-llm")))
        return runLlmSmokeTest();

    const int benchIdx = args.indexOf(QStringLiteral("--benchmark"));
    if (benchIdx >= 0) {
        QString imagePath;
        int iterations = 3;
        if (benchIdx + 1 < args.size() && !args.at(benchIdx + 1).startsWith(QLatin1String("--")))
            imagePath = args.at(benchIdx + 1);
        if (benchIdx + 2 < args.size())
            iterations = qMax(1, args.at(benchIdx + 2).toInt());
        if (imagePath.isEmpty()) {
            qCritical().noquote() << "用法: fmd_client --benchmark <图片路径> [每档迭代次数]";
            return 2;
        }
        return runBenchmark(imagePath, iterations);
    }

    qInfo().noquote() << "Qt runtime :" << qVersion();

    // 样式表编译进可执行文件（resources.qrc），无需外部文件
    {
        QFile styleFile(QStringLiteral(":/style.qss"));
        if (styleFile.open(QIODevice::ReadOnly | QIODevice::Text))
            app.setStyleSheet(QString::fromUtf8(styleFile.readAll()));
    }

    fmd::MainWindow window;
    window.show();
    return app.exec();
}
