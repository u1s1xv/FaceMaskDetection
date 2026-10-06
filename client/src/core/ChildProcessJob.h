#pragma once

// 子进程生命周期保护（Windows 作业对象）。
//
// 解决的问题：QProcess 只在"客户端正常退出"时才会走 closeEvent 去停子进程。
// 如果客户端被任务管理器强杀、或自己崩溃，Python 后端就会变成孤儿进程一直挂着，
// 占着 GPU 显存和端口，下次启动还可能因端口被占而失败。实测中确实出现过。
//
// 作业对象是 Windows 提供的机制：把子进程加入作业并设置
// JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE 后，作业句柄一旦关闭（进程终止时由内核关闭），
// 作业内的所有进程都会被一并终止 —— 正常退出、崩溃、被强杀都覆盖。
//
// 非 Windows 平台上这是一个空实现，接口保持一致。

#include <QtGlobal>

namespace fmd {

class ChildProcessJob
{
public:
    ChildProcessJob();
    ~ChildProcessJob();

    ChildProcessJob(const ChildProcessJob &) = delete;
    ChildProcessJob &operator=(const ChildProcessJob &) = delete;

    // 把指定 PID 加入作业。
    // 返回 false 表示创建/加入失败 —— 不致命，只是失去这层保护，调用方不应中断流程。
    bool assignProcess(qint64 processId);

    bool isValid() const { return m_job != nullptr; }

private:
    void *m_job = nullptr;   // HANDLE；放 void* 是为了不在头文件里引入 windows.h
};

} // namespace fmd
