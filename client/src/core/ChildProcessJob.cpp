// windows.h 必须放在 Qt 头之前，并关掉 min/max 宏，否则会和 std/Qt 冲突
#ifdef _WIN32
#  define WIN32_LEAN_AND_MEAN
#  define NOMINMAX
#  include <windows.h>
#endif

#include "ChildProcessJob.h"

#include <QDebug>

namespace fmd {

#ifdef _WIN32

ChildProcessJob::ChildProcessJob()
{
    HANDLE job = ::CreateJobObjectW(nullptr, nullptr);
    if (!job) {
        qWarning("ChildProcessJob: CreateJobObject 失败，子进程将不受作业对象保护");
        return;
    }

    JOBOBJECT_EXTENDED_LIMIT_INFORMATION limits{};
    limits.BasicLimitInformation.LimitFlags = JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE;

    if (!::SetInformationJobObject(job, JobObjectExtendedLimitInformation,
                                   &limits, sizeof(limits))) {
        qWarning("ChildProcessJob: SetInformationJobObject 失败，子进程将不受作业对象保护");
        ::CloseHandle(job);
        return;
    }

    m_job = job;
}

ChildProcessJob::~ChildProcessJob()
{
    if (m_job) {
        // 关闭句柄即触发 KILL_ON_JOB_CLOSE：作业内还活着的进程会被内核终止。
        // 这就是"父进程消失后子进程不会变孤儿"的关键一步。
        ::CloseHandle(static_cast<HANDLE>(m_job));
        m_job = nullptr;
    }
}

bool ChildProcessJob::assignProcess(qint64 processId)
{
    if (!m_job || processId <= 0)
        return false;

    HANDLE process = ::OpenProcess(PROCESS_SET_QUOTA | PROCESS_TERMINATE,
                                   FALSE, static_cast<DWORD>(processId));
    if (!process) {
        qWarning("ChildProcessJob: OpenProcess 失败 (pid=%lld)", static_cast<long long>(processId));
        return false;
    }

    const BOOL ok = ::AssignProcessToJobObject(static_cast<HANDLE>(m_job), process);
    ::CloseHandle(process);

    if (!ok) {
        // 常见于进程已经被别的作业独占（Windows 8 以前不支持嵌套作业）。
        // 不致命，但要知道保护没生效。
        qWarning("ChildProcessJob: AssignProcessToJobObject 失败 (pid=%lld, err=%lu)",
                 static_cast<long long>(processId), ::GetLastError());
        return false;
    }
    return true;
}

#else   // 非 Windows：空实现，保持接口一致

ChildProcessJob::ChildProcessJob() = default;
ChildProcessJob::~ChildProcessJob() = default;

bool ChildProcessJob::assignProcess(qint64)
{
    return false;
}

#endif

} // namespace fmd
