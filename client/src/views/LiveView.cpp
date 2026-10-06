#include "LiveView.h"

#include "VideoWidget.h"
#include "core/BackendClient.h"
#include "widgets/PageHeader.h"
#include "widgets/StatCard.h"

#include <QColor>
#include <QCheckBox>
#include <QComboBox>
#include <QCoreApplication>
#include <QFileInfo>
#include <QFormLayout>
#include <QGroupBox>
#include <QHBoxLayout>
#include <QLabel>
#include <QLineEdit>
#include <QListWidget>
#include <QPushButton>
#include <QSplitter>
#include <QTimer>
#include <QVBoxLayout>

namespace fmd {

namespace {

// 类别名 -> 中文。服务端画在画面上的标签是 ASCII 的类别名
// （cv2 的 putText 不支持中文），客户端这边用系统字体，可以显示中文。
QString classNameZh(const QString &name)
{
    if (name == QLatin1String("with_mask"))
        return QCoreApplication::translate("LiveView", "正确佩戴");
    if (name == QLatin1String("without_mask"))
        return QCoreApplication::translate("LiveView", "未佩戴");
    if (name == QLatin1String("mask_weared_incorrect"))
        return QCoreApplication::translate("LiveView", "佩戴不规范");
    return name;
}

} // namespace

LiveView::LiveView(BackendClient *client, QWidget *parent)
    : QWidget(parent)
    , m_client(client)
{
    buildUi();

    connect(m_client, &BackendClient::camerasReceived,   this, &LiveView::onCamerasReceived);
    connect(m_client, &BackendClient::cameraOpened,      this, &LiveView::onCameraOpened);
    connect(m_client, &BackendClient::cameraClosed,      this, &LiveView::onCameraClosed);
    connect(m_client, &BackendClient::streamStarted,     this, &LiveView::onStreamStarted);
    connect(m_client, &BackendClient::streamFrame,       this, &LiveView::onStreamFrame);
    connect(m_client, &BackendClient::streamStopped,     this, &LiveView::onStreamStopped);
    connect(m_client, &BackendClient::requestFailed,     this, &LiveView::onRequestFailed);

    m_tick = new QTimer(this);
    m_tick->setInterval(1000);
    connect(m_tick, &QTimer::timeout, this, &LiveView::onTick);
    m_tick->start();

    updateButtons();
}

void LiveView::buildUi()
{
    auto *outer = new QVBoxLayout(this);
    outer->setContentsMargins(12, 12, 12, 12);
    outer->setSpacing(10);

    outer->addWidget(new PageHeader(
        tr("实时监控"),
        tr("接入 USB 摄像头、RTSP 网络流或视频文件，服务端边采集边推理，画面以 MJPEG 推送到这里。\n"
           "检测框由服务端绘制在画面上 —— 这样框和画面永远同步，不会出现\"框在画面外飘\"。")));

    // ---------------- 工具栏 ----------------
    auto *toolbar = new QHBoxLayout;
    toolbar->setSpacing(8);

    toolbar->addWidget(new QLabel(tr("摄像头"), this));
    m_deviceCombo = new QComboBox(this);
    m_deviceCombo->setMinimumWidth(200);
    toolbar->addWidget(m_deviceCombo);

    m_refreshButton = new QPushButton(tr("刷新"), this);
    toolbar->addWidget(m_refreshButton);

    toolbar->addSpacing(12);
    toolbar->addWidget(new QLabel(tr("或指定源"), this));
    m_sourceEdit = new QLineEdit(this);
    m_sourceEdit->setPlaceholderText(tr("视频文件路径 / rtsp://…"));
    m_sourceEdit->setClearButtonEnabled(true);
    m_sourceEdit->setMinimumWidth(260);
    toolbar->addWidget(m_sourceEdit, 1);

    m_openButton = new QPushButton(tr("打开"), this);
    m_openButton->setObjectName(QStringLiteral("primaryButton"));
    toolbar->addWidget(m_openButton);

    m_closeButton = new QPushButton(tr("关闭"), this);
    toolbar->addWidget(m_closeButton);

    toolbar->addSpacing(12);
    m_mirrorCheck = new QCheckBox(tr("镜像画面"), this);
    m_mirrorCheck->setChecked(true);          // 与服务端默认值一致
    m_mirrorCheck->setToolTip(
        tr("桌面应用的惯例是镜像（像照镜子），视频会议的本地预览也是如此。\n"
           "工业监控场景建议关掉 —— 画面左右与现场一致，指挥\"往左一点\"才不会说反。\n"
           "镜像由服务端绘制，不会影响检测结果。"));
    m_mirrorCheck->setEnabled(false);         // 没有视频源时不可用
    toolbar->addWidget(m_mirrorCheck);

    outer->addLayout(toolbar);

    m_statusLabel = new QLabel(tr("尚未接入视频源"), this);
    m_statusLabel->setObjectName(QStringLiteral("pageSubtitle"));
    outer->addWidget(m_statusLabel);

    m_errorLabel = new QLabel(this);
    m_errorLabel->setWordWrap(true);
    m_errorLabel->setStyleSheet(QStringLiteral("color: #c62828;"));
    m_errorLabel->setVisible(false);
    outer->addWidget(m_errorLabel);

    // ---------------- 画面 + 状态 ----------------
    auto *splitter = new QSplitter(Qt::Horizontal, this);

    m_video = new VideoWidget(splitter);
    splitter->addWidget(m_video);

    auto *side = new QWidget(splitter);
    side->setMinimumWidth(300);
    side->setMaximumWidth(420);
    auto *sideLayout = new QVBoxLayout(side);
    sideLayout->setContentsMargins(0, 0, 0, 0);
    sideLayout->setSpacing(8);

    // 画面状态
    auto *videoBox = new QGroupBox(tr("画面"), side);
    auto *videoForm = new QFormLayout(videoBox);
    m_resolution   = new QLabel(QStringLiteral("—"), videoBox);
    m_rxFps        = new QLabel(QStringLiteral("—"), videoBox);
    m_bitrate      = new QLabel(QStringLiteral("—"), videoBox);
    m_streamFrames = new QLabel(QStringLiteral("—"), videoBox);
    videoForm->addRow(tr("分辨率"),   m_resolution);
    videoForm->addRow(tr("接收帧率"), m_rxFps);
    videoForm->addRow(tr("码率"),     m_bitrate);
    videoForm->addRow(tr("累计帧数"), m_streamFrames);
    sideLayout->addWidget(videoBox);

    // 推理状态
    auto *inferBox = new QGroupBox(tr("推理"), side);
    auto *inferForm = new QFormLayout(inferBox);
    m_inferMs = new QLabel(QStringLiteral("—"), inferBox);
    m_e2eMs   = new QLabel(QStringLiteral("—"), inferBox);
    m_jpegKb  = new QLabel(QStringLiteral("—"), inferBox);
    inferForm->addRow(tr("推理耗时"),   m_inferMs);
    inferForm->addRow(tr("端到端延迟"), m_e2eMs);
    inferForm->addRow(tr("单帧大小"),   m_jpegKb);
    sideLayout->addWidget(inferBox);

    // 当前目标
    auto *countBox = new QGroupBox(tr("当前画面目标"), side);
    auto *countLayout = new QVBoxLayout(countBox);
    auto *cardRow = new QHBoxLayout;
    cardRow->setSpacing(8);
    m_cardWith    = new StatCard(tr("正确佩戴"),  QColor(26, 127, 55),  countBox);
    m_cardWithout = new StatCard(tr("未佩戴"),    QColor(198, 40, 40),  countBox);
    m_cardWrong   = new StatCard(tr("佩戴不规范"), QColor(184, 134, 11), countBox);
    cardRow->addWidget(m_cardWith);
    cardRow->addWidget(m_cardWithout);
    cardRow->addWidget(m_cardWrong);
    countLayout->addLayout(cardRow);

    m_detectionList = new QListWidget(countBox);
    m_detectionList->setMaximumHeight(140);
    countLayout->addWidget(m_detectionList);
    sideLayout->addWidget(countBox, 1);

    splitter->addWidget(side);
    splitter->setStretchFactor(0, 1);
    splitter->setStretchFactor(1, 0);
    splitter->setCollapsible(0, false);
    outer->addWidget(splitter, 1);

    // ---------------- 连接 ----------------
    connect(m_refreshButton, &QPushButton::clicked, this, &LiveView::refreshDevices);
    connect(m_openButton,    &QPushButton::clicked, this, &LiveView::openSelected);
    connect(m_closeButton,   &QPushButton::clicked, this, &LiveView::closeCurrent);
    connect(m_sourceEdit, &QLineEdit::returnPressed, this, &LiveView::openCustomSource);
    connect(m_mirrorCheck, &QCheckBox::toggled, this, &LiveView::onMirrorToggled);
}

// ------------------------------------------------------------ 操作

void LiveView::refreshDevices()
{
    m_client->fetchCameras();
}

void LiveView::openSelected()
{
    // 输入框里有内容就优先用它（用户显式指定了源）
    if (!m_sourceEdit->text().trimmed().isEmpty()) {
        openCustomSource();
        return;
    }
    const int index = m_deviceCombo->currentData().toInt();
    if (m_deviceCombo->currentData().isNull()) {
        setStatus(tr("没有可用的摄像头。可以改为在右侧填入视频文件路径或 RTSP 地址。"));
        return;
    }
    m_errorLabel->setVisible(false);
    setStatus(tr("正在打开摄像头 %1 …").arg(index));
    m_client->openCamera(QString::number(index), m_deviceCombo->currentText());
}

void LiveView::openCustomSource()
{
    const QString source = m_sourceEdit->text().trimmed();
    if (source.isEmpty())
        return;
    m_errorLabel->setVisible(false);
    setStatus(tr("正在打开 %1 …").arg(source));
    m_client->openCamera(source, QFileInfo(source).fileName());
}

void LiveView::openSource(const QString &source)
{
    m_sourceEdit->setText(source);
    openCustomSource();
}

void LiveView::closeCurrent()
{
    if (m_currentCamId.isEmpty()) {
        m_client->stopStream();
        return;
    }
    m_pendingClose = true;
    m_client->closeCamera(m_currentCamId);
}

// ------------------------------------------------------------ 服务端回调

void LiveView::onCamerasReceived(const QVector<CameraDevice> &devices,
                                 const QVector<CameraInfo> &opened)
{
    // 设备下拉：尽量保持当前选择，避免每秒刷新时"跳回去"
    const QVariant previous = m_deviceCombo->currentData();
    m_deviceCombo->blockSignals(true);
    m_deviceCombo->clear();
    for (const CameraDevice &d : devices) {
        m_deviceCombo->addItem(tr("摄像头 %1（%2 %3x%4）")
                                   .arg(d.index).arg(d.backend)
                                   .arg(d.width).arg(d.height),
                               d.index);
    }
    if (m_deviceCombo->count() == 0)
        m_deviceCombo->addItem(tr("（未检测到摄像头）"), QVariant());
    else if (!previous.isNull()) {
        const int idx = m_deviceCombo->findData(previous);
        if (idx >= 0)
            m_deviceCombo->setCurrentIndex(idx);
    }
    m_deviceCombo->blockSignals(false);

    // 服务端状态：如果当前推的那一路还在，就用它刷新统计
    for (const CameraInfo &info : opened) {
        if (info.id == m_currentCamId) {
            applyLiveStats(info);
            break;
        }
    }

    updateButtons();
}

void LiveView::onCameraOpened(const QString &camId, const CameraInfo &info)
{
    m_currentCamId = camId;
    m_errorLabel->setVisible(false);
    setStatus(tr("已接入 %1（%2，后端 %3）")
                  .arg(info.name.isEmpty() ? info.source : info.name)
                  .arg(info.kind).arg(info.backend));
    emit statusMessage(tr("视频源 %1 已接入").arg(camId));
    m_client->startStream(camId);          // 打开成功才开始拉流
    updateButtons();
}

void LiveView::onCameraClosed(const QString &camId)
{
    m_pendingClose = false;
    if (camId != m_currentCamId)
        return;
    m_currentCamId.clear();
    m_video->clearFrame();
    resetStats();
    setStatus(tr("视频源已关闭"));
    emit statusMessage(tr("视频源 %1 已关闭").arg(camId));
    updateButtons();
}

void LiveView::onStreamStarted(const QString &camId)
{
    m_totalFrames = 0;
    m_framesThisSecond = 0;
    m_lastBytes = 0;
    setStatus(tr("正在接收 %1 的画面…").arg(camId));
    updateButtons();
}

void LiveView::onStreamFrame(const QImage &frame)
{
    m_video->setFrame(frame);
    ++m_framesThisSecond;
    ++m_totalFrames;
    if (m_totalFrames == 1)
        m_resolution->setText(QStringLiteral("%1 × %2")
                                  .arg(frame.width()).arg(frame.height()));
}

void LiveView::onStreamStopped(const QString &camId, const QString &reason)
{
    Q_UNUSED(camId)
    // 主动关闭时 onCameraClosed 会给出更准确的状态，这里不覆盖
    if (!m_pendingClose && !m_currentCamId.isEmpty()) {
        setStatus(tr("画面已停止：%1").arg(reason));
        m_errorLabel->setText(tr("推流中断：%1").arg(reason));
        m_errorLabel->setVisible(true);
    }
    updateButtons();
}

void LiveView::onRequestFailed(const QString &operation, const QString &error)
{
    // 只关心摄像头相关的失败；检测/历史的失败由各自页面展示
    if (!operation.startsWith(QLatin1String("camera")))
        return;
    m_errorLabel->setText(tr("操作失败：%1").arg(error));
    m_errorLabel->setVisible(true);
    setStatus(tr("打开视频源失败"));
    updateButtons();
}

void LiveView::onMirrorToggled(bool checked)
{
    if (m_currentCamId.isEmpty())
        return;
    m_client->setCameraMirror(m_currentCamId, checked);
    setStatus(checked ? tr("画面已镜像") : tr("画面已取消镜像"));
}

void LiveView::onTick()
{
    if (m_client->isStreaming()) {
        m_rxFps->setText(tr("%1 FPS").arg(m_framesThisSecond));
        m_streamFrames->setText(QString::number(m_totalFrames));

        const qint64 total = m_client->streamBytes();
        const qint64 delta = total - m_lastBytes;
        m_lastBytes = total;
        m_bitrate->setText(tr("%1 KB/s").arg(delta / 1024));

        // 服务端状态每秒拉一次。用同一个端点，避免多套状态不同步。
        m_client->fetchCameras();
    }
    m_framesThisSecond = 0;
}

// ------------------------------------------------------------ 状态

void LiveView::applyLiveStats(const CameraInfo &info)
{
    // 用服务端的真实状态回填复选框。断开信号避免"回填 -> 触发 toggled -> 又发请求"
    // 这种自激循环。
    if (m_mirrorCheck->isChecked() != info.live.mirror) {
        const QSignalBlocker blocker(m_mirrorCheck);
        m_mirrorCheck->setChecked(info.live.mirror);
    }

    m_inferMs->setText(tr("%1 ms").arg(info.live.inferMs, 0, 'f', 1));
    m_e2eMs->setText(tr("%1 ms").arg(info.live.e2eMs, 0, 'f', 1));
    m_jpegKb->setText(tr("%1 KB").arg(info.live.jpegKb, 0, 'f', 1));

    m_cardWith->setValue(info.live.counts.value(QStringLiteral("with_mask")));
    m_cardWithout->setValue(info.live.counts.value(QStringLiteral("without_mask")));
    m_cardWrong->setValue(info.live.counts.value(QStringLiteral("mask_weared_incorrect")));

    m_detectionList->clear();
    for (const Detection &d : info.live.detections) {
        m_detectionList->addItem(tr("%1  置信度 %2  框(%3,%4)-(%5,%6)")
                                     .arg(classNameZh(d.className))
                                     .arg(d.confidence, 0, 'f', 2)
                                     .arg(d.x1, 0, 'f', 0).arg(d.y1, 0, 'f', 0)
                                     .arg(d.x2, 0, 'f', 0).arg(d.y2, 0, 'f', 0));
    }
    if (info.live.detections.isEmpty())
        m_detectionList->addItem(tr("（当前画面没有检测到目标）"));
}

void LiveView::resetStats()
{
    for (QLabel *label : { m_resolution, m_rxFps, m_bitrate, m_streamFrames,
                           m_inferMs, m_e2eMs, m_jpegKb }) {
        label->setText(QStringLiteral("—"));
    }
    m_cardWith->reset();
    m_cardWithout->reset();
    m_cardWrong->reset();
    m_detectionList->clear();
    m_lastBytes = 0;
}

void LiveView::setStatus(const QString &text)
{
    m_statusLabel->setText(text);
}

void LiveView::updateButtons()
{
    const bool streaming = m_client->isStreaming();
    m_openButton->setEnabled(!streaming);
    m_closeButton->setEnabled(streaming || !m_currentCamId.isEmpty());
    m_mirrorCheck->setEnabled(streaming);
    m_sourceEdit->setEnabled(!streaming);
    m_deviceCombo->setEnabled(!streaming);
}

bool LiveView::isStreaming() const
{
    return m_client->isStreaming();
}

bool LiveView::hasPicture() const
{
    return m_video != nullptr && m_video->hasFrame();
}

} // namespace fmd
