#include "selfdrive/ui/sunnypilot/qt/offroad/settings/sunnypilot/jetson_settings.h"
#include <QFileInfo>
#include <QDir>
#include <QSpacerItem>
#include <QFrame>
#include <QTimer>
#include <QDateTime>
#include "selfdrive/ui/sunnypilot/ui.h"
#include "selfdrive/ui/qt/util.h"
#include "system/hardware/hw.h"
#include "selfdrive/ui/qt/widgets/input.h"
#include "common/params.h"

JetsonSettings::JetsonSettings(QWidget* parent) : QWidget(parent) {
  main_layout = new QVBoxLayout(this);
  main_layout->setContentsMargins(50, 20, 50, 20);
  main_layout->setSpacing(15);

  // Back button
  PanelBackButton* back = new PanelBackButton();
  connect(back, &QPushButton::clicked, [=]() { emit backPress(); });
  main_layout->addWidget(back, 0, Qt::AlignLeft);

  // Find config_jetson.json path
  QString current_dir = QDir::currentPath();
  QStringList test_paths = {
    current_dir + "/sicuem/adripilot/config_jetson.json",
    "sicuem/adripilot/config_jetson.json",
    "../sicuem/adripilot/config_jetson.json",
    "../../sicuem/adripilot/config_jetson.json",
  };
  QStringList possible_bases = {
    Hardware::PC() ? QDir::homePath() + "/.comma/openpilot" : "/data/openpilot",
    "/data/openpilot"
  };
  for (const QString& base : possible_bases) {
    test_paths.append(base + "/sicuem/adripilot/config_jetson.json");
  }
  for (const QString& path : test_paths) {
    QFileInfo fi(path);
    if (fi.exists() && fi.isReadable()) {
      config_path = fi.absoluteFilePath();
      break;
    }
  }
  if (config_path.isEmpty()) {
    config_path = "/data/openpilot/sicuem/adripilot/config_jetson.json";
  }

  setupHeader();
  setupEnableSection();
  main_layout->addItem(new QSpacerItem(20, 20));
  setupConnectionSection();
  main_layout->addItem(new QSpacerItem(20, 20));
  setupQualitySection();
  main_layout->addItem(new QSpacerItem(20, 30));
  setupSaveButton();

  main_layout->addStretch();
}

void JetsonSettings::setupHeader() {
  // Title with NVIDIA Jetson green accent
  QLabel* title = new QLabel(tr("NVIDIA Jetson"));
  title->setStyleSheet("font-size: 70px; font-weight: 800; color: #76B900;");
  main_layout->addWidget(title);

  QLabel* subtitle = new QLabel(tr("Configuracion de envio de imagenes a la Jetson"));
  subtitle->setStyleSheet("font-size: 40px; color: #BDBDBD;");
  main_layout->addWidget(subtitle);

  // Status label
  status_label = new QLabel();
  status_label->setStyleSheet("font-size: 38px; font-weight: 600; padding: 15px; border-radius: 10px;");
  main_layout->addWidget(status_label);

  // Separator
  QFrame* line = new QFrame();
  line->setFrameShape(QFrame::HLine);
  line->setStyleSheet("background-color: #76B900; max-height: 2px; margin: 10px 0px;");
  main_layout->addWidget(line);
}

void JetsonSettings::setupEnableSection() {
  QLabel* section_label = new QLabel(tr("Estado"));
  section_label->setStyleSheet("font-size: 50px; font-weight: 600; color: #E0E0E0; margin-top: 10px;");
  main_layout->addWidget(section_label);

  // Enable checkbox row
  QWidget* enable_row = new QWidget();
  QHBoxLayout* rl = new QHBoxLayout(enable_row);
  rl->setContentsMargins(0, 0, 0, 0);

  enabled_checkbox = new QCheckBox(tr("Envio de imagenes a Jetson activo"));
  enabled_checkbox->setStyleSheet(R"(
    QCheckBox {
      font-size: 45px;
      color: white;
      spacing: 20px;
    }
    QCheckBox::indicator {
      width: 60px;
      height: 60px;
      border-radius: 10px;
      border: 3px solid #555555;
      background-color: #393939;
    }
    QCheckBox::indicator:checked {
      background-color: #76B900;
      border: 3px solid #76B900;
    }
  )");
  connect(enabled_checkbox, &QCheckBox::toggled, this, &JetsonSettings::onEnabledToggled);
  rl->addWidget(enabled_checkbox);
  main_layout->addWidget(enable_row);
}

void JetsonSettings::setupConnectionSection() {
  QLabel* section_label = new QLabel(tr("Conexion"));
  section_label->setStyleSheet("font-size: 50px; font-weight: 600; color: #E0E0E0;");
  main_layout->addWidget(section_label);

  // IP Address
  ip_current_label = new QLabel(tr("IP de la Jetson:"));
  ip_current_label->setStyleSheet("font-size: 40px; color: #aaaaaa; margin-top: 5px;");
  main_layout->addWidget(ip_current_label);

  ip_input = new QLineEdit();
  ip_input->setPlaceholderText("192.168.1.50");
  ip_input->setStyleSheet(R"(
    QLineEdit {
      font-size: 48px;
      font-family: monospace;
      padding: 20px;
      border-radius: 10px;
      background-color: #393939;
      color: white;
      border: 2px solid #555555;
    }
    QLineEdit:focus {
      border: 2px solid #76B900;
    }
  )");
  ip_input->setReadOnly(true);
  ip_input->installEventFilter(this);
  main_layout->addWidget(ip_input);

  // Ports in a row
  QWidget* ports_row = new QWidget();
  QHBoxLayout* pl = new QHBoxLayout(ports_row);
  pl->setContentsMargins(0, 10, 0, 0);
  pl->setSpacing(20);

  // Image port
  QWidget* img_port_widget = new QWidget();
  QVBoxLayout* ip_vl = new QVBoxLayout(img_port_widget);
  ip_vl->setContentsMargins(0, 0, 0, 0);
  img_port_label = new QLabel(tr("Puerto imagenes:"));
  img_port_label->setStyleSheet("font-size: 36px; color: #76B900;");
  ip_vl->addWidget(img_port_label);
  img_port_input = new QLineEdit();
  img_port_input->setPlaceholderText("5555");
  img_port_input->setStyleSheet(R"(
    QLineEdit {
      font-size: 44px;
      font-family: monospace;
      padding: 15px;
      border-radius: 10px;
      background-color: #393939;
      color: white;
      border: 2px solid #555555;
    }
    QLineEdit:focus { border: 2px solid #76B900; }
  )");
  img_port_input->setReadOnly(true);
  img_port_input->installEventFilter(this);
  ip_vl->addWidget(img_port_input);
  pl->addWidget(img_port_widget);

  // Torque port
  QWidget* torque_port_widget = new QWidget();
  QVBoxLayout* tp_vl = new QVBoxLayout(torque_port_widget);
  tp_vl->setContentsMargins(0, 0, 0, 0);
  torque_port_label = new QLabel(tr("Puerto torque:"));
  torque_port_label->setStyleSheet("font-size: 36px; color: #F59E0B;");
  tp_vl->addWidget(torque_port_label);
  torque_port_input = new QLineEdit();
  torque_port_input->setPlaceholderText("5556");
  torque_port_input->setStyleSheet(R"(
    QLineEdit {
      font-size: 44px;
      font-family: monospace;
      padding: 15px;
      border-radius: 10px;
      background-color: #393939;
      color: white;
      border: 2px solid #555555;
    }
    QLineEdit:focus { border: 2px solid #F59E0B; }
  )");
  torque_port_input->setReadOnly(true);
  torque_port_input->installEventFilter(this);
  tp_vl->addWidget(torque_port_input);
  pl->addWidget(torque_port_widget);

  main_layout->addWidget(ports_row);
}

void JetsonSettings::setupQualitySection() {
  QLabel* section_label = new QLabel(tr("Calidad de imagen"));
  section_label->setStyleSheet("font-size: 50px; font-weight: 600; color: #E0E0E0;");
  main_layout->addWidget(section_label);

  // Quality value + slider
  quality_value_label = new QLabel("80%");
  quality_value_label->setStyleSheet("font-size: 55px; font-weight: 800; color: #76B900;");
  quality_value_label->setAlignment(Qt::AlignCenter);
  main_layout->addWidget(quality_value_label);

  quality_slider = new QSlider(Qt::Horizontal);
  quality_slider->setRange(10, 100);
  quality_slider->setSingleStep(10);
  quality_slider->setPageStep(10);
  quality_slider->setValue(80);
  quality_slider->setStyleSheet(R"(
    QSlider::groove:horizontal {
      height: 12px;
      background: #393939;
      border-radius: 6px;
    }
    QSlider::handle:horizontal {
      background: #76B900;
      width: 40px;
      height: 40px;
      margin: -14px 0;
      border-radius: 20px;
    }
    QSlider::sub-page:horizontal {
      background: #76B900;
      border-radius: 6px;
    }
  )");
  connect(quality_slider, &QSlider::valueChanged, [=](int val) {
    quality_value_label->setText(QString("%1%").arg(val));
  });
  main_layout->addWidget(quality_slider);

  // Labels row
  QWidget* labels_row = new QWidget();
  QHBoxLayout* ll = new QHBoxLayout(labels_row);
  ll->setContentsMargins(0, 0, 0, 0);
  QLabel* low = new QLabel("10 - Baja");
  low->setStyleSheet("font-size: 30px; color: #888888;");
  QLabel* high = new QLabel("100 - Maxima");
  high->setStyleSheet("font-size: 30px; color: #888888;");
  high->setAlignment(Qt::AlignRight);
  ll->addWidget(low);
  ll->addStretch();
  ll->addWidget(high);
  main_layout->addWidget(labels_row);
}

void JetsonSettings::setupSaveButton() {
  save_btn = new QPushButton(tr("GUARDAR Y ENVIAR AL DISPOSITIVO"));
  save_btn->setStyleSheet(R"(
    QPushButton {
      font-size: 50px;
      font-weight: 700;
      padding: 30px;
      border-radius: 15px;
      background-color: #76B900;
      color: white;
      border: none;
    }
    QPushButton:pressed {
      background-color: #5A8F00;
    }
  )");
  connect(save_btn, &QPushButton::clicked, this, &JetsonSettings::saveConfig);
  main_layout->addWidget(save_btn);

  // Info text
  QLabel* info = new QLabel(tr("Los cambios se guardan localmente y se sincronizan con la app ADRIPILOT via MQTT."));
  info->setStyleSheet("font-size: 30px; color: #888888; margin-top: 10px;");
  info->setWordWrap(true);
  main_layout->addWidget(info);
}

void JetsonSettings::updateStatusLabel() {
  if (enabled_checkbox->isChecked()) {
    status_label->setText(tr("ACTIVA - Enviando a %1:%2").arg(ip_input->text()).arg(img_port_input->text()));
    status_label->setStyleSheet("font-size: 38px; font-weight: 600; padding: 15px; border-radius: 10px; background-color: rgba(118, 185, 0, 0.2); color: #76B900; border: 2px solid #76B900;");
  } else {
    status_label->setText(tr("INACTIVA - Envio desactivado"));
    status_label->setStyleSheet("font-size: 38px; font-weight: 600; padding: 15px; border-radius: 10px; background-color: rgba(239, 68, 68, 0.15); color: #EF4444; border: 2px solid #EF4444;");
  }
}

void JetsonSettings::onEnabledToggled(bool checked) {
  updateStatusLabel();
}

QJsonObject JetsonSettings::loadJsonConfig() {
  QFile file(config_path);
  if (!file.exists() || !file.open(QIODevice::ReadOnly | QIODevice::Text)) {
    return QJsonObject();
  }
  QByteArray data = file.readAll();
  file.close();
  QJsonDocument doc = QJsonDocument::fromJson(data);
  if (doc.isNull() || !doc.isObject()) return QJsonObject();
  return doc.object();
}

bool JetsonSettings::saveJsonConfig(const QJsonObject& config) {
  // Ensure directory exists
  QFileInfo fi(config_path);
  QDir dir = fi.dir();
  if (!dir.exists()) {
    dir.mkpath(".");
  }

  QFile file(config_path);
  if (!file.open(QIODevice::WriteOnly | QIODevice::Text | QIODevice::Truncate)) {
    return false;
  }
  QJsonDocument doc(config);
  file.write(doc.toJson(QJsonDocument::Indented));
  file.close();
  return true;
}

void JetsonSettings::loadConfig() {
  QJsonObject config = loadJsonConfig();

  bool enabled = config.value("jetson_enabled").toBool(false);
  QString ip = config.value("jetson_ip").toString("192.168.1.50");
  int img_port = config.value("jetson_img_port").toInt(5555);
  int torque_port = config.value("jetson_torque_port").toInt(5556);
  int quality = config.value("jpeg_quality").toInt(80);

  enabled_checkbox->setChecked(enabled);
  ip_input->setText(ip);
  img_port_input->setText(QString::number(img_port));
  torque_port_input->setText(QString::number(torque_port));
  quality_slider->setValue(quality);
  quality_value_label->setText(QString("%1%").arg(quality));

  updateStatusLabel();
}

void JetsonSettings::saveConfig() {
  QJsonObject config;
  config["jetson_enabled"] = enabled_checkbox->isChecked();
  config["jetson_ip"] = ip_input->text().trimmed();
  config["jetson_img_port"] = img_port_input->text().trimmed().toInt();
  config["jetson_torque_port"] = torque_port_input->text().trimmed().toInt();
  config["jpeg_quality"] = quality_slider->value();

  if (saveJsonConfig(config)) {
    updateStatusLabel();

    // Signal CameraSender to reload via Params
    Params params;
    params.putBool("JetsonConfigChanged", true);

    // Publish config via MQTT for app/server sync
    publishConfigViaMqtt();

    // Visual feedback
    save_btn->setText(tr("GUARDADO"));
    save_btn->setStyleSheet(R"(
      QPushButton {
        font-size: 50px;
        font-weight: 700;
        padding: 30px;
        border-radius: 15px;
        background-color: #22C55E;
        color: white;
        border: none;
      }
    )");
    QTimer::singleShot(2000, [=]() {
      save_btn->setText(tr("GUARDAR Y ENVIAR AL DISPOSITIVO"));
      save_btn->setStyleSheet(R"(
        QPushButton {
          font-size: 50px;
          font-weight: 700;
          padding: 30px;
          border-radius: 15px;
          background-color: #76B900;
          color: white;
          border: none;
        }
        QPushButton:pressed {
          background-color: #5A8F00;
        }
      )");
    });
  }
}

void JetsonSettings::publishConfigViaMqtt() {
  // Build JSON payload and publish via MQTT topic so server/app can sync
  // Uses Params to signal the MQTT sender to publish the jetson config
  Params params;
  QString dongle_id = QString::fromStdString(params.get("DongleId"));
  if (dongle_id.isEmpty()) return;

  QJsonObject payload;
  payload["dongle_id"] = dongle_id;
  payload["jetson_enabled"] = enabled_checkbox->isChecked();
  payload["jetson_ip"] = ip_input->text().trimmed();
  payload["jetson_img_port"] = img_port_input->text().trimmed().toInt();
  payload["jetson_torque_port"] = torque_port_input->text().trimmed().toInt();
  payload["jpeg_quality"] = quality_slider->value();
  payload["source"] = "comma_ui";
  payload["timestamp"] = QString::number(QDateTime::currentMSecsSinceEpoch());

  QJsonDocument doc(payload);
  params.put("JetsonConfigMqttPayload", doc.toJson(QJsonDocument::Compact).toStdString());
}

bool JetsonSettings::eventFilter(QObject* watched, QEvent* event) {
  if (event->type() == QEvent::MouseButtonPress) {
    QString title;
    QLineEdit* target = nullptr;

    if (watched == ip_input) {
      title = tr("IP de la Jetson");
      target = ip_input;
    } else if (watched == img_port_input) {
      title = tr("Puerto de imagenes");
      target = img_port_input;
    } else if (watched == torque_port_input) {
      title = tr("Puerto de torque");
      target = torque_port_input;
    }

    if (target) {
      const QString current = target->text();
      const QString new_text = InputDialog::getText(title, this, QString(), false, 1, current);
      if (!new_text.isEmpty()) {
        target->setText(new_text);
      }
      return true;
    }
  }
  return QWidget::eventFilter(watched, event);
}

void JetsonSettings::showEvent(QShowEvent* event) {
  loadConfig();
  QWidget::showEvent(event);
}
