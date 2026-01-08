#include "selfdrive/ui/sunnypilot/qt/onroad/debug_panel.h"

#include <QPainter>
#include <QStyleOption>
#include "selfdrive/ui/qt/util.h"

DebugPanel::DebugPanel(QWidget *parent) : QWidget(parent), is_hidden(false) {
  debug_file = "/tmp/mqtt_debug_messages.txt";
  setupUI();

  // Timer para actualizar mensajes cada 500ms
  update_timer = new QTimer(this);
  connect(update_timer, &QTimer::timeout, this, &DebugPanel::updateMessages);
  update_timer->start(500);

  // Estado inicial: abierto (no oculto)
  is_hidden = false;
  updateMessages();
}

void DebugPanel::setupUI() {
  // El tamaño se ajustará dinámicamente cuando se muestre en paintGL
  // Usamos valores por defecto que se actualizarán después
  setFixedWidth(960);
  setFixedHeight(1080);

  // Layout principal
  main_layout = new QVBoxLayout(this);
  main_layout->setContentsMargins(0, 0, 0, 0);
  main_layout->setSpacing(0);

  // Header con título y botones
  header_layout = new QHBoxLayout();
  header_layout->setContentsMargins(25, 20, 25, 20);
  header_layout->setSpacing(20);

  // Título
  title_label = new QLabel("MQTT DEBUG", this);
  title_label->setStyleSheet(
    "QLabel {"
    "  color: #FFFFFF;"
    "  font-size: 72px;"
    "  font-weight: bold;"
    "  background: transparent;"
    "}"
  );
  header_layout->addWidget(title_label);
  header_layout->addStretch();

  // Botón limpiar (papelera)
  clear_btn = new QPushButton(this);
  clear_btn->setFixedSize(100, 100);
  clear_btn->setStyleSheet(
    "QPushButton {"
    "  background-color: rgba(255, 0, 0, 150);"
    "  border: 3px solid rgba(255, 255, 255, 200);"
    "  border-radius: 50px;"
    "  color: white;"
    "  font-size: 56px;"
    "  font-weight: bold;"
    "}"
    "QPushButton:pressed {"
    "  background-color: rgba(200, 0, 0, 200);"
    "}"
  );
  clear_btn->setText("🗑");
  connect(clear_btn, &QPushButton::clicked, this, &DebugPanel::onClearClicked);
  header_layout->addWidget(clear_btn);

  // Botón ocultar/mostrar
  toggle_btn = new QPushButton(this);
  toggle_btn->setFixedSize(100, 100);
  toggle_btn->setStyleSheet(
    "QPushButton {"
    "  background-color: rgba(0, 150, 255, 150);"
    "  border: 3px solid rgba(255, 255, 255, 200);"
    "  border-radius: 50px;"
    "  color: white;"
    "  font-size: 56px;"
    "  font-weight: bold;"
    "}"
    "QPushButton:pressed {"
    "  background-color: rgba(0, 120, 200, 200);"
    "}"
  );
  // Estado inicial: abierto, así que la flecha apunta a la izquierda (para ocultar)
  toggle_btn->setText("◀");
  connect(toggle_btn, &QPushButton::clicked, this, &DebugPanel::onToggleClicked);
  header_layout->addWidget(toggle_btn);

  main_layout->addLayout(header_layout);

  // Área de scroll para mensajes
  scroll_area = new QScrollArea(this);
  scroll_area->setWidgetResizable(true);
  scroll_area->setHorizontalScrollBarPolicy(Qt::ScrollBarAlwaysOff);
  scroll_area->setVerticalScrollBarPolicy(Qt::ScrollBarAsNeeded);
  scroll_area->setStyleSheet(
    "QScrollArea {"
    "  background-color: transparent;"
    "  border: none;"
    "}"
    "QScrollBar:vertical {"
    "  background-color: rgba(50, 50, 50, 200);"
    "  width: 35px;"
    "  border-radius: 17px;"
    "}"
    "QScrollBar::handle:vertical {"
    "  background-color: rgba(150, 150, 150, 200);"
    "  min-height: 50px;"
    "  border-radius: 17px;"
    "}"
    "QScrollBar::handle:vertical:hover {"
    "  background-color: rgba(200, 200, 200, 255);"
    "}"
  );

  // Widget de contenido para el scroll
  scroll_content = new QWidget();
  scroll_content->setStyleSheet("background-color: transparent;");

  QVBoxLayout *content_layout = new QVBoxLayout(scroll_content);
  content_layout->setContentsMargins(20, 10, 20, 20);
  content_layout->setSpacing(10);

  messages_label = new QLabel("Esperando mensajes MQTT...", scroll_content);
  messages_label->setStyleSheet(
    "QLabel {"
    "  color: #FFFFFF;"
    "  font-size: 40px;"
    "  font-family: 'Courier New', monospace;"
    "  background-color: transparent;"
    "  padding: 15px;"
    "}"
  );
  messages_label->setWordWrap(true);
  messages_label->setAlignment(Qt::AlignTop | Qt::AlignLeft);
  content_layout->addWidget(messages_label);
  content_layout->addStretch();

  scroll_area->setWidget(scroll_content);
  main_layout->addWidget(scroll_area);

  // Estilo del panel (se actualizará dinámicamente según el estado)
  updatePanelStyle();
}

void DebugPanel::loadMessages() {
  QFile file(debug_file);
  QString messages_html = "";

  if (file.exists() && file.open(QIODevice::ReadOnly | QIODevice::Text)) {
    QTextStream in(&file);
    QString content = in.readAll();
    file.close();

    if (content.trimmed().isEmpty()) {
      messages_html = "<span style='color: #888888;'>Esperando mensajes MQTT...</span>";
    } else {
      // Dividir por doble salto de línea (separador de mensajes)
      // Usamos QString::SkipEmptyParts para compatibilidad con la versión de Qt del comma
      QStringList messages = content.split("\n\n", QString::SkipEmptyParts);

      // Mostrar los últimos 50 mensajes
      int start = messages.size() > 50 ? messages.size() - 50 : 0;
      for (int i = start; i < messages.size(); i++) {
        QString message = messages[i].trimmed();
        if (!message.isEmpty()) {
          // Dividir en líneas para formatear
          QStringList lines = message.split('\n');
          for (const QString &line : lines) {
            if (!line.trimmed().isEmpty()) {
              messages_html += formatMessage(line.trimmed()) + "<br>";
            }
          }
          messages_html += "<br>"; // Separador entre mensajes
        }
      }
    }
  } else {
    messages_html = "<span style='color: #888888;'>Esperando mensajes MQTT...</span>";
  }

  messages_label->setText(messages_html);

  // Ajustar tamaño del contenido
  messages_label->adjustSize();
  scroll_content->adjustSize();

  // Scroll automático al final
  QScrollBar *vbar = scroll_area->verticalScrollBar();
  if (vbar) {
    vbar->setValue(vbar->maximum());
  }
}

QString DebugPanel::formatMessage(const QString &line) {
  QString formatted = line;

  // Colorear timestamp
  if (formatted.startsWith("[")) {
    int end_bracket = formatted.indexOf("]");
    if (end_bracket > 0) {
      QString timestamp = formatted.left(end_bracket + 1);
      QString rest = formatted.mid(end_bracket + 1);
      formatted = QString("<span style='color: #00FF00; font-weight: bold;'>%1</span>%2")
                  .arg(timestamp, rest);
    }
  }

  // Colorear topics
  if (formatted.contains("telemetry_config/")) {
    int topic_start = formatted.indexOf("telemetry_config/");
    int topic_end = formatted.indexOf(" ", topic_start);
    if (topic_end == -1) topic_end = formatted.length();

    QString topic = formatted.mid(topic_start, topic_end - topic_start);
    formatted = formatted.replace(topic,
      QString("<span style='color: #00BFFF; font-weight: bold;'>%1</span>").arg(topic));
  }

  // Colorear payloads JSON
  if (formatted.contains("{") || formatted.contains("true") || formatted.contains("false")) {
    formatted = formatted.replace(QRegExp("(\\{[^}]*\\}|true|false)"),
      "<span style='color: #FFD700;'>\\1</span>");
  }

  return formatted;
}

void DebugPanel::updateMessages() {
  if (!is_hidden) {
    loadMessages();
  }
}

void DebugPanel::updateSize() {
  if (is_hidden) {
    // Cuando está oculto: card pequeño pegado al borde izquierdo
    int panel_width = 120;
    int panel_height = 120;
    setFixedSize(panel_width, panel_height);

    if (parentWidget()) {
      int parent_height = parentWidget()->height();
      int y_pos = (parent_height - panel_height) / 2;
      move(0, y_pos);  // x=0 para estar literalmente pegado al borde izquierdo
    } else {
      move(0, 0);
    }
  } else {
    // Cuando está abierto: mitad de pantalla
    int panel_width = parentWidget() ? parentWidget()->width() / 2 : 960;
    int panel_height = parentWidget() ? parentWidget()->height() : 1080;
    setFixedSize(panel_width, panel_height);
    if (parentWidget()) {
      move(0, 0);
    }
  }
}

void DebugPanel::onClearClicked() {
  // Limpiar el archivo de mensajes
  QFile file(debug_file);
  if (file.exists()) {
    file.remove();
  }
  updateMessages();
}

void DebugPanel::updatePanelStyle() {
  if (is_hidden) {
    // Cuando está oculto: fondo negro tipo card pequeño alrededor de la flecha
    setStyleSheet(
      "DebugPanel {"
      "  background-color: rgba(0, 0, 0, 200);"
      "  border-top-right-radius: 15px;"
      "  border-bottom-right-radius: 15px;"
      "}"
    );
  } else {
    // Cuando está abierto: fondo negro semi-transparente
    setStyleSheet(
      "DebugPanel {"
      "  background-color: rgba(0, 0, 0, 220);"
      "}"
    );
  }
}

void DebugPanel::onToggleClicked() {
  is_hidden = !is_hidden;

  if (is_hidden) {
    // Ocultar: solo mostrar una flecha pegada al borde izquierdo
    scroll_area->hide();
    title_label->hide();
    clear_btn->hide();
    toggle_btn->setText("▶");

    // Centrar el botón en el card pequeño
    header_layout->setContentsMargins(8, 15, 8, 15);

    // Actualizar tamaño y posición
    updateSize();

    // Actualizar estilo: fondo negro tipo card pequeño
    updatePanelStyle();
  } else {
    // Mostrar: restaurar tamaño completo (mitad de pantalla)
    scroll_area->show();
    title_label->show();
    clear_btn->show();
    toggle_btn->setText("◀");

    // Restaurar el layout del header
    header_layout->setContentsMargins(25, 20, 25, 20);

    // Actualizar tamaño y posición
    updateSize();

    // Actualizar estilo: fondo negro
    updatePanelStyle();

    updateMessages();
  }

  // Forzar actualización del layout
  update();
  repaint();
}

void DebugPanel::paintEvent(QPaintEvent *event) {
  QStyleOption opt;
  opt.initFrom(this);
  QPainter p(this);
  style()->drawPrimitive(QStyle::PE_Widget, &opt, &p, this);
}
