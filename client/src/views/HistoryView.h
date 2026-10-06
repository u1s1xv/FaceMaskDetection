#pragma once

// 历史记录页：QTableView + 自定义模型 + 代理筛选 + 详情面板。

#include <QWidget>

#include "core/Protocol.h"

class QCheckBox;
class QLabel;
class QLineEdit;
class QPushButton;
class QTableView;
class QTimer;

namespace fmd {

class BackendClient;
class HistoryModel;
class HistoryProxy;
class ImageCanvas;

class HistoryView : public QWidget
{
    Q_OBJECT
public:
    explicit HistoryView(BackendClient *client, QWidget *parent = nullptr);

    // 当前代理过滤后可见的行数 / 源模型总行数
    int visibleRowCount() const;
    int loadedRowCount() const;

    // 详情面板状态（自动化验证用）
    bool detailHasImage() const;
    int  detailDetectionCount() const;
    void selectFirstRow();

public slots:
    void refresh();

signals:
    void statusMessage(const QString &message);

private slots:
    void onHistoryReceived(int total, const QVector<fmd::HistoryRecord> &items);
    void onRecordReceived(const fmd::HistoryRecord &record);
    void onImageReceived(int id, const QByteArray &data);
    void onRecordDeleted(int id);
    void onSelectionChanged();
    void deleteSelected();
    void onRequestFailed(const QString &operation, const QString &error);

private:
    void buildUi();
    void applyFilter();
    int  currentRecordId() const;

    BackendClient *m_client = nullptr;
    HistoryModel  *m_model  = nullptr;
    HistoryProxy  *m_proxy  = nullptr;

    QTableView  *m_table   = nullptr;
    QLineEdit   *m_search  = nullptr;
    QCheckBox   *m_onlyViolations = nullptr;
    QPushButton *m_refreshButton  = nullptr;
    QPushButton *m_deleteButton   = nullptr;
    QLabel      *m_summary        = nullptr;

    ImageCanvas *m_canvas   = nullptr;
    QLabel      *m_detail   = nullptr;
    int          m_loadedImageId = -1;

    // 详情接口返回的检测框。
    // 注意：列表接口 /history 只返回摘要，不含 detections，
    // 所以画框必须用这里存的详情数据，不能用模型里的记录。
    QVector<fmd::Detection> m_currentDetections;
};

} // namespace fmd
