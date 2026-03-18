#pragma once

#include <QObject>
#include <QWidget>
#include <QVBoxLayout>
#include <QHBoxLayout>
#include <QLabel>
#include <QLineEdit>
#include <QPushButton>
#include <QSlider>
#include <QFile>
#include <QJsonDocument>
#include <QJsonObject>
#include <QCheckBox>
#include "selfdrive/ui/sunnypilot/qt/widgets/controls.h"
#include "selfdrive/ui/sunnypilot/qt/widgets/scrollview.h"

class JetsonSettings : public QWidget {
  Q_OBJECT

public:
  explicit JetsonSettings(QWidget* parent = nullptr);
  void showEvent(QShowEvent* event) override;
  bool eventFilter(QObject* watched, QEvent* event) override;

signals:
  void backPress();

private slots:
  void saveConfig();
  void loadConfig();
  void onEnabledToggled(bool checked);

private:
  QVBoxLayout* main_layout;

  // UI elements
  QLabel* status_label;
  QLabel* ip_current_label;
  QLabel* img_port_label;
  QLabel* torque_port_label;
  QLabel* quality_label;
  QLabel* quality_value_label;

  QCheckBox* enabled_checkbox;
  QLineEdit* ip_input;
  QLineEdit* img_port_input;
  QLineEdit* torque_port_input;
  QSlider* quality_slider;
  QPushButton* save_btn;

  QString config_path;

  void setupHeader();
  void setupEnableSection();
  void setupConnectionSection();
  void setupQualitySection();
  void setupSaveButton();
  void updateStatusLabel();

  // JSON helpers
  QJsonObject loadJsonConfig();
  bool saveJsonConfig(const QJsonObject& config);

  // MQTT sync: publish config change to server/app
  void publishConfigViaMqtt();
};
