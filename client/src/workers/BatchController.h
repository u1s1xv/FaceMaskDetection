#pragma once

// 批量检测调度器。
//
// 并发策略说明（面试常问）：
//   这里限制的不是"线程数"，而是**在途请求数**。推理在服务端是串行的
//   （GPU 同一时刻只能跑一个模型），客户端把几十个请求同时打过去只会
//   让服务端排队、内存暴涨，进度反馈也会失真。
//   所以采用两级背压：
//     1) 预读上限：最多 readAhead 个文件同时在读，不把整批图片读进内存
//     2) 在途上限：最多 maxConcurrent 个请求挂在网络上，完成一个补一个

#include <QByteArray>
#include <QObject>
#include <QSet>
#include <QString>
#include <QStringList>
#include <QVector>

#include "core/Protocol.h"

class QThreadPool;

namespace fmd {

class BackendClient;

class BatchController : public QObject
{
    Q_OBJECT
public:
    explicit BatchController(BackendClient *client, QObject *parent = nullptr);

    void setMaxConcurrent(int n);
    int  maxConcurrent() const { return m_maxConcurrent; }

    void setInferenceParams(const QString &model, double conf, double iou, int imgsz);

    void addFiles(const QStringList &paths);
    void start();
    void cancel();
    void clear();

    int  totalCount()    const { return m_jobs.size(); }
    int  succeededCount() const { return m_succeeded; }
    int  failedCount()    const { return m_failed; }
    int  finishedCount()  const { return m_succeeded + m_failed; }
    bool isRunning()      const { return m_running; }

    QStringList filePaths() const;

signals:
    void jobFinished(const QString &filePath, const fmd::DetectionResult &result);
    void jobFailed(const QString &filePath, const QString &error);
    void progressChanged(int finished, int succeeded, int failed, int total);
    void batchFinished(int succeeded, int failed, bool cancelled);
    void logMessage(const QString &message);

private slots:
    void onDetectionFinished(const QString &tag, const fmd::DetectionResult &result);
    void onRequestFailed(const QString &operation, const QString &error);
    void onFileRead(const QString &filePath, const QImage &image,
                    const QByteArray &bytes, qint64 elapsedMs);
    void onFileReadFailed(const QString &filePath, const QString &error);

private:
    enum class State { Pending, Reading, Ready, InFlight, Done, Failed };

    struct Job {
        QString    path;
        QByteArray bytes;
        State      state = State::Pending;
    };

    void pump();
    void checkFinished();
    int  indexOf(const QString &path) const;
    void completeJob(int index, bool success);

    BackendClient *m_client = nullptr;
    QThreadPool   *m_pool   = nullptr;

    QVector<Job>  m_jobs;
    QSet<QString> m_inFlight;

    int  m_maxConcurrent = 4;
    int  m_succeeded     = 0;
    int  m_failed        = 0;
    bool m_running       = false;
    bool m_cancelled     = false;

    QString m_model;
    double  m_conf  = 0.25;
    double  m_iou   = 0.45;
    int     m_imgsz = 640;
};

} // namespace fmd
