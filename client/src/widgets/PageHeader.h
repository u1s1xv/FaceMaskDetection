#pragma once

// 页面标题栏：统一的标题 + 说明 + 分隔线。
// 每个页面顶部都放一个，界面才有"层次"，否则各种控件堆在一起显得简陋。

#include <QWidget>

class QLabel;

namespace fmd {

class PageHeader : public QWidget
{
    Q_OBJECT
public:
    PageHeader(const QString &title, const QString &subtitle,
               QWidget *parent = nullptr);

    void setSubtitle(const QString &text);

private:
    QLabel *m_subtitle = nullptr;
};

} // namespace fmd
