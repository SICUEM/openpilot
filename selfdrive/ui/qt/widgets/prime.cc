#include "selfdrive/ui/qt/widgets/prime.h"

#include <QDebug>
#include <QJsonDocument>
#include <QJsonObject>
#include <QLabel>
#include <QPushButton>
#include <QStackedWidget>
#include <QTimer>
#include <QVBoxLayout>
#include <QPainter>

#include <QrCode.hpp>

#include "selfdrive/ui/qt/request_repeater.h"
#include "selfdrive/ui/qt/util.h"
#include "selfdrive/ui/qt/qt_window.h"
#include "selfdrive/ui/qt/widgets/wifi.h"
#include <QFile>
#include <QFileInfo>
#include <QJsonDocument>
#include <QJsonObject>
#include <QProcess>
#include <QDir>

using qrcodegen::QrCode;

PairingQRWidget::PairingQRWidget(QWidget* parent) : QWidget(parent) {
  timer = new QTimer(this);
  connect(timer, &QTimer::timeout, this, &PairingQRWidget::refresh);
}

void PairingQRWidget::showEvent(QShowEvent *event) {
  refresh();
  timer->start(5 * 60 * 1000);
  device()->setOffroadBrightness(100);
}

void PairingQRWidget::hideEvent(QHideEvent *event) {
  timer->stop();
  device()->setOffroadBrightness(BACKLIGHT_OFFROAD);
}

void PairingQRWidget::refresh() {
  QString pairToken = CommaApi::create_jwt({{"pair", true}});
  QString qrString = "https://connect.comma.ai/?pair=" + pairToken;
  this->updateQrCode(qrString);
  update();
}

void PairingQRWidget::updateQrCode(const QString &text) {
  QrCode qr = QrCode::encodeText(text.toUtf8().data(), QrCode::Ecc::LOW);
  qint32 sz = qr.getSize();
  QImage im(sz, sz, QImage::Format_RGB32);

  QRgb black = qRgb(0, 0, 0);
  QRgb white = qRgb(255, 255, 255);
  for (int y = 0; y < sz; y++) {
    for (int x = 0; x < sz; x++) {
      im.setPixel(x, y, qr.getModule(x, y) ? black : white);
    }
  }

  // Integer division to prevent anti-aliasing
  int final_sz = ((width() / sz) - 1) * sz;
  img = QPixmap::fromImage(im.scaled(final_sz, final_sz, Qt::KeepAspectRatio), Qt::MonoOnly);
}

void PairingQRWidget::paintEvent(QPaintEvent *e) {
  QPainter p(this);

  // Establecer un fondo blanco
  p.fillRect(rect(), Qt::white);

  // Ruta al archivo de imagen
  QString imagePath = "uem_logo.png"; // Asegúrate de que el archivo está en la misma carpeta que el ejecutable
  QPixmap logoPixmap(imagePath); // Renombramos la variable local a logoPixmap para evitar conflicto

  // Verificar si la imagen se cargó correctamente
  if (!logoPixmap.isNull()) {
    // Centrar la imagen en el widget
    QSize s = (size() - logoPixmap.size()) / 2;
    QRect targetRect(s.width(), s.height(), logoPixmap.width(), logoPixmap.height());
    p.drawPixmap(targetRect, logoPixmap);

    qDebug() << "Imagen dibujada correctamente en" << targetRect;
  } else {
    qDebug() << "Error: No se pudo cargar la imagen desde" << imagePath;
  }
}



PairingPopup::PairingPopup(QWidget *parent) : DialogBase(parent) {
  QHBoxLayout *hlayout = new QHBoxLayout(this);
  hlayout->setContentsMargins(0, 0, 0, 0);
  hlayout->setSpacing(0);

  setStyleSheet("PairingPopup { background-color: #E0E0E0; }");

  // text
  QVBoxLayout *vlayout = new QVBoxLayout();
  vlayout->setContentsMargins(85, 70, 50, 70);
  vlayout->setSpacing(50);
  hlayout->addLayout(vlayout, 1);
  {
    QPushButton *close = new QPushButton(QIcon(":/icons/close.svg"), "", this);
    close->setIconSize(QSize(80, 80));
    close->setStyleSheet("border: none;");
    vlayout->addWidget(close, 0, Qt::AlignLeft);
    QObject::connect(close, &QPushButton::clicked, this, &QDialog::reject);

    vlayout->addSpacing(30);

    QLabel *title = new QLabel(tr("Pair your device to your comma account"), this);
    title->setStyleSheet("font-size: 75px; color: black;");
    title->setWordWrap(true);
    vlayout->addWidget(title);

    QLabel *instructions = new QLabel(QString(R"(
      <ol type='1' style='margin-left: 15px;'>
        <li style='margin-bottom: 50px;'>%1</li>
        <li style='margin-bottom: 50px;'>%2</li>
        <li style='margin-bottom: 50px;'>%3</li>
      </ol>
    )").arg(tr("Go to https://connect.comma.ai on your phone"))
    .arg(tr("Click \"add new device\" and scan the QR code on the right"))
    .arg(tr("Bookmark connect.comma.ai to your home screen to use it like an app")), this);

    instructions->setStyleSheet("font-size: 47px; font-weight: bold; color: black;");
    instructions->setWordWrap(true);
    vlayout->addWidget(instructions);

    vlayout->addStretch();
  }

  // QR code
  PairingQRWidget *qr = new PairingQRWidget(this);
  hlayout->addWidget(qr, 1);
}


PrimeUserWidget::PrimeUserWidget(QWidget *parent) : QFrame(parent) {
  setObjectName("primeWidget");
  QVBoxLayout *mainLayout = new QVBoxLayout(this);
  mainLayout->setContentsMargins(56, 40, 56, 40);
  mainLayout->setSpacing(20);

  QLabel *subscribed = new QLabel(tr("✓ SUBSCRIBED"));
  subscribed->setStyleSheet("font-size: 41px; font-weight: bold; color: #86FF4E;");
  mainLayout->addWidget(subscribed);

  QLabel *commaPrime = new QLabel(tr("comma prime"));
  commaPrime->setStyleSheet("font-size: 75px; font-weight: bold;");
  mainLayout->addWidget(commaPrime);
}


#include <QPainter>

PrimeAdWidget::PrimeAdWidget(QWidget* parent) : QFrame(parent) {
  QVBoxLayout *main_layout = new QVBoxLayout(this);
  main_layout->setContentsMargins(80, 90, 80, 60);
  main_layout->setSpacing(0);

  // Crear un layout horizontal para SICUEM y la imagen
  QHBoxLayout *sicuem_layout = new QHBoxLayout();

  // Crear QLabel para el texto "SICUEM"
  QLabel *upgrade = new QLabel(tr("SICUEM"));
  upgrade->setStyleSheet("font-size: 75px; font-weight: bold; color: red;");
  sicuem_layout->addWidget(upgrade, 0, Qt::AlignLeft);

  // Crear QLabel para la imagen del logo
  QLabel *icon = new QLabel;
  QPixmap pixmap("../assets/offroad/icon_wifi_strength_full.sv"); // Ruta a la imagen
  if (!pixmap.isNull()) {
    icon->setPixmap(pixmap.scaledToWidth(100, Qt::SmoothTransformation)); // Ajustar el tamaño de la imagen
  } else {
    qDebug() << "Error: No se pudo cargar la imagen desde ../assets/images/sicuem_logo.png";
  }
  sicuem_layout->addWidget(icon, 0, Qt::AlignRight);

  // Añadir el layout horizontal al layout principal
  main_layout->addLayout(sicuem_layout, 0);
  main_layout->addSpacing(50);

  // Descripción
  QLabel *description = new QLabel(tr("Grupo de investigacion de la Universidad Europea"));
  description->setStyleSheet("font-size: 56px; font-weight: light; color: white;");
  description->setWordWrap(true);
  main_layout->addWidget(description, 0, Qt::AlignTop);

  main_layout->addStretch();

  // Características
  QLabel *features = new QLabel(tr("Integrantes del grupo:"));
  features->setStyleSheet("font-size: 41px; font-weight: bold; color: #E5E5E5;");
  main_layout->addWidget(features, 0, Qt::AlignBottom);
  main_layout->addSpacing(30);

  QVector<QString> bullets = {tr("Adrian Cañadas"), tr("Javier F."), tr("Nourdine A."), tr("Sergio B.")};
  for (auto &b : bullets) {
    const QString check = "<b><font color='#465BEA'>✓</font></b> ";
    QLabel *l = new QLabel(check + b);
    l->setAlignment(Qt::AlignLeft);
    l->setStyleSheet("font-size: 50px; margin-bottom: 15px;");
    main_layout->addWidget(l, 0, Qt::AlignBottom);
  }

  setStyleSheet(R"(
    PrimeAdWidget {
      border-radius: 10px;
      background-color: #333333;
    }
  )");
}





SetupWidget::SetupWidget(QWidget* parent) : QFrame(parent) {
  mainLayout = new QStackedWidget;

  // Unpaired, registration prompt layout

  QFrame* finishRegistration = new QFrame;
  finishRegistration->setObjectName("primeWidget");
  QVBoxLayout* finishRegistationLayout = new QVBoxLayout(finishRegistration);
  finishRegistationLayout->setSpacing(38);
  finishRegistationLayout->setContentsMargins(64, 48, 64, 48);

  QLabel* registrationTitle = new QLabel(tr("Finish Setup"));
  registrationTitle->setStyleSheet("font-size: 75px; font-weight: bold;");
  finishRegistationLayout->addWidget(registrationTitle);

  QLabel* registrationDescription = new QLabel(tr("Pair your device with comma connect (connect.comma.ai) and claim your comma prime offer."));
  registrationDescription->setWordWrap(true);
  registrationDescription->setStyleSheet("font-size: 50px; font-weight: light;");
  finishRegistationLayout->addWidget(registrationDescription);

  finishRegistationLayout->addStretch();

  QPushButton* pair = new QPushButton(tr("Pair device"));
  pair->setStyleSheet(R"(
    QPushButton {
      font-size: 55px;
      font-weight: 500;
      border-radius: 10px;
      background-color: #465BEA;
      padding: 64px;
    }
    QPushButton:pressed {
      background-color: #3049F4;
    }
  )");
  finishRegistationLayout->addWidget(pair);

  popup = new PairingPopup(this);
  QObject::connect(pair, &QPushButton::clicked, popup, &PairingPopup::exec);

  mainLayout->addWidget(finishRegistration);

  // build stacked layout
  QVBoxLayout *outer_layout = new QVBoxLayout(this);
  outer_layout->setContentsMargins(0, 0, 0, 0);
  outer_layout->addWidget(mainLayout);

  QWidget *content = new QWidget;
  QVBoxLayout *content_layout = new QVBoxLayout(content);
  content_layout->setContentsMargins(40, 30, 40, 30);
  content_layout->setSpacing(20);

  // Cabecera UEM
  QWidget *header = new QWidget(content);
  QVBoxLayout *hl = new QVBoxLayout(header);
  hl->setContentsMargins(0, 0, 0, 0);
  uemTitle = new QLabel(tr("Universidad Europea - UEM"), header);
  uemTitle->setStyleSheet("font-size: 75px; font-weight: 700; color: white;");
  uemSubtitle = new QLabel(tr("Integración AdriPilot / SICUEM"), header);
  uemSubtitle->setStyleSheet("font-size: 50px; color: #BDBDBD;");
  hl->addWidget(uemTitle);
  hl->addWidget(uemSubtitle);
  content_layout->addWidget(header);

  // Panel de estado de servidores
  auto mkIndicator = [](QWidget *parent) {
    QWidget *w = new QWidget(parent);
    w->setFixedSize(36, 36);
    w->setStyleSheet("border-radius: 18px; background: #888888;");
    return w;
  };

  auto mkRow = [&](const QString &label_text, QLabel **label_out, QWidget **ind_out) {
    QWidget *row = new QWidget(content);
    QHBoxLayout *rl = new QHBoxLayout(row);
    rl->setContentsMargins(0, 10, 0, 10);
    rl->setSpacing(20);
    QWidget *ind = mkIndicator(row);
    QLabel *lab = new QLabel(label_text, row);
    lab->setStyleSheet("font-size: 55px; color: white;");
    rl->addWidget(ind, 0, Qt::AlignLeft);
    rl->addWidget(lab, 0, Qt::AlignLeft);
    rl->addStretch(1);
    content_layout->addWidget(row);
    *label_out = lab;
    *ind_out = ind;
  };

  adripilotStatusLabel = nullptr;
  adripilotIndicator = nullptr;
  sicuemStatusLabel = nullptr;
  sicuemIndicator = nullptr;
  mkRow(tr("AdriPilot IP: - (DOWN)"), &adripilotStatusLabel, &adripilotIndicator);
  mkRow(tr("SICUEM IP: - (DOWN)"), &sicuemStatusLabel, &sicuemIndicator);

  content_layout->addStretch();
  mainLayout->addWidget(content);

  // Mostrar directamente el panel UEM simplificado
  mainLayout->setCurrentIndex(1);

  setStyleSheet(R"(
    #primeWidget {
      border-radius: 10px;
      background-color: #333333;
    }
  )");

  // Retain size while hidden
  QSizePolicy sp_retain = sizePolicy();
  sp_retain.setRetainSizeWhenHidden(true);
  setSizePolicy(sp_retain);

  // set up API requests
  if (auto dongleId = getDongleId()) {
    QString url = CommaApi::BASE_URL + "/v1.1/devices/" + *dongleId + "/";
    RequestRepeater* repeater = new RequestRepeater(this, url, "ApiCache_Device", 5);

    QObject::connect(repeater, &RequestRepeater::requestDone, this, &SetupWidget::replyFinished);
  }

  // Inicializar rutas de config y temporizador de estado
  ensureConfigPaths();
  statusTimer = new QTimer(this);
  statusTimer->setInterval(8000);
  QObject::connect(statusTimer, &QTimer::timeout, this, &SetupWidget::refreshNetworkStatus);
  statusTimer->start();
  QTimer::singleShot(100, this, &SetupWidget::refreshNetworkStatus);
}

void SetupWidget::replyFinished(const QString &response, bool success) {
  if (!success) return;

  QJsonDocument doc = QJsonDocument::fromJson(response.toUtf8());
  if (doc.isNull()) {
    qDebug() << "JSON Parse failed on getting pairing and prime status";
    return;
  }

  QJsonObject json = doc.object();
  bool is_paired = json["is_paired"].toBool();
  PrimeType prime_type = static_cast<PrimeType>(json["prime_type"].toInt());
  uiState()->setPrimeType(is_paired ? prime_type : PrimeType::UNPAIRED);

  if (!is_paired) {
    mainLayout->setCurrentIndex(0);
  } else {
    popup->reject();

    primeUser->setVisible(uiState()->hasPrime());
    mainLayout->setCurrentIndex(1);
  }
}

// Helpers
QString SetupWidget::loadIpFromJson(const QString &file_path, const QString &key_path) {
  QFile file(file_path);
  if (!file.exists() || !file.open(QIODevice::ReadOnly | QIODevice::Text)) return QString();
  const QByteArray data = file.readAll();
  file.close();
  QJsonParseError err; QJsonDocument doc = QJsonDocument::fromJson(data, &err);
  if (err.error != QJsonParseError::NoError || !doc.isObject()) return QString();
  QJsonObject root = doc.object();
  if (key_path == "broker") {
    return root.value("broker").toString();
  }
  if (key_path == "config.IpServer.value") {
    QJsonObject cfg = root.value("config").toObject();
    QJsonObject ipS = cfg.value("IpServer").toObject();
    return ipS.value("value").toString();
  }
  return QString();
}

void SetupWidget::ensureConfigPaths() {
  QStringList bases = { QDir::currentPath(), QDir::currentPath()+"/..", QDir::currentPath()+"/../..", "/data/openpilot" };
  for (const QString &b : bases) {
    QString a = b + "/sicuem/adripilot/config_mqtt.json";
    QString s = b + "/sicuem/config.json";
    if (adripilotConfigPath.isEmpty() && QFile::exists(a)) adripilotConfigPath = QFileInfo(a).absoluteFilePath();
    if (sicuemConfigPath.isEmpty() && QFile::exists(s)) sicuemConfigPath = QFileInfo(s).absoluteFilePath();
  }
  if (adripilotConfigPath.isEmpty()) adripilotConfigPath = "/data/openpilot/sicuem/adripilot/config_mqtt.json";
  if (sicuemConfigPath.isEmpty()) sicuemConfigPath = "/data/openpilot/sicuem/config.json";
}

bool SetupWidget::pingHost(const QString &ip, int timeout_ms) {
  if (ip.isEmpty()) return false;
  QProcess p;
  QStringList args = {"-c", "1", "-W", QString::number(qMax(1, timeout_ms/1000)), ip};
  p.start("/system/bin/ping", args);
  if (!p.waitForStarted(200)) {
    p.start("/bin/ping", args);
    if (!p.waitForStarted(200)) return false;
  }
  p.waitForFinished(timeout_ms + 500);
  return p.exitStatus() == QProcess::NormalExit && p.exitCode() == 0;
}

void SetupWidget::setIndicator(QWidget *w, bool up) {
  if (!w) return;
  w->setStyleSheet(QString("border-radius: 18px; background: %1;").arg(up ? "#27AE60" : "#C0392B"));
}

void SetupWidget::refreshNetworkStatus() {
  ensureConfigPaths();
  const QString ipA = loadIpFromJson(adripilotConfigPath, "broker");
  const QString ipS = loadIpFromJson(sicuemConfigPath, "config.IpServer.value");
  const bool upA = pingHost(ipA, 1000);
  const bool upS = pingHost(ipS, 1000);
  if (adripilotStatusLabel) adripilotStatusLabel->setText(tr("AdriPilot IP: %1 (%2)").arg(ipA.isEmpty()?"-":ipA, upA?"UP":"DOWN"));
  if (sicuemStatusLabel) sicuemStatusLabel->setText(tr("SICUEM IP: %1 (%2)").arg(ipS.isEmpty()?"-":ipS, upS?"UP":"DOWN"));
  setIndicator(adripilotIndicator, upA);
  setIndicator(sicuemIndicator, upS);
}
