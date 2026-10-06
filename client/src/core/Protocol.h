#pragma once

// 客户端与服务端之间的数据契约。
// 所有 JSON 解析集中在这里，界面层不碰 QJsonObject。

#include <QByteArray>
#include <QHash>
#include <QJsonArray>
#include <QJsonObject>
#include <QString>
#include <QVector>

namespace fmd {

struct Detection {
    int    classId    = -1;
    QString className;
    double confidence = 0.0;
    double x1 = 0.0, y1 = 0.0, x2 = 0.0, y2 = 0.0;   // 像素坐标
};

struct DetectionResult {
    bool    success     = false;
    QString error;
    int     recordId    = 0;      // 服务端落库后返回的记录 id，0 表示未落库
    double  processingTime = 0.0;
    int     imageWidth  = 0;
    int     imageHeight = 0;
    int     totalDetections = 0;
    QHash<QString, int> counts;
    QVector<Detection>  detections;
    QByteArray annotatedPng;      // 已从 base64 解码

    static DetectionResult fromJson(const QJsonObject &obj);
};

// 一条检测历史（列表接口只返回摘要，详情接口才带 detections）
struct HistoryRecord {
    int     id = 0;
    QString fileName;
    int     imageWidth  = 0;
    int     imageHeight = 0;
    QString modelName;
    int     totalDetections  = 0;
    int     withMask        = 0;
    int     withoutMask     = 0;
    int     incorrectMask   = 0;
    double  processingTime  = 0.0;
    double  queueWait       = 0.0;
    QString status;
    QString createdAt;
    QVector<Detection> detections;      // 仅详情接口填充

    static HistoryRecord fromJson(const QJsonObject &obj);
    static QVector<HistoryRecord> listFromJson(const QJsonObject &obj);
};

// ---------------- 视频源 / 实时监控 ----------------

// 本机可用的摄像头（由服务端枚举）
struct CameraDevice {
    int     index = 0;
    QString backend;
    int     width  = 0;
    int     height = 0;

    static QVector<CameraDevice> listFromJson(const QJsonArray &arr);
};

// 实时推理管线的运行状态（对应服务端的 LivePipeline.stats）
struct LiveStats {
    bool    running       = false;
    int     processed     = 0;
    double  inferMs       = 0.0;
    double  e2eMs         = 0.0;
    double  jpegKb        = 0.0;
    int     droppedFrames = 0;
    QString lastError;
    bool    mirror        = true;    // 画面是否镜像（服务端做的显示变换）

    // 最近一帧的检测结果
    int     total = 0;
    QHash<QString, int> counts;
    QVector<Detection>  detections;

    static LiveStats fromJson(const QJsonObject &obj);
};

// 一个已打开的视频源
struct CameraInfo {
    QString id;
    QString name;
    QString source;
    QString kind;          // device / file / stream
    QString backend;
    double  fps    = 0.0;
    int     frames = 0;
    int     width  = 0;
    int     height = 0;
    bool    running = false;
    LiveStats live;

    static CameraInfo fromJson(const QJsonObject &obj);
    static QVector<CameraInfo> listFromJson(const QJsonArray &arr);
};

struct ModelInfo {
    QString name;
    double  sizeMb = 0.0;
    QString modified;

    static QVector<ModelInfo> listFromJson(const QJsonObject &obj);
};

struct HealthInfo {
    bool    ok = false;
    QString status;
    QString device;
    QString torch;
    QString ultralytics;
    QString gpu;
    QString modelDir;
    QString error;

    static HealthInfo fromJson(const QJsonObject &obj);
};

} // namespace fmd
