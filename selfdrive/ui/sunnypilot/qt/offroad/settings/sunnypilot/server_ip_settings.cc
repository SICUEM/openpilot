/**
The MIT License

Copyright (c) 2021-, Haibin Wen, sunnypilot, and a number of other contributors.

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.

Last updated: December 2024
***/

#include "selfdrive/ui/sunnypilot/qt/offroad/settings/sunnypilot/server_ip_settings.h"
#include <QFileInfo>
#include <QDir>
#include <QSpacerItem>
#include "selfdrive/ui/sunnypilot/ui.h"
#include "selfdrive/ui/qt/util.h"
#include "system/hardware/hw.h"
#include "selfdrive/ui/qt/widgets/input.h"

ServerIpSettings::ServerIpSettings(QWidget* parent) : QWidget(parent) {
  main_layout = new QVBoxLayout(this);
  main_layout->setContentsMargins(50, 20, 50, 20);
  main_layout->setSpacing(20);

  // Back button
  PanelBackButton* back = new PanelBackButton();
  connect(back, &QPushButton::clicked, [=]() { emit backPress(); });
  main_layout->addWidget(back, 0, Qt::AlignLeft);

  // Configurar rutas de archivos
  // Probar múltiples rutas posibles para encontrar los archivos
  QString current_dir = QDir::currentPath();
  QStringList possible_bases = {
    current_dir,
    current_dir + "/..",
    current_dir + "/../..",
    Hardware::PC() ? QDir::homePath() + "/.comma/openpilot" : "/data/openpilot",
    "/data/openpilot"
  };

  // También probar rutas relativas directas desde el directorio actual
  QStringList test_adripilot_paths = {
    current_dir + "/sicuem/adripilot/config_mqtt.json",
    "sicuem/adripilot/config_mqtt.json",
    "../sicuem/adripilot/config_mqtt.json",
    "../../sicuem/adripilot/config_mqtt.json"
  };

  QStringList test_sicuem_paths = {
    current_dir + "/sicuem/config.json",
    "sicuem/config.json",
    "../sicuem/config.json",
    "../../sicuem/config.json"
  };

  // Añadir rutas basadas en possible_bases
  for (const QString& base : possible_bases) {
    test_adripilot_paths.append(base + "/sicuem/adripilot/config_mqtt.json");
    test_sicuem_paths.append(base + "/sicuem/config.json");
  }

  // Buscar archivo de AdriPilot
  for (const QString& path : test_adripilot_paths) {
    QFileInfo file_info(path);
    if (file_info.exists() && file_info.isReadable()) {
      adripilot_config_path = file_info.absoluteFilePath();
      break;
    }
  }

  // Buscar archivo de SICUEM
  for (const QString& path : test_sicuem_paths) {
    QFileInfo file_info(path);
    if (file_info.exists() && file_info.isReadable()) {
      sicuem_config_path = file_info.absoluteFilePath();
      break;
    }
  }

  // Si no se encontraron, usar las rutas por defecto
  if (adripilot_config_path.isEmpty()) {
    adripilot_config_path = "/data/openpilot/sicuem/adripilot/config_mqtt.json";
  }
  if (sicuem_config_path.isEmpty()) {
    sicuem_config_path = "/data/openpilot/sicuem/config.json";
  }

  setupAdriPilotSection();
  main_layout->addItem(new QSpacerItem(20, 30)); // Espacio entre secciones
  setupSicuemSection();

  main_layout->addStretch();
}

void ServerIpSettings::setupAdriPilotSection() {
  // Título AdriPilot
  adripilot_label = new QLabel(tr("Servidor AdriPilot"));
  adripilot_label->setStyleSheet("font-size: 55px; font-weight: 600; color: white; margin: 20px 0px 10px 0px;");
  main_layout->addWidget(adripilot_label);

  // Label de IP actual - se actualizará con la IP cargada
  adripilot_current_ip_label = new QLabel(tr("IP actual: -"));
  adripilot_current_ip_label->setStyleSheet("font-size: 45px; color: #aaaaaa; margin: 10px 0px;");
  main_layout->addWidget(adripilot_current_ip_label);

  // Input para IP AdriPilot
  adripilot_input = new QLineEdit(this);
  adripilot_input->setPlaceholderText(tr("Ingrese la IP del servidor AdriPilot"));
  adripilot_input->setStyleSheet(R"(
    QLineEdit {
      font-size: 48px;
      padding: 20px;
      border-radius: 10px;
      background-color: #393939;
      color: white;
      border: 2px solid #555555;
    }
    QLineEdit:focus {
      border: 2px solid #00a6fb;
    }
  )");
  // Abrir teclado táctil al tocar (dispositivo Comma)
  adripilot_input->setReadOnly(true);
  adripilot_input->installEventFilter(this);
  main_layout->addWidget(adripilot_input);

  // Botón Guardar AdriPilot
  adripilot_save_btn = new QPushButton(tr("GUARDAR IP ADRIPILOT"));
  adripilot_save_btn->setStyleSheet(R"(
    QPushButton {
      font-size: 50px;
      font-weight: 600;
      padding: 25px;
      border-radius: 10px;
      background-color: #00a6fb;
      color: white;
      border: none;
    }
    QPushButton:pressed {
      background-color: #0088cc;
    }
  )");
  connect(adripilot_save_btn, &QPushButton::clicked, this, &ServerIpSettings::saveAdriPilotIp);
  main_layout->addWidget(adripilot_save_btn);
}

void ServerIpSettings::setupSicuemSection() {
  // Título SICUEM
  sicuem_label = new QLabel(tr("Servidor SICUEM (Universidad Europea)"));
  sicuem_label->setStyleSheet("font-size: 55px; font-weight: 600; color: white; margin: 20px 0px 10px 0px;");
  main_layout->addWidget(sicuem_label);

  // Label de IP actual - se actualizará con la IP cargada
  sicuem_current_ip_label = new QLabel(tr("IP actual: -"));
  sicuem_current_ip_label->setStyleSheet("font-size: 45px; color: #aaaaaa; margin: 10px 0px;");
  main_layout->addWidget(sicuem_current_ip_label);

  // Input para IP SICUEM
  sicuem_input = new QLineEdit(this);
  sicuem_input->setPlaceholderText(tr("Ingrese la IP del servidor SICUEM"));
  sicuem_input->setStyleSheet(R"(
    QLineEdit {
      font-size: 48px;
      padding: 20px;
      border-radius: 10px;
      background-color: #393939;
      color: white;
      border: 2px solid #555555;
    }
    QLineEdit:focus {
      border: 2px solid #00a6fb;
    }
  )");
  // Abrir teclado táctil al tocar (dispositivo Comma)
  sicuem_input->setReadOnly(true);
  sicuem_input->installEventFilter(this);
  main_layout->addWidget(sicuem_input);

  // Botón Guardar SICUEM
  sicuem_save_btn = new QPushButton(tr("GUARDAR IP SICUEM"));
  sicuem_save_btn->setStyleSheet(R"(
    QPushButton {
      font-size: 50px;
      font-weight: 600;
      padding: 25px;
      border-radius: 10px;
      background-color: #00a6fb;
      color: white;
      border: none;
    }
    QPushButton:pressed {
      background-color: #0088cc;
    }
  )");
  connect(sicuem_save_btn, &QPushButton::clicked, this, &ServerIpSettings::saveSicuemIp);
  main_layout->addWidget(sicuem_save_btn);
}

QString ServerIpSettings::loadIpFromJson(const QString& file_path, const QString& key_path) {
  QFile file(file_path);

  // Verificar que el archivo existe
  if (!file.exists()) {
    return QString();
  }

  if (!file.open(QIODevice::ReadOnly | QIODevice::Text)) {
    return QString();
  }

  QByteArray data = file.readAll();
  file.close();

  if (data.isEmpty()) {
    return QString();
  }

  QJsonParseError error;
  QJsonDocument doc = QJsonDocument::fromJson(data, &error);

  if (error.error != QJsonParseError::NoError || doc.isNull() || !doc.isObject()) {
    return QString();
  }

  QJsonObject root = doc.object();

  // Para AdriPilot: "broker" está en la raíz
  if (key_path == "broker") {
    if (root.contains("broker") && root["broker"].isString()) {
      QString ip = root["broker"].toString();
      if (!ip.isEmpty()) {
        return ip;
      }
    }
  }

  // Para SICUEM: "config.IpServer.value" está anidado
  if (key_path == "config.IpServer.value") {
    if (root.contains("config") && root["config"].isObject()) {
      QJsonObject config = root["config"].toObject();
      if (config.contains("IpServer") && config["IpServer"].isObject()) {
        QJsonObject ipServer = config["IpServer"].toObject();
        if (ipServer.contains("value") && ipServer["value"].isString()) {
          QString ip = ipServer["value"].toString();
          if (!ip.isEmpty()) {
            return ip;
          }
        }
      }
    }
  }

  return QString();
}

bool ServerIpSettings::saveIpToJson(const QString& file_path, const QString& key_path, const QString& ip) {
  QFile file(file_path);
  QJsonObject root;

  // Leer archivo existente si existe
  if (file.exists()) {
    if (file.open(QIODevice::ReadOnly | QIODevice::Text)) {
      QByteArray data = file.readAll();
      file.close();
      QJsonDocument doc = QJsonDocument::fromJson(data);
      if (!doc.isNull() && doc.isObject()) {
        root = doc.object();
      }
    }
  }

  // Actualizar el valor
  if (key_path == "broker") {
    root["broker"] = ip;
  } else if (key_path == "config.IpServer.value") {
    if (!root.contains("config") || !root["config"].isObject()) {
      root["config"] = QJsonObject();
    }
    QJsonObject config = root["config"].toObject();
    if (!config.contains("IpServer") || !config["IpServer"].isObject()) {
      config["IpServer"] = QJsonObject();
    }
    QJsonObject ipServer = config["IpServer"].toObject();
    ipServer["value"] = ip;
    config["IpServer"] = ipServer;
    root["config"] = config;
  }

  // Escribir archivo
  if (file.open(QIODevice::WriteOnly | QIODevice::Text | QIODevice::Truncate)) {
    QJsonDocument doc(root);
    file.write(doc.toJson(QJsonDocument::Indented));
    file.close();
    return true;
  }

  return false;
}

void ServerIpSettings::loadIps() {
  // Cargar IP AdriPilot
  QString adripilot_ip = loadIpFromJson(adripilot_config_path, "broker");
  if (!adripilot_ip.isEmpty()) {
    adripilot_input->setText(adripilot_ip);
    adripilot_current_ip_label->setText(tr("IP actual: %1").arg(adripilot_ip));
  } else {
    // Si no se encontró, intentar leer desde la ruta relativa también
    QString relative_path = "sicuem/adripilot/config_mqtt.json";
    if (QFile::exists(relative_path)) {
      adripilot_ip = loadIpFromJson(relative_path, "broker");
      if (!adripilot_ip.isEmpty()) {
        adripilot_config_path = QFileInfo(relative_path).absoluteFilePath();
        adripilot_input->setText(adripilot_ip);
        adripilot_current_ip_label->setText(tr("IP actual: %1").arg(adripilot_ip));
      } else {
        adripilot_current_ip_label->setText(tr("IP actual: (No configurada)"));
      }
    } else {
      adripilot_current_ip_label->setText(tr("IP actual: (No configurada)"));
    }
  }

  // Cargar IP SICUEM
  QString sicuem_ip = loadIpFromJson(sicuem_config_path, "config.IpServer.value");
  if (!sicuem_ip.isEmpty()) {
    sicuem_input->setText(sicuem_ip);
    sicuem_current_ip_label->setText(tr("IP actual: %1").arg(sicuem_ip));
  } else {
    // Si no se encontró, intentar leer desde la ruta relativa también
    QString relative_path = "sicuem/config.json";
    if (QFile::exists(relative_path)) {
      sicuem_ip = loadIpFromJson(relative_path, "config.IpServer.value");
      if (!sicuem_ip.isEmpty()) {
        sicuem_config_path = QFileInfo(relative_path).absoluteFilePath();
        sicuem_input->setText(sicuem_ip);
        sicuem_current_ip_label->setText(tr("IP actual: %1").arg(sicuem_ip));
      } else {
        sicuem_current_ip_label->setText(tr("IP actual: (No configurada)"));
      }
    } else {
      sicuem_current_ip_label->setText(tr("IP actual: (No configurada)"));
    }
  }
}

void ServerIpSettings::saveAdriPilotIp() {
  QString ip = adripilot_input->text().trimmed();
  if (ip.isEmpty()) {
    // Mostrar mensaje de error (simplificado)
    return;
  }

  if (saveIpToJson(adripilot_config_path, "broker", ip)) {
    // Actualizar label de IP actual
    adripilot_current_ip_label->setText(tr("IP actual: %1").arg(ip));
  }
}

void ServerIpSettings::saveSicuemIp() {
  QString ip = sicuem_input->text().trimmed();
  if (ip.isEmpty()) {
    // Mostrar mensaje de error (simplificado)
    return;
  }

  if (saveIpToJson(sicuem_config_path, "config.IpServer.value", ip)) {
    // Actualizar label de IP actual
    sicuem_current_ip_label->setText(tr("IP actual: %1").arg(ip));
  }
}

bool ServerIpSettings::eventFilter(QObject* watched, QEvent* event) {
  // Abrir teclado en pantalla cuando se toque el QLineEdit
  if ((watched == adripilot_input || watched == sicuem_input) && event->type() == QEvent::MouseButtonPress) {
    const bool is_adripilot = (watched == adripilot_input);
    const QString title = is_adripilot ? tr("IP Servidor AdriPilot") : tr("IP Servidor SICUEM");
    QLineEdit* target = is_adripilot ? adripilot_input : sicuem_input;
    const QString current = target->text();

    const QString new_text = InputDialog::getText(title, this, QString(), /*secret=*/false, /*minLength=*/1, current);
    if (!new_text.isEmpty()) {
      target->setText(new_text);
    }
    return true; // Consumir el evento
  }
  return QWidget::eventFilter(watched, event);
}

void ServerIpSettings::showEvent(QShowEvent* event) {
  loadIps();
  QWidget::showEvent(event);
}

