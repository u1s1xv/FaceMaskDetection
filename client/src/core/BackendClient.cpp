#include "BackendClient.h"

#include <QJsonArray>
#include <QJsonDocument>
#include <QJsonObject>
#include <QNetworkAccessManager>
#include <QNetworkReply>
#include <QNetworkRequest>
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
