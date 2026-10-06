#pragma once

// 统计数字卡片：一个大号数字 + 一行小标签，用于突出关键指标。
// 比 "标签: 数字" 的普通表单行更容易一眼扫到，这是工业界面上位机的常见做法。

#include <QWidget>

class QLabel;

namespace fmd {

class StatCard : public QWidget
{
    Q_OBJECT
public:
    StatCard(const QString &caption, const QColor &accent, QWidget *parent = nullptr);

    void setValue(int value);
    void setValueText(const QString &text);
    void reset();

private:
    QLabel *m_value   = nullptr;
    QLabel *m_caption = nullptr;
    QString m_default = QStringLiteral("0");
};

} // namespace fmd
