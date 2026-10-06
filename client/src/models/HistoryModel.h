#pragma once

// 检测历史的表格模型。
//
// 为什么不用 QTableWidget：历史记录会有成千上万条，QTableWidget 是"控件里塞数据"，
// 每条记录都对应一堆 QTableWidgetItem 对象，内存和刷新开销都不可接受。
// QAbstractTableModel 只暴露"视图按需取数"的接口，滚动到哪里才取哪里的数据，
// 而且排序、筛选可以交给 QSortFilterProxyModel 复用，不用自己重排控件。

#include <QAbstractTableModel>
#include <QVector>

#include "core/Protocol.h"

namespace fmd {

class HistoryModel : public QAbstractTableModel
{
    Q_OBJECT
public:
    enum Column {
        ColId = 0,
        ColFile,
        ColSize,
        ColTotal,
        ColWith,
        ColWithout,
        ColWrong,
        ColTime,
        ColQueue,
        ColCreated,
        ColumnCount
    };

    enum Role {
        RecordIdRole = Qt::UserRole + 1,
        FileNameRole,
        ViolationRole,      // 该记录是否存在未佩戴/佩戴不规范
    };

    explicit HistoryModel(QObject *parent = nullptr);

    int      rowCount(const QModelIndex &parent = QModelIndex()) const override;
    int      columnCount(const QModelIndex &parent = QModelIndex()) const override;
    QVariant data(const QModelIndex &index, int role = Qt::DisplayRole) const override;
    QVariant headerData(int section, Qt::Orientation orientation,
                        int role = Qt::DisplayRole) const override;

    void setRecords(const QVector<HistoryRecord> &records);
    void setTotal(int total);
    void removeRecordById(int id);
    void clear();

    const HistoryRecord *recordAt(int row) const;
    int totalCount() const { return m_total; }

private:
    QVector<HistoryRecord> m_records;
    int m_total = 0;
};

} // namespace fmd
