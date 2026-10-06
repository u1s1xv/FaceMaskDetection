#pragma once

// 模型管理页：列出可用权重，展示体积/时间，并可设为默认模型。

#include <QVector>
#include <QWidget>

#include "core/Protocol.h"

class QLabel;
class QPushButton;
class QTableWidget;

namespace fmd {

class ModelsView : public QWidget
{
    Q_OBJECT
public:
    explicit ModelsView(QWidget *parent = nullptr);

    int modelCount() const;

public slots:
    void setModels(const QVector<fmd::ModelInfo> &models);

signals:
    void statusMessage(const QString &message);
    void defaultModelChanged(const QString &modelName);
    void refreshRequested();

private slots:
    void setSelectedAsDefault();
    void onSelectionChanged();

private:
    void buildUi();
    void setModelsFromCurrentTable();
    int  rowOfModel(const QString &name) const;

    QTableWidget *m_table = nullptr;
    QLabel       *m_summary = nullptr;
    QLabel       *m_currentDefault = nullptr;
    QPushButton  *m_setDefaultButton = nullptr;
    QString       m_defaultModel;
};

} // namespace fmd
