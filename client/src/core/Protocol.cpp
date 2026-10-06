#include "Protocol.h"

#include <QJsonArray>
#include <QJsonValue>

namespace fmd {

DetectionResult DetectionResult::fromJson(const QJsonObject &obj)
{
    DetectionResult r;
    r.success = obj.value(QStringLiteral("success")).toBool(false);

    if (!r.success) {
        r.error = obj.value(QStringLiteral("error")).toString(
                      QStringLiteral("服务端返回失败但未给出原因"));
        return r;
    }

    r.recordId        = obj.value(QStringLiteral("record_id")).toInt();
    r.processingTime  = obj.value(QStringLiteral("processing_time")).toDouble();
    r.imageWidth      = obj.value(QStringLiteral("image_width")).toInt();
    r.imageHeight     = obj.value(QStringLiteral("image_height")).toInt();
    r.totalDetections = obj.value(QStringLiteral("total_detections")).toInt();

    const QJsonObject counts = obj.value(QStringLiteral("counts")).toObject();
    for (auto it = counts.constBegin(); it != counts.constEnd(); ++it)
        r.counts.insert(it.key(), it.value().toInt());

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

} // namespace fmd
