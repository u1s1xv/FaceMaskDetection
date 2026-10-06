#pragma once

// 实时监控页：摄像头接入 + MJPEG 画面 + 实时推理状态。

#include <QVector>
#include <QWidget>

#include "core/Protocol.h"

class QCheckBox;
class QComboBox;
class QLabel;
class QLineEdit;
class QListWidget;
class QPushButton;
class QTimer;

namespace fmd {

class BackendClient;
class StatCard;
class VideoWidget;

class LiveView : public QWidget
{
    Q_OBJECT
public:
    explicit LiveView(BackendClient *client, QWidget *parent = nullptr);

    // 程序化打开一个视频源（供自动化验证/命令行使用）
    void openSource(const QString &source);

    // 供主窗口/自动化验证查询
    bool    isStreaming() const;
    QString currentCameraId() const { return m_currentCamId; }
    int     receivedFrames() const { return m_totalFrames; }
    bool    hasPicture() const;

signals:
    void statusMessage(const QString &text);

private slots:
    void refreshDevices();
    void openSelected();
    void openCustomSource();
    void closeCurrent();
    void onCamerasReceived(const QVector<fmd::CameraDevice> &devices,
                           const QVector<fmd::CameraInfo> &opened);
    void onCameraOpened(const QString &camId, const fmd::CameraInfo &info);
    void onCameraClosed(const QString &camId);
    void onStreamStarted(const QString &camId);
    void onStreamFrame(const QImage &frame);
    void onStreamStopped(const QString &camId, const QString &reason);
    void onRequestFailed(const QString &operation, const QString &error);
    void onMirrorToggled(bool checked);
    void onTick();

private:
    void buildUi();
    void updateButtons();
    void applyLiveStats(const fmd::CameraInfo &info);
    void setStatus(const QString &text);
    void resetStats();

    BackendClient *m_client = nullptr;

    QComboBox   *m_deviceCombo = nullptr;
    QPushButton *m_refreshButton = nullptr;
    QLineEdit   *m_sourceEdit  = nullptr;
    QCheckBox   *m_mirrorCheck = nullptr;
    QPushButton *m_openButton  = nullptr;
    QPushButton *m_closeButton = nullptr;
    QLabel      *m_statusLabel = nullptr;
    QLabel      *m_errorLabel  = nullptr;

    VideoWidget *m_video = nullptr;

    QLabel *m_resolution  = nullptr;
    QLabel *m_rxFps       = nullptr;
    QLabel *m_bitrate     = nullptr;
    QLabel *m_streamFrames = nullptr;
    QLabel *m_inferMs     = nullptr;
    QLabel *m_e2eMs       = nullptr;
    QLabel *m_jpegKb      = nullptr;

    StatCard    *m_cardWith    = nullptr;
    StatCard    *m_cardWithout = nullptr;
    StatCard    *m_cardWrong   = nullptr;
    QListWidget *m_detectionList = nullptr;

    QTimer *m_tick = nullptr;      // 1 秒一次：算接收帧率 + 轮询服务端状态

    QString m_currentCamId;
    int     m_framesThisSecond = 0;
    int     m_totalFrames      = 0;
    qint64  m_lastBytes        = 0;   // 上一秒的累计字节数，用于算码率
    bool    m_pendingClose     = false;
};

} // namespace fmd
