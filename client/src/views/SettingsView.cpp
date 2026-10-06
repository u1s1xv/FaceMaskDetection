#include "SettingsView.h"

#include "BackendStatusView.h"

#include <QComboBox>
#include <QDoubleSpinBox>
#include <QFileDialog>
#include <QFormLayout>
#include <QGroupBox>
#include <QHBoxLayout>
#include <QLabel>
#include <QLineEdit>
#include <QPushButton>
#include <QScrollArea>
#include <QSettings>
#include <QSpinBox>
#include <QVBoxLayout>

namespace fmd {

namespace {
constexpr int kDefaultPort = 8756;
}

quint16 SettingsView::configuredPort()
{
    return quint16(QSettings().value(QStringLiteral("backend/port"), kDefaultPort).toUInt());
}

QString SettingsView::configuredPython()
{
    return QSettings().value(QStringLiteral("backend/python")).toString();
}

QString SettingsView::configuredScript()
{
    return QSettings().value(QStringLiteral("backend/script")).toString();
}

SettingsView::SettingsView(QWidget *parent)
    : QWidget(parent)
{
    buildUi();
    loadFromSettings();
}

void SettingsView::buildUi()
{
    auto *outer = new QVBoxLayout(this);
    outer->setContentsMargins(0, 0, 0, 0);

    auto *scroll = new QScrollArea(this);
    scroll->setWidgetResizable(true);
    scroll->setFrameShape(QFrame::NoFrame);

    auto *content = new QWidget(scroll);
    auto *root = new QVBoxLayout(content);
    root->setContentsMargins(8, 8, 8, 8);

    // ---------------- 连接配置 ----------------
    auto *connBox = new QGroupBox(QStringLiteral("推理服务连接"), content);
    auto *connForm = new QFormLayout(connBox);

    m_port = new QSpinBox(connBox);
    m_port->setRange(1024, 65535);
    connForm->addRow(QStringLiteral("服务端口"), m_port);

    auto *pythonRow = new QHBoxLayout;
    m_python = new QLineEdit(connBox);
    m_python->setPlaceholderText(QStringLiteral("留空则自动探测（环境变量 FMD_PYTHON > 配置 > conda med-yolo）"));
    auto *pythonBrowse = new QPushButton(QStringLiteral("…"), connBox);
    pythonBrowse->setFixedWidth(32);
    pythonRow->addWidget(m_python, 1);
    pythonRow->addWidget(pythonBrowse);
    connForm->addRow(QStringLiteral("Python 解释器"), pythonRow);

    auto *scriptRow = new QHBoxLayout;
    m_script = new QLineEdit(connBox);
    m_script->setPlaceholderText(QStringLiteral("留空则按 <应用目录>/../../server/app.py 探测"));
    auto *scriptBrowse = new QPushButton(QStringLiteral("…"), connBox);
    scriptBrowse->setFixedWidth(32);
    scriptRow->addWidget(m_script, 1);
    scriptRow->addWidget(scriptBrowse);
    connForm->addRow(QStringLiteral("服务脚本"), scriptRow);

    root->addWidget(connBox);

    // ---------------- 默认推理参数 ----------------
    auto *inferBox = new QGroupBox(QStringLiteral("默认推理参数"), content);
    auto *inferForm = new QFormLayout(inferBox);

    m_modelCombo = new QComboBox(inferBox);
    m_modelCombo->addItem(QStringLiteral("（自动选择 best）"), QString());
    inferForm->addRow(QStringLiteral("默认模型"), m_modelCombo);

    m_confSpin = new QDoubleSpinBox(inferBox);
    m_confSpin->setRange(0.01, 0.99);
    m_confSpin->setSingleStep(0.05);
    inferForm->addRow(QStringLiteral("置信度阈值"), m_confSpin);

    m_iouSpin = new QDoubleSpinBox(inferBox);
    m_iouSpin->setRange(0.01, 0.99);
    m_iouSpin->setSingleStep(0.05);
    inferForm->addRow(QStringLiteral("IOU 阈值"), m_iouSpin);

    m_imgszCombo = new QComboBox(inferBox);
    m_imgszCombo->addItem(QStringLiteral("320"), 320);
    m_imgszCombo->addItem(QStringLiteral("640"), 640);
    m_imgszCombo->addItem(QStringLiteral("1280"), 1280);
    inferForm->addRow(QStringLiteral("推理尺寸"), m_imgszCombo);

    root->addWidget(inferBox);

    // ---------------- 操作 ----------------
    auto *buttons = new QHBoxLayout;
    buttons->addStretch();
    auto *restartButton = new QPushButton(QStringLiteral("保存并重启服务"), content);
    m_saveButton = new QPushButton(QStringLiteral("保存"), content);
    m_saveButton->setDefault(true);
    buttons->addWidget(restartButton);
    buttons->addWidget(m_saveButton);
    root->addLayout(buttons);

    // ---------------- 诊断面板（嵌入复用）----------------
    m_statusView = new BackendStatusView(content);
    root->addWidget(m_statusView, 1);

    scroll->setWidget(content);
    outer->addWidget(scroll);

    connect(m_saveButton,   &QPushButton::clicked, this, &SettingsView::save);
    connect(restartButton,  &QPushButton::clicked, this, &SettingsView::saveAndRestart);
    connect(pythonBrowse,   &QPushButton::clicked, this, &SettingsView::browsePython);
    connect(scriptBrowse,   &QPushButton::clicked, this, &SettingsView::browseScript);
}

void SettingsView::loadFromSettings()
{
    QSettings settings;
    m_port->setValue(int(configuredPort()));
    m_python->setText(settings.value(QStringLiteral("backend/python")).toString());
    m_script->setText(settings.value(QStringLiteral("backend/script")).toString());

    m_confSpin->setValue(settings.value(QStringLiteral("infer/conf"), 0.25).toDouble());
    m_iouSpin->setValue (settings.value(QStringLiteral("infer/iou"),  0.45).toDouble());

    const int imgsz = settings.value(QStringLiteral("infer/imgsz"), 640).toInt();
    const int idx = m_imgszCombo->findData(imgsz);
    m_imgszCombo->setCurrentIndex(idx >= 0 ? idx : 1);

    const QString model = settings.value(QStringLiteral("infer/model")).toString();
    const int modelIdx = m_modelCombo->findData(model);
    if (modelIdx >= 0)
        m_modelCombo->setCurrentIndex(modelIdx);
}

void SettingsView::setModels(const QVector<ModelInfo> &models)
{
    const QString current = m_modelCombo->currentData().toString();
    m_modelCombo->clear();
    m_modelCombo->addItem(QStringLiteral("（自动选择 best）"), QString());
    for (const ModelInfo &m : models)
        m_modelCombo->addItem(m.name, m.name);

    const int idx = m_modelCombo->findData(current);
    if (idx >= 0)
        m_modelCombo->setCurrentIndex(idx);
}

void SettingsView::save()
{
    QSettings settings;
    settings.setValue(QStringLiteral("backend/port"),    m_port->value());
    settings.setValue(QStringLiteral("backend/python"),  m_python->text().trimmed());
    settings.setValue(QStringLiteral("backend/script"),  m_script->text().trimmed());
    settings.setValue(QStringLiteral("infer/model"),     m_modelCombo->currentData().toString());
    settings.setValue(QStringLiteral("infer/conf"),      m_confSpin->value());
    settings.setValue(QStringLiteral("infer/iou"),       m_iouSpin->value());
    settings.setValue(QStringLiteral("infer/imgsz"),     m_imgszCombo->currentData().toInt());
    settings.sync();

    m_statusView->appendLog(QStringLiteral("[设置] 已保存（端口 %1）").arg(m_port->value()));
    emit saved(false);
}

void SettingsView::saveAndRestart()
{
    save();
    emit saved(true);
}

void SettingsView::browsePython()
{
    const QString path = QFileDialog::getOpenFileName(
        this, QStringLiteral("选择 Python 解释器"), QString(),
        QStringLiteral("可执行文件 (*.exe);;所有文件 (*.*)"));
    if (!path.isEmpty())
        m_python->setText(path);
}

void SettingsView::browseScript()
{
    const QString path = QFileDialog::getOpenFileName(
        this, QStringLiteral("选择服务端脚本"), QString(),
        QStringLiteral("Python 脚本 (*.py);;所有文件 (*.*)"));
    if (!path.isEmpty())
        m_script->setText(path);
}

} // namespace fmd
