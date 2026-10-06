#pragma once

// 与 Python 推理服务通信的网络层。
// 全程异步：每个请求通过信号回传结果，绝不阻塞调用线程。

#include <QObject>
#include <QUrl>

#include "Protocol.h"
#include "SseParser.h"

class QNetworkAccessManager;
class QNetworkReply;

namespace fmd {

class BackendClient : public QObject
{
    Q_OBJECT
public:
    explicit BackendClient(QObject *parent = nullptr);

    void setBaseUrl(const QUrl &url);
    QUrl baseUrl() const { return m_baseUrl; }

    // 单次请求超时（毫秒）。冷启动首次推理要加载模型，给足时间。
    void setTimeoutMs(int ms) { m_timeoutMs = ms; }

    void checkHealth();
    void fetchModels();

    // ---- 历史记录 ----
    void fetchHistory(int limit = 300, int offset = 0);
    void fetchRecord(int id);
    void deleteRecord(int id);
    void fetchImage(int id);

    // ---- 大模型分析（SSE 流式）----
    void fetchLlmModels();
    void analyzeStream(int recordId, const QString &prompt, const QString &model);
    // tag 用于并发场景下把响应关联回发起方（批量检测按文件路径打标）。
    // 返回自增请求号，便于日志追踪。
    quint64 detect(const QByteArray &imageBytes,
                   const QString &modelName,
                   double conf, double iou, int imgsz,
                   bool wantAnnotated = true,
                   const QString &tag = QString(),
                   const QString &fileName = QString());

signals:
    void healthReceived(const fmd::HealthInfo &info);
    void modelsReceived(const QVector<fmd::ModelInfo> &models);
    void historyReceived(int total, const QVector<fmd::HistoryRecord> &items);
    void recordReceived(const fmd::HistoryRecord &record);
    void recordDeleted(int id);
    void imageReceived(int id, const QByteArray &data);
    void llmModelsReceived(const QStringList &models, const QString &defaultModel, bool keyConfigured);
    void analysisStarted(const QString &model, bool mockMode);
    void analysisChunk(const QString &text);
    void analysisFinished();
    void analysisFailed(const QString &error);
    void detectionFinished(const QString &tag, const fmd::DetectionResult &result);
    void requestFailed(const QString &operation, const QString &error);

private:
    QNetworkReply *get(const QString &path, const QString &opName);
    QNetworkReply *del(const QString &path, const QString &opName);
    QNetworkReply *post(const QString &path, const QByteArray &body, const QString &opName,
                        const QString &tag = QString());

    QNetworkAccessManager *m_nam = nullptr;
    QUrl    m_baseUrl;
    int     m_timeoutMs = 300000;
    quint64 m_requestCounter = 0;
    SseParser m_sseParser;      // 流式响应的增量解析状态
};

} // namespace fmd
