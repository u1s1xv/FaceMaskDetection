#include "HistoryProxy.h"

#include "models/HistoryModel.h"

namespace fmd {

HistoryProxy::HistoryProxy(QObject *parent)
    : QSortFilterProxyModel(parent)
{
    setDynamicSortFilter(true);
    setSortCaseSensitivity(Qt::CaseInsensitive);
}

void HistoryProxy::setKeyword(const QString &keyword)
{
    const QString trimmed = keyword.trimmed();
    if (m_keyword == trimmed)
        return;
    m_keyword = trimmed;
    invalidateFilter();
}

void HistoryProxy::setOnlyViolations(bool on)
{
    if (m_onlyViolations == on)
        return;
    m_onlyViolations = on;
    invalidateFilter();
}

bool HistoryProxy::filterAcceptsRow(int sourceRow, const QModelIndex &sourceParent) const
{
    const QAbstractItemModel *source = sourceModel();
    if (!source)
        return true;

    const QModelIndex first = source->index(sourceRow, 0, sourceParent);

    if (m_onlyViolations && !first.data(HistoryModel::ViolationRole).toBool())
        return false;

    if (m_keyword.isEmpty())
        return true;

    // 跨列模糊匹配：文件名、时间、ID、模型都能搜到
    const int columns = source->columnCount(sourceParent);
    for (int col = 0; col < columns; ++col) {
        const QString text = source->index(sourceRow, col, sourceParent)
                                 .data(Qt::DisplayRole).toString();
        if (text.contains(m_keyword, Qt::CaseInsensitive))
            return true;
    }
    return false;
}

} // namespace fmd
