#include "BatchController.h"

#include "core/BackendClient.h"
#include "workers/ImageLoaderTask.h"

#include <QFileInfo>
#include <QThreadPool>

namespace fmd {

BatchController::BatchController(BackendClient *client, QObject *parent)
    : QObject(parent)
    , m_client(client)
    , m_pool(new QThreadPool(this))
{
    m_pool->setMaxThreadCount(qMax(2, QThread::idealThreadCount() - 1));

    connect(m_client, &BackendClient::detectionFinished,
            this, &BatchController::onDetectionFinished);
    connect(m_client, &BackendClient::requestFailed,
            this, &BatchController::onRequestFailed);
}

void BatchController::setMaxConcurrent(int n)
{
    m_maxConcurrent = qBound(1, n, 16);
}

void BatchController::setInferenceParams(const QString &model, double conf, double iou, int imgsz)
{
    m_model = model;
    m_conf  = conf;
    m_iou   = iou;
    m_imgsz = imgsz;
}

void BatchController::addFiles(const QStringList &paths)
{
    for (const QString &path : paths) {
        if (indexOf(path) >= 0)
            continue;                   // 去重，避免同一个文件被算两次
        Job job;
        job.path = path;
        m_jobs.append(job);
    }
}

QStringList BatchController::filePaths() const
{
    QStringList list;
    list.reserve(m_jobs.size());
    for (const Job &j : m_jobs)
        list.append(j.path);
    return list;
}

int BatchController::indexOf(const QString &path) const
{
    for (int i = 0; i < m_jobs.size(); ++i) {
        if (m_jobs[i].path == path)
            return i;
    }
    return -1;
}

void BatchController::clear()
{
    if (m_running)
        return;
    m_jobs.clear();
    m_inFlight.clear();
    m_succeeded = 0;
    m_failed = 0;
    m_cancelled = false;
    emit progressChanged(0, 0, 0, 0);
}

void BatchController::start()
{
    if (m_running || m_jobs.isEmpty())
        return;

    m_running = true;
    m_cancelled = false;
    m_succeeded = 0;
    m_failed = 0;
    m_inFlight.clear();
    for (Job &j : m_jobs) {
        j.state = State::Pending;
        j.bytes.clear();
    }

    emit logMessage(QStringLiteral("批量开始：%1 个文件，最大并发 %2")
                        .arg(m_jobs.size()).arg(m_maxConcurrent));
    emit progressChanged(0, 0, 0, m_jobs.size());
    pump();
}

void BatchController::cancel()
{
    if (!m_running)
        return;
    m_cancelled = true;
    emit logMessage(QStringLiteral("已请求取消：不再派发新任务，在途的 %1 个会跑完")
                        .arg(m_inFlight.size()));
    if (m_inFlight.isEmpty())
        checkFinished();
}

void BatchController::pump()
{
    if (!m_running)
        return;

    // ---- 1) 预读：控制在读文件数，不把整批图一次性读进内存 ----
    const int readAhead = qMax(1, m_maxConcurrent * 2);
    int reading = 0;
    for (const Job &j : m_jobs) {
        if (j.state == State::Reading)
            ++reading;
    }

    if (!m_cancelled) {
        for (Job &job : m_jobs) {
            if (reading >= readAhead)
                break;
            if (job.state != State::Pending)
                continue;
            job.state = State::Reading;
            ++reading;

            auto *task = new ImageLoaderTask(job.path, /*decodeImage=*/false);
            connect(task, &ImageLoaderTask::loaded, this, &BatchController::onFileRead);
            connect(task, &ImageLoaderTask::failed, this, &BatchController::onFileReadFailed);
            m_pool->start(task);
        }
    }

    // ---- 2) 派发：在途请求数上限即背压 ----
    while (!m_cancelled && m_inFlight.size() < size_t(m_maxConcurrent)) {
        int idx = -1;
        for (int i = 0; i < m_jobs.size(); ++i) {
            if (m_jobs[i].state == State::Ready) {
                idx = i;
                break;
            }
        }
        if (idx < 0)
            break;

        Job &job = m_jobs[idx];
        job.state = State::InFlight;
        m_inFlight.insert(job.path);

        m_client->detect(job.bytes, m_model, m_conf, m_iou, m_imgsz,
                         /*wantAnnotated=*/false,
                         job.path,                          // tag：并发时关联回文件
                         QFileInfo(job.path).fileName());   // 历史里显示的文件名
        job.bytes.clear();      // 派发后立刻释放，峰值内存 = 并发数 × 单图大小
    }

    checkFinished();
}

void BatchController::checkFinished()
{
    if (!m_running)
        return;

    // 还有在途请求就必须等；取消时也要等在途的跑完
    if (!m_inFlight.isEmpty())
        return;

    for (const Job &j : m_jobs) {
        if (j.state == State::Pending || j.state == State::Reading
            || j.state == State::Ready || j.state == State::InFlight)
            return;
    }

    m_running = false;
    emit logMessage(QStringLiteral("批量结束：成功 %1，失败 %2%3")
                        .arg(m_succeeded).arg(m_failed)
                        .arg(m_cancelled ? QStringLiteral("（已取消）") : QString()));
    emit batchFinished(m_succeeded, m_failed, m_cancelled);
}

void BatchController::completeJob(int index, bool success)
{
    if (index < 0 || index >= m_jobs.size())
        return;
    Job &job = m_jobs[index];
    job.state = success ? State::Done : State::Failed;
    job.bytes.clear();
    m_inFlight.remove(job.path);

    if (success)
        ++m_succeeded;
    else
        ++m_failed;

    emit progressChanged(finishedCount(), m_succeeded, m_failed, m_jobs.size());
    pump();
}

void BatchController::onFileRead(const QString &filePath, const QImage &,
                                 const QByteArray &bytes, qint64)
{
    const int idx = indexOf(filePath);
    if (idx < 0)
        return;

    Job &job = m_jobs[idx];
    if (job.state != State::Reading)
        return;

    job.bytes = bytes;
    job.state = State::Ready;
    pump();
}

void BatchController::onFileReadFailed(const QString &filePath, const QString &error)
{
    const int idx = indexOf(filePath);
    if (idx < 0)
        return;
    emit logMessage(QStringLiteral("读取失败 %1：%2")
                        .arg(QFileInfo(filePath).fileName(), error));
    emit jobFailed(filePath, error);
    completeJob(idx, false);
}

void BatchController::onDetectionFinished(const QString &tag, const DetectionResult &result)
{
    if (tag.isEmpty())
        return;             // 不是批量任务发起的

    const int idx = indexOf(tag);
    if (idx < 0)
        return;

    if (result.success) {
        emit jobFinished(tag, result);
        completeJob(idx, true);
    } else {
        emit jobFailed(tag, result.error);
        completeJob(idx, false);
    }
}

void BatchController::onRequestFailed(const QString &operation, const QString &error)
{
    const int sep = operation.indexOf(QLatin1Char('|'));
    if (sep < 0 || operation.left(sep) != QLatin1String("detect"))
        return;

    const QString tag = operation.mid(sep + 1);
    const int idx = indexOf(tag);
    if (idx < 0)
        return;

    emit logMessage(QStringLiteral("请求失败 %1：%2")
                        .arg(QFileInfo(tag).fileName(), error));
    emit jobFailed(tag, error);
    completeJob(idx, false);
}

} // namespace fmd
