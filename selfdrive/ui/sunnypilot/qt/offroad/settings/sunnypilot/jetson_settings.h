#pragma once

#include <QObject>
#include <QWidget>
#include <QVBoxLayout>
#include <QHBoxLayout>
#include <QLabel>
#include <QLineEdit>
#include <QPushButton>
#include <QSlider>
#include <QTimer>
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
  void hideEvent(QHideEvent* event) override;
  bool eventFilter(QObject* watched, QEvent* event) override;

signals:
  void backPress();

private slots:
  void saveConfig();
  void loadConfig();
  void onEnabledToggled(bool checked);
  void onSteerModeChanged(int mode);
  void tryChangeSteerMode(int mode);
  // Refresco visual puro (sin escribir param ni publicar MQTT).
  // Se usa cuando el cambio viene de fuera (app via MQTT) para sincronizar los botones.
  void updateSteerModeVisual(int mode);

private:
  // Pregunta al usuario "¿curvature o torque?" tras pulsar COMMA+JETSON.
  // Devuelve "curvature", "torque" o "" si cancela. No escribe params ni publica MQTT.
  QString askObstacleApplyTarget();

private:
  QVBoxLayout* main_layout;

  // UI elements
  QLabel* status_label;
  QLabel* ip_current_label;
  QLabel* comma_ip_label;
  QLabel* img_port_label;
  QLabel* torque_port_label;
  QLabel* quality_label;
  QLabel* quality_value_label;

  QCheckBox* enabled_checkbox;
  QPushButton* btn_mode_model;
  QPushButton* btn_mode_comma_jetson;
  QPushButton* btn_mode_jetson;
  QPushButton* btn_mode_test;
  QLabel* torque_status_label;
  QLabel* obstacle_status_label;
  QLineEdit* ip_input;
  QLineEdit* comma_ip_input;
  QLineEdit* img_port_input;
  QLineEdit* torque_port_input;
  QSlider* quality_slider;
  QPushButton* save_btn;

  QString config_path;

  // Timer que sondea mientras la pantalla esta visible:
  //   - SteerTorqueMode (param): refresca los botones de torque.
  //   - config_jetson.json (archivo): refresca IP/puertos/quality si el
  //     archivo cambio por fuera (p.ej. la app envio jetson_config via MQTT
  //     y mqtt_comandos.py reescribio el JSON).
  // Todo visual; NO re-publica MQTT (evita eco).
  QTimer* steer_mode_sync_timer = nullptr;
  // Cache del ultimo modo que refleja la UI. Evita updates redundantes.
  int last_steer_mode_ui = -1;
  // mtime del config_jetson.json la ultima vez que refrescamos los campos.
  // Si cambia, recargamos los inputs sin pisar lo que el usuario este editando.
  qint64 last_config_mtime = 0;

  void setupHeader();
  void setupEnableSection();
  void setupTorqueControlSection();
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
