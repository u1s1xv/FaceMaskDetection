#pragma once

// 历史记录的筛选/排序代理。
//
// 关键点：筛选逻辑放在代理里，源模型完全不用知道"当前用户在搜什么"，
// 一个源模型可以同时挂多个代理给出不同视图（比如"全部"和"只看违规"两个表）。

#include <QSortFilterProxyModel>
#include <QString>

namespace fmd {

class HistoryProxy : public QSortFilterProxyModel
{
    Q_OBJECT
public:
    explicit HistoryProxy(QObject *parent = nullptr);

    void setKeyword(const QString &keyword);
    QString keyword() const { return m_keyword; }

    // 业务语义筛选：只看存在未佩戴/佩戴不规范的记录
    void setOnlyViolations(bool on);
    bool onlyViolations() const { return m_onlyViolations; }

protected:
    bool filterAcceptsRow(int sourceRow, const QModelIndex &sourceParent) const override;

private:
    QString m_keyword;
    bool    m_onlyViolations = false;
};

} // namespace fmd
