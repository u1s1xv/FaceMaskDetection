#pragma once

// 批量检测页：多选文件/文件夹 → 队列调度 → 进度与结果表。

#include <QHash>
#include <QVector>
#include <QWidget>

#include "core/Protocol.h"

class QComboBox;
class QDoubleSpinBox;
class QLabel;
class QListWidget;
class QProgressBar;
class QPushButton;
class QSpinBox;
class QSplitter;
class QTableWidget;
class QThreadPool;

namespace fmd {

class BackendClient;
class BatchController;
class ImageCanvas;

class BatchView : public QWidget
{
    Q_OBJECT
public:
    explicit BatchView(BackendClient *client, QWidget *parent = nullptr);

public slots:
    void setModels(const QVector<fmd::ModelInfo> &models);
    void startBatch();
    void cancelBatch();
    void clearList();
    // 脚本化 / 外部拖入：直接入队一批文件
    void enqueueFiles(const QStringList &paths);

    // 自动化验证用
    void selectRow(int row);
    bool previewHasImage() const;
    int  previewDetectionCount() const;

signals:
    void statusMessage(const QString &message);
    void requestOpenImage(const QString &filePath);
    void batchCompleted(int succeeded, int failed, bool cancelled);
    void jobFailedWithReason(const QString &filePath, const QString &error);

private slots:
    void addFiles();
    void addFolder();
    void onJobFinished(const QString &filePath, const fmd::DetectionResult &result);
    void onJobFailed(const QString &filePath, const QString &error);
    void onProgress(int finished, int succeeded, int failed, int total);
    void onBatchFinished(int succeeded, int failed, bool cancelled);
    void onLog(const QString &message);
    void openRowInDetectPage(int row, int column);
    void onSelectionChanged();
    void onPreviewLoaded(const QString &filePath, const QImage &image,
                         const QByteArray &rawBytes, qint64 elapsedMs);
    void onPreviewFailed(const QString &filePath, const QString &error);

private:
    enum Column { ColFile = 0, ColStatus, ColTotal, ColWith, ColWithout,
                  ColWrong, ColTime, ColumnCount };

    void buildUi();
    void appendRows(const QStringList &paths);
    int  rowOf(const QString &filePath) const;
    void setRowStatus(int row, const QString &text, const QColor &color);
    void updateButtons();

    // 每行对应的检测结果，用于选中该行时显示标注预览。
    // 批量请求为了省带宽不返回标注图（return_image=0），
    // 所以预览用"本地原图 + 服务端返回的检测框"在客户端重绘。
    struct RowResult {
        bool                    ok = false;
        int                     recordId = 0;
        QVector<fmd::Detection> detections;
    };

    void showPreviewForRow(int row);

    BackendClient   *m_client     = nullptr;
    BatchController *m_controller = nullptr;
    QThreadPool     *m_pool       = nullptr;
    QHash<QString, RowResult> m_results;   // key = 文件绝对路径
    QString m_previewPath;                 // 当前预览的文件，用于丢弃过期响应

    QTableWidget   *m_table   = nullptr;
    QComboBox      *m_modelCombo = nullptr;
    QDoubleSpinBox *m_confSpin   = nullptr;
    QDoubleSpinBox *m_iouSpin    = nullptr;
    QComboBox      *m_imgszCombo = nullptr;
    QSpinBox       *m_concurrencySpin = nullptr;
    QProgressBar   *m_progress = nullptr;
    QLabel         *m_summary  = nullptr;

    // 选中某行后的结果预览
    QSplitter   *m_splitter     = nullptr;
    ImageCanvas *m_preview      = nullptr;
    QLabel      *m_previewInfo  = nullptr;
    QListWidget *m_previewList  = nullptr;
    QPushButton    *m_startButton  = nullptr;
    QPushButton    *m_cancelButton = nullptr;
    QPushButton    *m_clearButton  = nullptr;
    QPushButton    *m_addFilesButton = nullptr;
    QPushButton    *m_addFolderButton = nullptr;
};

} // namespace fmd
