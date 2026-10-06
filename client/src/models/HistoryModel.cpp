#include "HistoryModel.h"

#include <QBrush>
#include <QColor>
#include <QFont>

namespace fmd {

namespace {
const QColor kOkColor      (26, 127, 55);
const QColor kWarnColor    (184, 134, 11);
const QColor kDangerColor  (180, 35, 24);
const QColor kMutedColor   (120, 120, 120);
}

HistoryModel::HistoryModel(QObject *parent)
    : QAbstractTableModel(parent)
{
}

int HistoryModel::rowCount(const QModelIndex &parent) const
{
    return parent.isValid() ? 0 : m_records.size();
}

int HistoryModel::columnCount(const QModelIndex &parent) const
{
    return parent.isValid() ? 0 : ColumnCount;
}

const HistoryRecord *HistoryModel::recordAt(int row) const
{
    if (row < 0 || row >= m_records.size())
        return nullptr;
    return &m_records.at(row);
}

QVariant HistoryModel::data(const QModelIndex &index, int role) const
{
    if (!index.isValid() || index.row() < 0 || index.row() >= m_records.size())
        return QVariant();

    const HistoryRecord &r = m_records.at(index.row());
    const int column = index.column();

    switch (role) {
    case Qt::DisplayRole:
        switch (column) {
        case ColId:      return r.id;
        case ColFile:    return r.fileName;
        case ColSize:    return QStringLiteral("%1×%2").arg(r.imageWidth).arg(r.imageHeight);
        case ColTotal:   return r.totalDetections;
        case ColWith:    return r.withMask;
        case ColWithout: return r.withoutMask;
        case ColWrong:   return r.incorrectMask;
        case ColTime:    return QStringLiteral("%1").arg(r.processingTime * 1000.0, 0, 'f', 0);
        case ColQueue:   return QStringLiteral("%1").arg(r.queueWait * 1000.0, 0, 'f', 0);
        case ColCreated: return r.createdAt;
        default:         return QVariant();
        }

    case Qt::TextAlignmentRole:
        if (column == ColFile || column == ColCreated)
            return int(Qt::AlignLeft | Qt::AlignVCenter);
        return int(Qt::AlignCenter);

    case Qt::ForegroundRole:
        // 用颜色把"有问题"的行直接标出来，不用用户自己逐列看数字
        if (column == ColWithout && r.withoutMask > 0)
            return QBrush(kDangerColor);
        if (column == ColWrong && r.incorrectMask > 0)
            return QBrush(kWarnColor);
        if (column == ColWith && r.withMask > 0)
            return QBrush(kOkColor);
        if (column == ColQueue && r.queueWait > 0.05)
            return QBrush(kWarnColor);      // 排队明显，说明并发压过头了
        if (column == ColId || column == ColSize)
            return QBrush(kMutedColor);
        return QVariant();

    case Qt::FontRole:
        if (column == ColTotal) {
            QFont f;
            f.setBold(true);
            return f;
        }
        return QVariant();

    case Qt::ToolTipRole:
        return tr("记录 #%1\n文件：%2\n模型：%3\n图像：%4×%5\n耗时：%6 ms\n排队：%7 ms")
            .arg(r.id).arg(r.fileName).arg(r.modelName)
            .arg(r.imageWidth).arg(r.imageHeight)
            .arg(r.processingTime * 1000.0, 0, 'f', 0)
            .arg(r.queueWait * 1000.0, 0, 'f', 0);

    case RecordIdRole:   return r.id;
    case FileNameRole:   return r.fileName;
    case ViolationRole:  return (r.withoutMask + r.incorrectMask) > 0;
    default:             return QVariant();
    }
}

QVariant HistoryModel::headerData(int section, Qt::Orientation orientation, int role) const
{
    if (role != Qt::DisplayRole)
        return QVariant();

    if (orientation == Qt::Vertical)
        return section + 1;

    switch (section) {
    case ColId:      return QStringLiteral("ID");
    case ColFile:    return tr("文件名");
    case ColSize:    return tr("尺寸");
    case ColTotal:   return tr("目标数");
    case ColWith:    return tr("正确");
    case ColWithout: return tr("未佩戴");
    case ColWrong:   return tr("不规范");
    case ColTime:    return tr("推理 ms");
    case ColQueue:   return tr("排队 ms");
    case ColCreated: return tr("时间");
    default:         return QVariant();
    }
}

void HistoryModel::setRecords(const QVector<HistoryRecord> &records)
{
    beginResetModel();
    m_records = records;
    endResetModel();
}

void HistoryModel::setTotal(int total)
{
    m_total = total;
}

void HistoryModel::removeRecordById(int id)
{
    for (int row = 0; row < m_records.size(); ++row) {
        if (m_records.at(row).id != id)
            continue;
        beginRemoveRows(QModelIndex(), row, row);
        m_records.remove(row);
        endRemoveRows();
        if (m_total > 0)
            --m_total;
        return;
    }
}

void HistoryModel::clear()
{
    beginResetModel();
    m_records.clear();
    m_total = 0;
    endResetModel();
}

} // namespace fmd
