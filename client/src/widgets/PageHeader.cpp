#include "PageHeader.h"

#include <QHBoxLayout>
#include <QLabel>
#include <QVBoxLayout>

namespace fmd {

PageHeader::PageHeader(const QString &title, const QString &subtitle, QWidget *parent)
    : QWidget(parent)
{
    auto *layout = new QVBoxLayout(this);
    layout->setContentsMargins(0, 0, 0, 8);
    layout->setSpacing(2);

    auto *titleLabel = new QLabel(title, this);
    titleLabel->setObjectName(QStringLiteral("pageTitle"));
    layout->addWidget(titleLabel);

    m_subtitle = new QLabel(subtitle, this);
    m_subtitle->setObjectName(QStringLiteral("pageSubtitle"));
    m_subtitle->setWordWrap(true);
    layout->addWidget(m_subtitle);
}

void PageHeader::setSubtitle(const QString &text)
{
    m_subtitle->setText(text);
}

} // namespace fmd
