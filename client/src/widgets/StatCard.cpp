#include "StatCard.h"

#include <QLabel>
#include <QVBoxLayout>

namespace fmd {

StatCard::StatCard(const QString &caption, const QColor &accent, QWidget *parent)
    : QWidget(parent)
{
    setObjectName(QStringLiteral("statCard"));

    // QWidget 的子类默认不会绘制样式表里的 background/border，
    // 必须显式打开 WA_StyledBackground —— 否则卡片看着就是"没有卡片"，
    // 只是一堆浮在分组框上的数字。
    setAttribute(Qt::WA_StyledBackground, true);
    // 注意：控件级样式表会整体覆盖应用级样式表中的同名选择器，
    // 所以这里必须写完整规则，不能只写 border-left —— 否则卡片会丢掉背景和圆角，
    // 看起来就是一块扁平的白矩形。
    // 左侧色条表达类别语义：绿=合规、红=违规、黄=警告。
    setStyleSheet(QStringLiteral(
                      "QWidget#statCard {"
                      "  background: #ffffff;"
                      "  border: 1px solid #e1e4e8;"
                      "  border-left: 4px solid %1;"
                      "  border-radius: 8px;"
                      "}")
                      .arg(accent.name()));

    auto *layout = new QVBoxLayout(this);
    layout->setContentsMargins(12, 8, 12, 8);
    layout->setSpacing(0);

    m_value = new QLabel(m_default, this);
    m_value->setObjectName(QStringLiteral("statValue"));
    m_value->setAlignment(Qt::AlignCenter);
    m_value->setStyleSheet(QStringLiteral("color: %1;").arg(accent.name()));

    m_caption = new QLabel(caption, this);
    m_caption->setObjectName(QStringLiteral("statCaption"));
    m_caption->setAlignment(Qt::AlignCenter);

    layout->addWidget(m_value);
    layout->addWidget(m_caption);
}

void StatCard::setValue(int value)
{
    m_value->setText(QString::number(value));
}

void StatCard::setValueText(const QString &text)
{
    m_value->setText(text);
}

void StatCard::reset()
{
    m_value->setText(m_default);
}

} // namespace fmd
