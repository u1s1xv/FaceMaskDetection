#include "Protocol.h"
#include <QCoreApplication>

#include <QJsonArray>
#include <QJsonValue>

namespace fmd {

namespace {

// 检测框与计数的解析在多处用到（单图结果、实时管线状态），抽出来避免各写一遍。
QVector<Detection> detectionsFromJson(const QJsonArray &arr)
{
    QVector<Detection> out;
    out.reserve(arr.size());
    for (const QJsonValue &v : arr) {
        const QJsonObject d = v.toObject();
        Detection det;
        det.classId    = d.value(QStringLiteral("class_id")).toInt(-1);
        det.className  = d.value(QStringLiteral("class_name")).toString();
        det.confidence = d.value(QStringLiteral("confidence")).toDouble();
        det.x1 = d.value(QStringLiteral("x1")).toDouble();
        det.y1 = d.value(QStringLiteral("y1")).toDouble();
        det.x2 = d.value(QStringLiteral("x2")).toDouble();
        det.y2 = d.value(QStringLiteral("y2")).toDouble();
        out.append(det);
    }
    return out;
}

QHash<QString, int> countsFromJson(const QJsonObject &obj)
{
    QHash<QString, int> out;
    for (auto it = obj.constBegin(); it != obj.constEnd(); ++it)
        out.insert(it.key(), it.value().toInt());
    return out;
}

} // namespace

DetectionResult DetectionResult::fromJson(const QJsonObject &obj)
{
    DetectionResult r;
    r.success = obj.value(QStringLiteral("success")).toBool(false);

    if (!r.success) {
        r.error = obj.value(QStringLiteral("error")).toString(
                      QCoreApplication::translate("Protocol", "服务端返回失败但未给出原因"));
        return r;
    }

    r.recordId        = obj.value(QStringLiteral("record_id")).toInt();
    r.processingTime  = obj.value(QStringLiteral("processing_time")).toDouble();
    r.imageWidth      = obj.value(QStringLiteral("image_width")).toInt();
    r.imageHeight     = obj.value(QStringLiteral("image_height")).toInt();
    r.totalDetections = obj.value(QStringLiteral("total_detections")).toInt();

    r.counts     = countsFromJson(obj.value(QStringLiteral("counts")).toObject());
    r.detections = detectionsFromJson(obj.value(QStringLiteral("detections")).toArray());

    const QString b64 = obj.value(QStringLiteral("annotated_image_b64")).toString();
    if (!b64.isEmpty())
        r.annotatedPng = QByteArray::fromBase64(b64.toLatin1());

    return r;
}

HistoryRecord HistoryRecord::fromJson(const QJsonObject &obj)
{
    HistoryRecord r;
    r.id              = obj.value(QStringLiteral("id")).toInt();
    r.fileName        = obj.value(QStringLiteral("file_name")).toString();
    r.imageWidth      = obj.value(QStringLiteral("image_width")).toInt();
    r.imageHeight     = obj.value(QStringLiteral("image_height")).toInt();
    r.modelName       = obj.value(QStringLiteral("model_name")).toString();
    r.totalDetections = obj.value(QStringLiteral("total_detections")).toInt();
    r.withMask        = obj.value(QStringLiteral("with_mask_count")).toInt();
    r.withoutMask     = obj.value(QStringLiteral("without_mask_count")).toInt();
    r.incorrectMask   = obj.value(QStringLiteral("incorrect_mask_count")).toInt();
    r.processingTime  = obj.value(QStringLiteral("processing_time")).toDouble();
    r.queueWait       = obj.value(QStringLiteral("queue_wait")).toDouble();
    r.status          = obj.value(QStringLiteral("status")).toString();
    r.createdAt       = obj.value(QStringLiteral("created_at")).toString();

    const QJsonArray dets = obj.value(QStringLiteral("detections")).toArray();
    r.detections.reserve(dets.size());
    for (const QJsonValue &v : dets) {
        const QJsonObject d = v.toObject();
        Detection det;
        det.classId    = d.value(QStringLiteral("class_id")).toInt(-1);
        det.className  = d.value(QStringLiteral("class_name")).toString();
        det.confidence = d.value(QStringLiteral("confidence")).toDouble();
        det.x1 = d.value(QStringLiteral("x1")).toDouble();
        det.y1 = d.value(QStringLiteral("y1")).toDouble();
        det.x2 = d.value(QStringLiteral("x2")).toDouble();
        det.y2 = d.value(QStringLiteral("y2")).toDouble();
        r.detections.append(det);
    }
    return r;
}

QVector<HistoryRecord> HistoryRecord::listFromJson(const QJsonObject &obj)
{
    QVector<HistoryRecord> items;
    const QJsonArray arr = obj.value(QStringLiteral("items")).toArray();
    items.reserve(arr.size());
    for (const QJsonValue &v : arr)
        items.append(HistoryRecord::fromJson(v.toObject()));
    return items;
}

QVector<ModelInfo> ModelInfo::listFromJson(const QJsonObject &obj)
{
    QVector<ModelInfo> models;
    const QJsonArray arr = obj.value(QStringLiteral("models")).toArray();
    models.reserve(arr.size());
    for (const QJsonValue &v : arr) {
        const QJsonObject m = v.toObject();
        ModelInfo info;
        info.name     = m.value(QStringLiteral("name")).toString();
        info.sizeMb   = m.value(QStringLiteral("size_mb")).toDouble();
        info.modified = m.value(QStringLiteral("modified")).toString();
        models.append(info);
    }
    return models;
}

HealthInfo HealthInfo::fromJson(const QJsonObject &obj)
{
    HealthInfo h;
    h.status      = obj.value(QStringLiteral("status")).toString();
    h.ok          = (h.status == QLatin1String("ok"));
    h.device      = obj.value(QStringLiteral("device")).toString();
    h.torch       = obj.value(QStringLiteral("torch")).toString();
    h.ultralytics = obj.value(QStringLiteral("ultralytics")).toString();
    h.gpu         = obj.value(QStringLiteral("gpu")).toString();
    h.modelDir    = obj.value(QStringLiteral("models_dir")).toString();
    h.error       = obj.value(QStringLiteral("error")).toString();
    return h;
}

// ---------------- 视频源 / 实时监控 ----------------

QVector<CameraDevice> CameraDevice::listFromJson(const QJsonArray &arr)
{
    QVector<CameraDevice> out;
    out.reserve(arr.size());
    for (const QJsonValue &v : arr) {
        const QJsonObject o = v.toObject();
        CameraDevice d;
        d.index   = o.value(QStringLiteral("index")).toInt();
        d.backend = o.value(QStringLiteral("backend")).toString();
        d.width   = o.value(QStringLiteral("width")).toInt();
        d.height  = o.value(QStringLiteral("height")).toInt();
        out.append(d);
    }
    return out;
}

LiveStats LiveStats::fromJson(const QJsonObject &obj)
{
    LiveStats s;
    s.running       = obj.value(QStringLiteral("running")).toBool(false);
    s.processed     = obj.value(QStringLiteral("processed")).toInt();
    s.inferMs       = obj.value(QStringLiteral("infer_ms")).toDouble();
    s.e2eMs         = obj.value(QStringLiteral("e2e_ms")).toDouble();
    s.jpegKb        = obj.value(QStringLiteral("jpeg_kb")).toDouble();
    s.droppedFrames = obj.value(QStringLiteral("dropped_frames")).toInt();
    s.lastError     = obj.value(QStringLiteral("last_error")).toString();

    const QJsonObject latest = obj.value(QStringLiteral("latest")).toObject();
    s.total      = latest.value(QStringLiteral("total")).toInt();
    s.counts     = countsFromJson(latest.value(QStringLiteral("counts")).toObject());
    s.detections = detectionsFromJson(latest.value(QStringLiteral("detections")).toArray());
    return s;
}

CameraInfo CameraInfo::fromJson(const QJsonObject &obj)
{
    CameraInfo c;
    c.id      = obj.value(QStringLiteral("cam_id")).toString();
    c.name    = obj.value(QStringLiteral("name")).toString();
    c.source  = obj.value(QStringLiteral("source")).toString();
    c.kind    = obj.value(QStringLiteral("kind")).toString();
    c.backend = obj.value(QStringLiteral("backend")).toString();
    c.fps     = obj.value(QStringLiteral("fps")).toDouble();
    c.frames  = obj.value(QStringLiteral("frames")).toInt();
    c.width   = obj.value(QStringLiteral("width")).toInt();
    c.height  = obj.value(QStringLiteral("height")).toInt();
    c.running = obj.value(QStringLiteral("running")).toBool(false);
    c.live    = LiveStats::fromJson(obj.value(QStringLiteral("live")).toObject());
    return c;
}

QVector<CameraInfo> CameraInfo::listFromJson(const QJsonArray &arr)
{
    QVector<CameraInfo> out;
    out.reserve(arr.size());
    for (const QJsonValue &v : arr)
        out.append(CameraInfo::fromJson(v.toObject()));
    return out;
}

} // namespace fmd
