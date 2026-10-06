#pragma once

// 与 Python 推理服务通信的网络层。
// 全程异步：每个请求通过信号回传结果，绝不阻塞调用线程。

#include <QImage>
#include <QJsonObject>
#include <QObject>
#include <QUrl>

#include "MjpegParser.h"
#include "Protocol.h"
#include "SseParser.h"

class QNetworkAccessManager;
class QNetworkReply;
class QTimer;

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

    // ---- 视频源 / 实时监控 ----
    //
    // 只用一个轮询端点 /cameras：它同时返回"本机可用设备"、"已打开列表"
    // 和"实时管线状态"。分开成多个端点会让客户端维护多套状态，容易不同步。
    void fetchCameras();
    void openCamera(const QString &source, const QString &name = QString());
    void closeCamera(const QString &camId);

    // 运行时切换画面镜像。镜像由服务端做 —— 因为帧率/延迟那些 OSD 文字
    // 是服务端画进画面里的，客户端整体翻转会把文字也镜像掉。
    void setCameraMirror(const QString &camId, bool mirror);

    // MJPEG 长连接。同一时刻只维持一路 —— 界面上一次只看一个画面，
    // 多开只会浪费带宽和 CPU。
    void startStream(const QString &camId);
    void stopStream();
    bool isStreaming() const { return m_streamReply != nullptr; }
    qint64 streamFrameCount() const { return m_streamFrames; }
    qint64 streamBytes() const { return m_streamBytes; }

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
    void camerasReceived(const QVector<fmd::CameraDevice> &devices,
                         const QVector<fmd::CameraInfo> &opened);
    void cameraOpened(const QString &camId, const fmd::CameraInfo &info);
    void cameraClosed(const QString &camId);
    void streamStarted(const QString &camId);
    void streamFrame(const QImage &frame);
    void streamStopped(const QString &camId, const QString &reason);

    void llmModelsReceived(const QStringList &models, const QString &defaultModel, bool keyConfigured);
    void analysisStarted(const QString &model, bool mockMode);
    void analysisChunk(const QString &text);
    void analysisFinished();
    void analysisFailed(const QString &error);
    void detectionFinished(const QString &tag, const fmd::DetectionResult &result);
    void requestFailed(const QString &operation, const QString &error);

private:
    QNetworkReply *get(const QString &path, const QString &opName);
    QNetworkReply *postJson(const QString &path, const QJsonObject &body, const QString &opName);
    QNetworkReply *del(const QString &path, const QString &opName);
    QNetworkReply *post(const QString &path, const QByteArray &body, const QString &opName,
                        const QString &tag = QString());

    QNetworkAccessManager *m_nam = nullptr;
    QUrl    m_baseUrl;
    int     m_timeoutMs = 300000;
    quint64 m_requestCounter = 0;
    SseParser m_sseParser;      // SSE 流式响应的增量解析状态

    // MJPEG 长连接状态
    QNetworkReply *m_streamReply  = nullptr;
    QString        m_streamCamId;
    MjpegParser    m_mjpegParser;
    qint64         m_streamFrames = 0;
    qint64         m_streamBytes  = 0;

    // 推流看门狗：连上了但迟迟没有数据时自动重连。
    // 服务端在"管线尚未产出第一帧"与"客户端恰好此刻连接"之间存在竞态，
    // 实测约 1/3 的概率会出现"HTTP 200 但零字节"。与其在服务端赌时序，
    // 不如让客户端具备自愈能力 —— 这本来就是网络客户端该有的健壮性。
    QTimer        *m_streamWatchdog = nullptr;
    qint64         m_streamAttemptStartBytes = 0;
    int            m_streamRetries = 0;
    static constexpr int kStreamRetryLimit = 3;
    static constexpr int kStreamStallMs    = 2500;
};

} // namespace fmd
