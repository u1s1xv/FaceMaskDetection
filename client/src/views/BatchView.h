#pragma once

// 批量检测页：多选文件/文件夹 → 队列调度 → 进度与结果表。

#include <QVector>
#include <QWidget>

#include "core/Protocol.h"

class QComboBox;
class QDoubleSpinBox;
class QLabel;
class QProgressBar;
class QPushButton;
class QSpinBox;
class QTableWidget;

namespace fmd {

class BackendClient;
class BatchController;

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

private:
    enum Column { ColFile = 0, ColStatus, ColTotal, ColWith, ColWithout,
                  ColWrong, ColTime, ColumnCount };

    void buildUi();
    void appendRows(const QStringList &paths);
    int  rowOf(const QString &filePath) const;
    void setRowStatus(int row, const QString &text, const QColor &color);
    void updateButtons();

    BackendClient   *m_client     = nullptr;
    BatchController *m_controller = nullptr;

    QTableWidget   *m_table   = nullptr;
    QComboBox      *m_modelCombo = nullptr;
    QDoubleSpinBox *m_confSpin   = nullptr;
    QDoubleSpinBox *m_iouSpin    = nullptr;
    QComboBox      *m_imgszCombo = nullptr;
    QSpinBox       *m_concurrencySpin = nullptr;
    QProgressBar   *m_progress = nullptr;
    QLabel         *m_summary  = nullptr;
    QPushButton    *m_startButton  = nullptr;
    QPushButton    *m_cancelButton = nullptr;
    QPushButton    *m_clearButton  = nullptr;
    QPushButton    *m_addFilesButton = nullptr;
    QPushButton    *m_addFolderButton = nullptr;
};

} // namespace fmd
