#include "selfdrive/ui/sunnypilot/qt/offroad/settings/sunnypilot/jetson_settings.h"
#include <QFileInfo>
#include <QDir>
#include <QSpacerItem>
#include <QFrame>
#include <QTimer>
#include <QDateTime>
#include <QSaveFile>
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
  setupTorqueControlSection();
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

void JetsonSettings::setupTorqueControlSection() {
  QLabel* section_label = new QLabel(tr("Control del volante"));
  section_label->setStyleSheet("font-size: 50px; font-weight: 600; color: #E0E0E0; margin-top: 10px;");
  main_layout->addWidget(section_label);

  QLabel* desc = new QLabel(tr("Selecciona de donde sale el torque que se aplica al volante cuando el control lateral esta activo."));
  desc->setStyleSheet("font-size: 32px; color: #BDBDBD;");
  desc->setWordWrap(true);
  main_layout->addWidget(desc);

  // Fila con los 3 botones de modo
  QWidget* mode_row = new QWidget();
  QHBoxLayout* ml = new QHBoxLayout(mode_row);
  ml->setContentsMargins(0, 15, 0, 0);
  ml->setSpacing(15);

  auto makeModeButton = [](const QString& text, const QString& accent) {
    QPushButton* b = new QPushButton(text);
    b->setCheckable(true);
    b->setMinimumHeight(120);
    b->setStyleSheet(QString(R"(
      QPushButton {
        font-size: 38px;
        font-weight: 700;
        padding: 20px;
        border-radius: 15px;
        background-color: #393939;
        color: #BDBDBD;
        border: 3px solid #555555;
      }
      QPushButton:checked {
        background-color: %1;
        color: white;
        border: 3px solid %1;
      }
    )").arg(accent));
    return b;
  };

  btn_mode_model        = makeModeButton(tr("★ MODELO\nCOMMA\n(RECOMENDADO)"),  "#76B900");  // verde, recomendado
  btn_mode_comma_jetson = makeModeButton(tr("COMMA + JETSON\n(esquive obstaculos)"), "#3B82F6");  // azul
  btn_mode_jetson       = makeModeButton(tr("JETSON\n(PilotNet)"), "#F59E0B");  // naranja
  btn_mode_test         = makeModeButton(tr("⚠ TEST MAX\n(PELIGROSO)"), "#EF4444");  // rojo

  ml->addWidget(btn_mode_model);
  ml->addWidget(btn_mode_comma_jetson);  // 2ª posición visual
  ml->addWidget(btn_mode_jetson);
  ml->addWidget(btn_mode_test);
  main_layout->addWidget(mode_row);

  // Label de estado
  torque_status_label = new QLabel();
  torque_status_label->setStyleSheet("font-size: 34px; font-weight: 600; padding: 12px; border-radius: 10px; margin-top: 8px;");
  torque_status_label->setWordWrap(true);
  main_layout->addWidget(torque_status_label);

  // Indicador de estado del esquive (modo 3 - obstáculo Jetson)
  obstacle_status_label = new QLabel();
  obstacle_status_label->setStyleSheet(
    "font-size: 28px; font-weight: 600; padding: 8px; border-radius: 8px; margin-top: 6px;"
  );
  obstacle_status_label->setWordWrap(true);
  obstacle_status_label->setVisible(false);
  main_layout->addWidget(obstacle_status_label);

  // Conectar cada boton a su modo (0=modelo, 1=jetson, 2=test max, 3=comma+jetson)
  // Usamos tryChangeSteerMode que muestra un dialogo de confirmacion antes
  connect(btn_mode_model,        &QPushButton::clicked, this, [this]() { tryChangeSteerMode(0); });
  connect(btn_mode_comma_jetson, &QPushButton::clicked, this, [this]() { tryChangeSteerMode(3); });
  connect(btn_mode_jetson,       &QPushButton::clicked, this, [this]() { tryChangeSteerMode(1); });
  connect(btn_mode_test,         &QPushButton::clicked, this, [this]() { tryChangeSteerMode(2); });

  // Estado inicial: leer el param guardado y pintar los botones.
  // OJO: usamos updateSteerModeVisual (solo UI), NO onSteerModeChanged.
  // onSteerModeChanged publicaria un payload MQTT "source=comma_ui" cada vez
  // que el usuario abre la pantalla, lo cual es spam innecesario.
  std::string mode_str = Params().get("SteerTorqueMode");
  int mode = 0;
  try { mode = mode_str.empty() ? 0 : std::stoi(mode_str); } catch (...) { mode = 0; }
  updateSteerModeVisual(mode);

  // Timer de sincronizacion: mientras la pantalla este visible, sondeamos:
  //   - SteerTorqueMode (param): refresca botones si cambio por MQTT.
  //   - config_jetson.json (archivo): refresca IP/puertos/quality si cambio
  //     por fuera (la app envio jetson_config y mqtt_comandos reescribio
  //     el JSON). Comparamos mtime para no releer/repintar cada tick.
  // Ninguna de las dos ramas publica MQTT -> sin riesgo de eco.
  steer_mode_sync_timer = new QTimer(this);
  steer_mode_sync_timer->setInterval(500);
  connect(steer_mode_sync_timer, &QTimer::timeout, this, [this]() {
    // 1) Refresco del selector de torque
    std::string s = Params().get("SteerTorqueMode");
    int m = 0;
    try { m = s.empty() ? 0 : std::stoi(s); } catch (...) { m = 0; }
    if (m != last_steer_mode_ui) {
      updateSteerModeVisual(m);
    }

    // 2) Refresco de IP/puertos/quality si cambio el JSON.
    // Solo actuamos si NINGUN QLineEdit tiene el foco: asi no pisamos lo
    // que el usuario este escribiendo (los inputs son readOnly y se
    // editan con el keyboard dialog, pero por si acaso).
    QFileInfo fi(config_path);
    if (fi.exists()) {
      qint64 mtime = fi.lastModified().toMSecsSinceEpoch();
      if (mtime != last_config_mtime) {
        last_config_mtime = mtime;
        bool editing = ip_input->hasFocus() || comma_ip_input->hasFocus() ||
                       img_port_input->hasFocus() || torque_port_input->hasFocus();
        if (!editing) {
          loadConfig();
        }
      }
    }

    // 3) Indicador de estado del esquive (modo 3 obstáculo)
    std::string obs = Params().get("JetsonObstacleStatus");
    if (obs.empty()) {
      obstacle_status_label->setVisible(false);
    } else {
      QString text;
      QString bg = "#3B82F622";
      QString fg = "#3B82F6";
      if (obs == "DODGING_LEFT") {
        text = tr("🚨 ESQUIVANDO ←");
        bg = "#F59E0B33"; fg = "#F59E0B";
      } else if (obs == "DODGING_RIGHT") {
        text = tr("🚨 ESQUIVANDO →");
        bg = "#F59E0B33"; fg = "#F59E0B";
      } else if (obs == "CANCELED_DRIVER") {
        text = tr("⚠ Cancelado por conductor");
        bg = "#9CA3AF33"; fg = "#9CA3AF";
      } else if (obs == "CANCELED_STALE") {
        text = tr("❌ Jetson sin respuesta");
        bg = "#EF444433"; fg = "#EF4444";
      }
      obstacle_status_label->setText(text);
      obstacle_status_label->setStyleSheet(
        QString("background:%1; color:%2; font-size: 28px; font-weight: 600; padding: 8px; border-radius: 8px; margin-top: 6px;")
        .arg(bg).arg(fg)
      );
      obstacle_status_label->setVisible(true);
    }
  });
  // Se arranca/para en showEvent/hideEvent.
}

void JetsonSettings::tryChangeSteerMode(int mode) {
  // Leer modo actual para no pedir confirmacion si ya esta en ese modo
  Params params;
  std::string cur = params.get("SteerTorqueMode");
  int current = 0;
  try { current = cur.empty() ? 0 : std::stoi(cur); } catch (...) { current = 0; }

  // Refrescar estado visual de los botones (por si el usuario cancela)
  btn_mode_model->setChecked(current == 0);
  btn_mode_jetson->setChecked(current == 1);
  btn_mode_test->setChecked(current == 2);
  btn_mode_comma_jetson->setChecked(current == 3);

  if (mode == current) return;

  // Preparar mensaje segun el modo destino
  QString msg;
  bool confirmed = false;

  if (mode == 0) {
    // MODELO COMMA - opcion segura, confirmacion ligera
    msg = tr("Volver al MODELO COMMA (recomendado)\n\n"
             "El volante usara el torque calculado por el modelo interno de openpilot.\n\n"
             "Esta es la opcion mas segura y probada.");
    confirmed = ConfirmationDialog::confirm(msg, tr("Cambiar a MODELO COMMA"), this);
  } else if (mode == 1) {
    // JETSON - aviso importante
    msg = tr("⚠ ATENCION\n\n"
             "Vas a delegar el control del volante a la JETSON (PilotNet).\n\n"
             "El volante obedecera al torque que calcule la red neuronal externa a traves del torque que llegue desde la jetson por zmq.\n\n"
             "Asegurate de que:\n"
             "- La Jetson esta conectada y enviando torque por ZMQ\n"
             "- Estas en un entorno controlado\n"
             "- Tienes las manos sobre el volante\n\n"
             "Deseas continuar?");
    confirmed = ConfirmationDialog::confirm(msg, tr("SI, usar JETSON"), this);
  } else if (mode == 2) {
    // TEST MAX - aviso fuerte
    msg = tr("⚠⚠ PELIGRO - MODO DE PRUEBA ⚠⚠\n\n"
             "Este modo fija el torque del volante al MAXIMO hacia la DERECHA de forma continua.\n\n"
             "SOLO sirve para verificar que el punto de interceptacion del torque en controlsd.py funciona correctamente.\n\n"
             "Cuando el coche este en engage con openpilot, el volante girara a la derecha tanto como el panda permita.\n\n"
             "USALO SOLO EN PRUEBAS CONTROLADAS.\n"
             "USALO SOLO CON LAS MANOS EN EL VOLANTE.\n"
             "NO LO USES EN VIA PUBLICA.\n\n"
             "Deseas continuar?");
    confirmed = ConfirmationDialog::confirm(msg, tr("SI, ACTIVAR TEST MAX"), this);
  } else if (mode == 3) {
    // COMMA + JETSON - aviso medio, no peligroso
    msg = tr("Activar COMMA + JETSON\n\n"
             "El volante usara el torque calculado por el MODELO COMMA "
             "(comportamiento normal). Si la Jetson detecta un obstaculo "
             "en la carretera, aplicara temporalmente un esquive lateral "
             "(maximo 2.5 segundos).\n\n"
             "Requisitos:\n"
             "- La Jetson conectada y enviando alertas por ZMQ\n"
             "- Modelo de deteccion de obstaculos cargado en la Jetson");
    confirmed = ConfirmationDialog::confirm(msg, tr("SI, activar COMMA+JETSON"), this);
  }

  if (confirmed) {
    onSteerModeChanged(mode);
  } else {
    // Restaurar visual al estado previo
    btn_mode_model->setChecked(current == 0);
    btn_mode_jetson->setChecked(current == 1);
    btn_mode_test->setChecked(current == 2);
    btn_mode_comma_jetson->setChecked(current == 3);
  }
}

// Refresco VISUAL puro: actualiza botones + label de estado.
// No toca Params. No publica MQTT. Se usa cuando el cambio ha venido
// de fuera (app via MQTT -> mqtt_comandos.py ya escribio el param) y
// solo queremos que los botones de la pantalla del Comma reflejen el
// nuevo estado.
void JetsonSettings::updateSteerModeVisual(int mode) {
  btn_mode_model->setChecked(mode == 0);
  btn_mode_jetson->setChecked(mode == 1);
  btn_mode_test->setChecked(mode == 2);
  btn_mode_comma_jetson->setChecked(mode == 3);

  if (mode == 0) {
    torque_status_label->setText(tr("MODELO COMMA - El volante usa el torque del modelo interno (original)"));
    torque_status_label->setStyleSheet("font-size: 34px; font-weight: 600; padding: 12px; border-radius: 10px; background-color: rgba(118, 185, 0, 0.15); color: #76B900; border: 2px solid #76B900;");
  } else if (mode == 1) {
    torque_status_label->setText(tr("⚠ JETSON - El volante hara caso al torque que llega de la Jetson (PilotNet)"));
    torque_status_label->setStyleSheet("font-size: 34px; font-weight: 600; padding: 12px; border-radius: 10px; background-color: rgba(245, 158, 11, 0.2); color: #F59E0B; border: 2px solid #F59E0B;");
  } else if (mode == 2) {
    torque_status_label->setText(tr("⚠⚠ TEST MAX - Torque FIJO al maximo hacia la derecha (para probar interceptacion)"));
    torque_status_label->setStyleSheet("font-size: 34px; font-weight: 600; padding: 12px; border-radius: 10px; background-color: rgba(239, 68, 68, 0.2); color: #EF4444; border: 2px solid #EF4444;");
  } else if (mode == 3) {
    torque_status_label->setText(tr("COMMA + JETSON - Comma manda; la Jetson puede esquivar obstaculos"));
    torque_status_label->setStyleSheet("font-size: 34px; font-weight: 600; padding: 12px; border-radius: 10px; background-color: #3B82F622; color: #3B82F6; border: 2px solid #3B82F6;");
  }

  last_steer_mode_ui = mode;
}

// Cambio originado DESDE esta UI Qt (el usuario pulso un boton local).
// Escribe Params, refresca los botones y deja un payload MQTT para que
// mqtt_envio_general.py lo publique y llegue a la app.
void JetsonSettings::onSteerModeChanged(int mode) {
  Params params;
  params.put("SteerTorqueMode", std::to_string(mode));

  updateSteerModeVisual(mode);

  // Publicar via MQTT para sincronizar con app/servidor.
  // source=comma_ui -> el anti-eco de mqtt_comandos.py lo ignora si rebota.
  QString dongle_id = QString::fromStdString(params.get("DongleId"));
  if (!dongle_id.isEmpty()) {
    QJsonObject payload;
    payload["dongle_id"] = dongle_id;
    payload["steer_torque_mode"] = mode;
    payload["source"] = "comma_ui";
    payload["timestamp"] = QString::number(QDateTime::currentMSecsSinceEpoch());
    QJsonDocument doc(payload);
    params.put("SteerTorqueModeMqttPayload", doc.toJson(QJsonDocument::Compact).toStdString());
  }
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

  // Comma IP Address (IP de este dispositivo, para que la Jetson se conecte)
  comma_ip_label = new QLabel(tr("IP del Comma (este dispositivo):"));
  comma_ip_label->setStyleSheet("font-size: 40px; color: #aaaaaa; margin-top: 15px;");
  main_layout->addWidget(comma_ip_label);

  comma_ip_input = new QLineEdit();
  comma_ip_input->setPlaceholderText("127.0.0.1");
  comma_ip_input->setStyleSheet(R"(
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
      border: 2px solid #3B82F6;
    }
  )");
  comma_ip_input->setReadOnly(true);
  comma_ip_input->installEventFilter(this);
  main_layout->addWidget(comma_ip_input);

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

  // Escritura ATOMICA con QSaveFile: escribe a un temporal y hace rename()
  // al commit(). Asi, si un lector (mqtt_comandos.py, camera_sender.py)
  // accede mientras escribimos, o bien ve el contenido antiguo completo o
  // ve el nuevo completo, pero nunca un JSON a medio escribir / truncado.
  // Tambien protege si el proceso muere a mitad: el archivo original queda
  // intacto en vez de quedar corrupto.
  QSaveFile file(config_path);
  if (!file.open(QIODevice::WriteOnly | QIODevice::Text)) {
    return false;
  }
  QJsonDocument doc(config);
  file.write(doc.toJson(QJsonDocument::Indented));
  return file.commit();  // rename atomico + fsync implicito
}

void JetsonSettings::loadConfig() {
  QJsonObject config = loadJsonConfig();

  bool enabled = config.value("jetson_enabled").toBool(false);
  QString ip = config.value("jetson_ip").toString("192.168.1.50");
  QString comma_ip = config.value("comma_ip").toString("127.0.0.1");
  int img_port = config.value("jetson_img_port").toInt(5555);
  int torque_port = config.value("jetson_torque_port").toInt(5556);
  int quality = config.value("jpeg_quality").toInt(80);

  enabled_checkbox->setChecked(enabled);
  ip_input->setText(ip);
  comma_ip_input->setText(comma_ip);
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
  config["comma_ip"] = comma_ip_input->text().trimmed();
  config["jetson_img_port"] = img_port_input->text().trimmed().toInt();
  config["jetson_torque_port"] = torque_port_input->text().trimmed().toInt();
  config["jpeg_quality"] = quality_slider->value();

  // Version monotonica (ms desde epoch) que se persiste en el JSON Y viaja
  // en el payload MQTT. Permite que los consumidores (mqtt_comandos.py,
  // otros clientes MQTT) rechacen ecos/retained viejos: si una escritura
  // entrante trae _version <= al local, se ignora. Esto evita que una
  // publicacion retenida en el broker, de antes de este guardado, nos
  // pise la IP que el usuario acaba de poner.
  const qint64 version_ms = QDateTime::currentMSecsSinceEpoch();
  config["_version"] = QString::number(version_ms);

  if (saveJsonConfig(config)) {
    // Readback defensivo: releemos lo que acabamos de escribir. Si el
    // _version releido no coincide con el que acabamos de generar, otro
    // proceso pisó el archivo entre el commit y el readback -> avisamos
    // en consola para diagnostico. No bloqueamos al usuario.
    QJsonObject readback = loadJsonConfig();
    const QString readback_version = readback.value("_version").toString();
    if (readback_version != QString::number(version_ms)) {
      qWarning() << "[JETSON SYNC] readback _version mismatch after save. Expected"
                 << version_ms << "got" << readback_version;
    }

    updateStatusLabel();

    // Signal CameraSender to reload via Params
    Params params;
    params.putBool("JetsonConfigChanged", true);

    // Publish config via MQTT for app/server sync (propaga el mismo _version)
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

  // Leer el _version del JSON recien escrito para que el payload MQTT lleve
  // EXACTAMENTE la misma version que el disco. Asi, si este payload vuelve
  // al broker y nos regresa por eco/retained, comparando _version podemos
  // identificarlo como "nuestro" y no reescribir el disco con el.
  QJsonObject on_disk = loadJsonConfig();
  QString version_str = on_disk.value("_version").toString();

  QJsonObject payload;
  payload["dongle_id"] = dongle_id;
  payload["jetson_enabled"] = enabled_checkbox->isChecked();
  payload["jetson_ip"] = ip_input->text().trimmed();
  payload["comma_ip"] = comma_ip_input->text().trimmed();
  payload["jetson_img_port"] = img_port_input->text().trimmed().toInt();
  payload["jetson_torque_port"] = torque_port_input->text().trimmed().toInt();
  payload["jpeg_quality"] = quality_slider->value();
  payload["source"] = "comma_ui";
  payload["timestamp"] = QString::number(QDateTime::currentMSecsSinceEpoch());
  payload["_version"] = version_str;

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
    } else if (watched == comma_ip_input) {
      title = tr("IP del Comma (este dispositivo)");
      target = comma_ip_input;
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

  // Guardar mtime actual del JSON para que el timer solo dispare loadConfig()
  // de nuevo cuando el archivo cambie DESPUES de este momento (evita bucle).
  {
    QFileInfo fi(config_path);
    if (fi.exists()) {
      last_config_mtime = fi.lastModified().toMSecsSinceEpoch();
    }
  }

  // Refrescar el selector de torque por si cambio mientras la pantalla
  // estaba oculta (la app pudo enviar un cambio via MQTT). Visual puro,
  // sin re-publicar MQTT.
  {
    std::string s = Params().get("SteerTorqueMode");
    int m = 0;
    try { m = s.empty() ? 0 : std::stoi(s); } catch (...) { m = 0; }
    updateSteerModeVisual(m);
  }

  // Arrancar el poll de sincronizacion mientras esta visible.
  if (steer_mode_sync_timer && !steer_mode_sync_timer->isActive()) {
    steer_mode_sync_timer->start();
  }

  QWidget::showEvent(event);
}

void JetsonSettings::hideEvent(QHideEvent* event) {
  // Paramos el poll cuando la pantalla no esta visible.
  // No hace falta gastar CPU sondeando si el usuario no lo ve; cuando
  // vuelva a showEvent se refresca el estado y se reanuda.
  if (steer_mode_sync_timer && steer_mode_sync_timer->isActive()) {
    steer_mode_sync_timer->stop();
  }
  QWidget::hideEvent(event);
}
