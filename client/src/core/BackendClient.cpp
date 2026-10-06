#include "BackendClient.h"

#include <QJsonArray>
#include <QJsonDocument>
#include <QJsonObject>
#include <QNetworkAccessManager>
#include <QNetworkReply>
#include <QNetworkRequest>
#include <QTimer>
#include <QUrlQuery>
#include <QDebug>

namespace fmd {

BackendClient::BackendClient(QObject *parent)
    : QObject(parent)
    , m_nam(new QNetworkAccessManager(this))
    , m_baseUrl(QStringLiteral("http://127.0.0.1:8756"))
{
}

void BackendClient::setBaseUrl(const QUrl &url)
{
    m_baseUrl = url;
}

QNetworkReply *BackendClient::get(const QString &path, const QString &opName)
{
    // 注意：QUrl::setPath() 会把 '?' 百分号编码成 %3F，直接把
    // "/history?limit=50" 塞进 setPath 会变成路径的一部分，服务端只会返回 404。
    // 必须把 path 和 query 拆开分别设置。
    QUrl url(m_baseUrl);
    const int queryPos = path.indexOf(QLatin1Char('?'));
    if (queryPos >= 0) {
        url.setPath(path.left(queryPos));
        url.setQuery(path.mid(queryPos + 1));
    } else {
        url.setPath(path);
    }

    QNetworkRequest req(url);
    req.setTransferTimeout(m_timeoutMs);
    req.setHeader(QNetworkRequest::UserAgentHeader, QStringLiteral("FMD-Client/0.1"));

    QNetworkReply *reply = m_nam->get(req);
    QObject::connect(reply, &QNetworkReply::finished, this, [this, reply, opName]() {
        reply->deleteLater();
        if (reply->error() != QNetworkReply::NoError) {
            emit requestFailed(opName, reply->errorString());
            return;
        }
        const QJsonObject obj = QJsonDocument::fromJson(reply->readAll()).object();
        if (opName == QLatin1String("health"))
            emit healthReceived(HealthInfo::fromJson(obj));
        else if (opName == QLatin1String("models"))
            emit modelsReceived(ModelInfo::listFromJson(obj));
        else if (opName == QLatin1String("history"))
            emit historyReceived(obj.value(QStringLiteral("total")).toInt(),
                                 HistoryRecord::listFromJson(obj));
        else if (opName == QLatin1String("record"))
            emit recordReceived(HistoryRecord::fromJson(
                obj.value(QStringLiteral("record")).toObject()));
        else if (opName == QLatin1String("cameras"))
            emit camerasReceived(CameraDevice::listFromJson(
                                     obj.value(QStringLiteral("devices")).toArray()),
                                 CameraInfo::listFromJson(
                                     obj.value(QStringLiteral("opened")).toArray()));
    });
    return reply;
}

QNetworkReply *BackendClient::post(const QString &path, const QByteArray &body, const QString &opName,
                                   const QString &tag)
{
    QUrl url(m_baseUrl);
    url.setPath(path);

    QNetworkRequest req(url);
    req.setTransferTimeout(m_timeoutMs);
    req.setHeader(QNetworkRequest::ContentTypeHeader, QStringLiteral("application/octet-stream"));
    req.setHeader(QNetworkRequest::UserAgentHeader, QStringLiteral("FMD-Client/0.1"));

    QNetworkReply *reply = m_nam->post(req, body);
    QObject::connect(reply, &QNetworkReply::finished, this, [this, reply, opName, tag]() {
        reply->deleteLater();
        if (reply->error() != QNetworkReply::NoError) {
            // 把 tag 附在错误里，批量场景才能定位是哪个文件失败
            emit requestFailed(tag.isEmpty() ? opName : opName + QLatin1Char('|') + tag,
                               reply->errorString());
            return;
        }
        const QJsonObject obj = QJsonDocument::fromJson(reply->readAll()).object();
        if (opName == QLatin1String("detect"))
            emit detectionFinished(tag, DetectionResult::fromJson(obj));
    });
    return reply;
}

QNetworkReply *BackendClient::postJson(const QString &path, const QJsonObject &body,
                                       const QString &opName)
{
    QUrl url(m_baseUrl);
    url.setPath(path);

    QNetworkRequest req(url);
    req.setTransferTimeout(m_timeoutMs);
    req.setHeader(QNetworkRequest::ContentTypeHeader,
                  QStringLiteral("application/json"));
    req.setHeader(QNetworkRequest::UserAgentHeader, QStringLiteral("FMD-Client/0.1"));

    QNetworkReply *reply = m_nam->post(req, QJsonDocument(body).toJson(QJsonDocument::Compact));
    QObject::connect(reply, &QNetworkReply::finished, this, [this, reply, opName]() {
        reply->deleteLater();
        if (reply->error() != QNetworkReply::NoError) {
            // 服务端的 4xx 响应体里有可读的原因（比如"5 秒内没有出帧"），
            // 比 Qt 的 "Bad Request" 有用得多
            const QJsonObject err = QJsonDocument::fromJson(reply->readAll()).object();
            const QString detail = err.value(QStringLiteral("error")).toString();
            emit requestFailed(opName, detail.isEmpty() ? reply->errorString() : detail);
            return;
        }
        const QJsonObject obj = QJsonDocument::fromJson(reply->readAll()).object();
        if (opName == QLatin1String("cameraOpen")) {
            if (!obj.value(QStringLiteral("success")).toBool()) {
                emit requestFailed(opName,
                                   obj.value(QStringLiteral("error")).toString());
                return;
            }
            const QString camId = obj.value(QStringLiteral("cam_id")).toString();
            CameraInfo info = CameraInfo::fromJson(
                obj.value(QStringLiteral("stats")).toObject());
            info.id = camId;          // stats 里没有 cam_id，从外层补上
            emit cameraOpened(camId, info);
        }
    });
    return reply;
}

QNetworkReply *BackendClient::del(const QString &path, const QString &opName)
{
    QUrl url(m_baseUrl);
    url.setPath(path);

    QNetworkRequest req(url);
    req.setTransferTimeout(m_timeoutMs);
    req.setHeader(QNetworkRequest::UserAgentHeader, QStringLiteral("FMD-Client/0.1"));

    QNetworkReply *reply = m_nam->deleteResource(req);
    QObject::connect(reply, &QNetworkReply::finished, this, [this, reply, opName]() {
        reply->deleteLater();
        if (reply->error() != QNetworkReply::NoError) {
            emit requestFailed(opName, reply->errorString());
            return;
        }
        const QJsonObject obj = QJsonDocument::fromJson(reply->readAll()).object();
        if (obj.value(QStringLiteral("success")).toBool())
            emit recordDeleted(obj.value(QStringLiteral("id")).toInt());
    });
    return reply;
}

void BackendClient::fetchHistory(int limit, int offset)
{
    get(QStringLiteral("/history?limit=%1&offset=%2").arg(limit).arg(offset),
        QStringLiteral("history"));
}

void BackendClient::fetchRecord(int id)
{
    get(QStringLiteral("/history/%1").arg(id), QStringLiteral("record"));
}

void BackendClient::deleteRecord(int id)
{
    del(QStringLiteral("/history/%1").arg(id), QStringLiteral("deleteRecord"));
}

void BackendClient::fetchImage(int id)
{
    QUrl url(m_baseUrl);
    url.setPath(QStringLiteral("/image/%1").arg(id));

    QNetworkRequest req(url);
    req.setTransferTimeout(m_timeoutMs);
    req.setHeader(QNetworkRequest::UserAgentHeader, QStringLiteral("FMD-Client/0.1"));

    QNetworkReply *reply = m_nam->get(req);
    QObject::connect(reply, &QNetworkReply::finished, this, [this, reply, id]() {
        reply->deleteLater();
        if (reply->error() != QNetworkReply::NoError) {
            emit requestFailed(QStringLiteral("image"), reply->errorString());
            return;
        }
        emit imageReceived(id, reply->readAll());
    });
}

void BackendClient::fetchLlmModels()
{
    QUrl url(m_baseUrl);
    url.setPath(QStringLiteral("/llm-models"));

    QNetworkRequest req(url);
    req.setTransferTimeout(m_timeoutMs);
    QNetworkReply *reply = m_nam->get(req);
    QObject::connect(reply, &QNetworkReply::finished, this, [this, reply]() {
        reply->deleteLater();
        if (reply->error() != QNetworkReply::NoError) {
            emit requestFailed(QStringLiteral("llmModels"), reply->errorString());
            return;
        }
        const QJsonObject obj = QJsonDocument::fromJson(reply->readAll()).object();
        QStringList models;
        for (const QJsonValue &v : obj.value(QStringLiteral("models")).toArray())
            models.append(v.toString());
        emit llmModelsReceived(models,
                               obj.value(QStringLiteral("default")).toString(),
                               obj.value(QStringLiteral("api_key_configured")).toBool());
    });
}

void BackendClient::analyzeStream(int recordId, const QString &prompt, const QString &model)
{
    // 上一次流可能还残留半帧，必须先清空
    m_sseParser.reset();

    QUrl url(m_baseUrl);
    url.setPath(QStringLiteral("/llm/analyze"));

    QJsonObject body;
    body.insert(QStringLiteral("record_id"), recordId);
    body.insert(QStringLiteral("prompt"), prompt);
    body.insert(QStringLiteral("model"), model);

    QNetworkRequest req(url);
    req.setHeader(QNetworkRequest::ContentTypeHeader, QStringLiteral("application/json"));
    req.setTransferTimeout(300000);         // 大模型生成可能很久，单独放宽

    QNetworkReply *reply = m_nam->post(req, QJsonDocument(body).toJson(QJsonDocument::Compact));

    // 关键：不等 finished，而是随着数据到达增量解析
    QObject::connect(reply, &QNetworkReply::readyRead, this, [this, reply]() {
        for (const SseParser::Event &event : m_sseParser.feed(reply->readAll())) {
            if (event.type == QLatin1String("start")) {
                emit analysisStarted(event.data.value(QStringLiteral("model")).toString(),
                                     event.data.value(QStringLiteral("mock")).toBool());
            } else if (event.type == QLatin1String("content")) {
                emit analysisChunk(event.text);
            } else if (event.type == QLatin1String("error")) {
                emit analysisFailed(event.data.value(QStringLiteral("error")).toString());
            }
        }
    });

    QObject::connect(reply, &QNetworkReply::finished, this, [this, reply]() {
        reply->deleteLater();
        if (reply->error() != QNetworkReply::NoError) {
            emit analysisFailed(reply->errorString());
            return;
        }
        emit analysisFinished();
    });
}

void BackendClient::checkHealth()
{
    get(QStringLiteral("/health"), QStringLiteral("health"));
}

// ---------------- 视频源 / 实时监控 ----------------

void BackendClient::fetchCameras()
{
    get(QStringLiteral("/cameras"), QStringLiteral("cameras"));
}

void BackendClient::openCamera(const QString &source, const QString &name)
{
    QJsonObject body;
    body.insert(QStringLiteral("source"), source);
    if (!name.isEmpty())
        body.insert(QStringLiteral("name"), name);
    postJson(QStringLiteral("/cameras/open"), body, QStringLiteral("cameraOpen"));
}

void BackendClient::closeCamera(const QString &camId)
{
    // 关闭视频源必然要停掉它对应的推流。
    // 不主动停的话，服务端要等空闲超时（10 秒）才会断开，
    // 这段时间客户端一直挂着一个没有数据的连接 —— 界面上表现为
    // "已经点了关闭，但状态还是推流中"。
    // 放在这里而不是调用方，是为了保证不管谁调用都不会漏。
    if (!m_streamCamId.isEmpty() && m_streamCamId == camId)
        stopStream();

    // 关闭结果用 cam_id 回传：服务端的响应体里没有 id，
    // 而调用方需要知道"关掉的是哪一路"（可能已经切到别的摄像头了）。
    QNetworkReply *reply = postJson(QStringLiteral("/cameras/%1/close").arg(camId),
                                    QJsonObject(), QStringLiteral("cameraClose"));
    QObject::connect(reply, &QNetworkReply::finished, this, [this, reply, camId]() {
        // postJson 的通用处理器会先 deleteLater（延后执行），这里仍可读错误码
        if (reply->error() == QNetworkReply::NoError)
            emit cameraClosed(camId);
    });
}

void BackendClient::setCameraMirror(const QString &camId, bool mirror)
{
    QJsonObject body;
    body.insert(QStringLiteral("mirror"), mirror);
    postJson(QStringLiteral("/cameras/%1/mirror").arg(camId), body,
             QStringLiteral("cameraMirror"));
}

void BackendClient::startStream(const QString &camId)
{
    stopStream();

    QUrl url(m_baseUrl);
    url.setPath(QStringLiteral("/cameras/%1/stream.mjpg").arg(camId));

    QNetworkRequest req(url);
    // 推流是长连接，不能沿用单次请求那个 5 分钟超时。
    // 但也**不能设为 0** —— 那在不同 Qt 版本上语义不一致（有的是"无超时"，
    // 有的是"用管理器默认值"）。用 60 秒：服务端 25fps 推流，
    // 静默 60 秒必定是链路已死。该超时会在每次收到数据时重置。
    req.setTransferTimeout(60000);
    req.setHeader(QNetworkRequest::UserAgentHeader, QStringLiteral("FMD-Client/0.1"));

    m_mjpegParser.reset();
    m_streamCamId = camId;
    m_streamFrames = 0;
    m_streamBytes = 0;

    QNetworkReply *reply = m_nam->get(req);
    m_streamReply = reply;
    m_streamAttemptStartBytes = m_streamBytes;

    // 看门狗：连上后迟迟收不到数据就重连（见头文件里的说明）
    if (m_streamWatchdog == nullptr) {
        m_streamWatchdog = new QTimer(this);
        m_streamWatchdog->setSingleShot(true);
        QObject::connect(m_streamWatchdog, &QTimer::timeout, this, [this]() {
            if (m_streamReply == nullptr)
                return;
            if (m_streamBytes > m_streamAttemptStartBytes)
                return;                       // 有数据，说明是正常在推，只是慢
            if (m_streamRetries >= kStreamRetryLimit) {
                const QString camId = m_streamCamId;
                stopStream();
                emit streamStopped(camId, tr("多次重连仍未收到画面"));
                return;
            }
            ++m_streamRetries;
            const QString camId = m_streamCamId;
            qWarning("推流 %s 在 %d ms 内没有数据，第 %d 次重连",
                     qPrintable(camId), kStreamStallMs, m_streamRetries);
            stopStream();
            // 稍等一下再重连：给服务端的管线一点时间产出第一帧
            QTimer::singleShot(600, this, [this, camId]() { startStream(camId); });
        });
    }
    m_streamWatchdog->start(kStreamStallMs);

    QObject::connect(reply, &QNetworkReply::readyRead, this, [this, reply]() {
        if (reply != m_streamReply)
            return;                       // 已经切换到别的流，丢弃过期数据
        const QByteArray chunk = reply->readAll();
        if (chunk.isEmpty())
            return;
        m_streamBytes += chunk.size();
        m_streamRetries = 0;                  // 收到数据就重置重连计数
        if (m_streamWatchdog != nullptr)
            m_streamWatchdog->stop();

        QVector<QByteArray> frames = m_mjpegParser.feed(chunk);
        if (frames.isEmpty())
            return;
        m_streamFrames += frames.size();

        // 一批里可能有多帧（客户端处理慢于服务端时，数据会在 socket 缓冲里积压）。
        // **只解码最后一帧** —— 前面的帧即使解出来也立刻会被覆盖，
        // 白白花掉 3~4 ms/帧的 JPEG 解码。
        // 这与采集端的 latest-frame-wins 是同一个道理：宁可丢帧，不要做无用功。
        const QByteArray jpeg = frames.takeLast();
        const QImage image = QImage::fromData(jpeg, "JPG");
        if (image.isNull())
            return;                       // 坏帧丢掉即可，不能因此中断整路流
        emit streamFrame(image);
    });

    QObject::connect(reply, &QNetworkReply::finished, this, [this, reply]() {
        if (reply != m_streamReply)
            return;                       // stopStream() 主动停止时已置空
        const QString camId = m_streamCamId;
        const bool ok = reply->error() == QNetworkReply::NoError;
        const QString reason = ok ? tr("服务端结束了推流") : reply->errorString();
        reply->deleteLater();
        m_streamReply = nullptr;
        m_streamCamId.clear();
        emit streamStopped(camId, reason);
    });

    emit streamStarted(camId);
}

void BackendClient::stopStream()
{
    QNetworkReply *reply = m_streamReply;
    if (reply == nullptr)
        return;

    const QString camId = m_streamCamId;
    m_streamReply = nullptr;
    m_streamCamId.clear();
    if (m_streamWatchdog != nullptr)
        m_streamWatchdog->stop();

    // 断开连接再 abort：否则 finished 处理器会把它当成"服务端断开"，
    // 界面就会弹出无意义的错误提示。
    QObject::disconnect(reply, nullptr, this, nullptr);
    reply->abort();
    reply->deleteLater();

    emit streamStopped(camId, tr("已停止"));
}

void BackendClient::fetchModels()
{
    get(QStringLiteral("/models"), QStringLiteral("models"));
}

quint64 BackendClient::detect(const QByteArray &imageBytes,
                              const QString &modelName,
                              double conf, double iou, int imgsz,
                              bool wantAnnotated,
                              const QString &tag,
                              const QString &fileName)
{
    const quint64 requestId = ++m_requestCounter;
    QUrl url(m_baseUrl);
    url.setPath(QStringLiteral("/detect"));

    QUrlQuery q;
    if (!modelName.isEmpty())
        q.addQueryItem(QStringLiteral("model"), modelName);
    q.addQueryItem(QStringLiteral("conf"), QString::number(conf));
    q.addQueryItem(QStringLiteral("iou"),  QString::number(iou));
    q.addQueryItem(QStringLiteral("imgsz"), QString::number(imgsz));
    q.addQueryItem(QStringLiteral("return_image"), wantAnnotated ? QStringLiteral("1") : QStringLiteral("0"));
    if (!fileName.isEmpty())
        q.addQueryItem(QStringLiteral("file_name"), fileName);
    url.setQuery(q);

    QNetworkRequest req(url);
    req.setTransferTimeout(m_timeoutMs);
    req.setHeader(QNetworkRequest::ContentTypeHeader, QStringLiteral("application/octet-stream"));
    req.setHeader(QNetworkRequest::UserAgentHeader, QStringLiteral("FMD-Client/0.1"));

    QNetworkReply *reply = m_nam->post(req, imageBytes);
    QObject::connect(reply, &QNetworkReply::finished, this, [this, reply, tag]() {
        reply->deleteLater();
        if (reply->error() != QNetworkReply::NoError) {
            emit requestFailed(tag.isEmpty() ? QStringLiteral("detect")
                                             : QStringLiteral("detect|") + tag,
                               reply->errorString());
            return;
        }
        const QJsonObject obj = QJsonDocument::fromJson(reply->readAll()).object();
        emit detectionFinished(tag, DetectionResult::fromJson(obj));
    });
    return requestId;
}

} // namespace fmd
