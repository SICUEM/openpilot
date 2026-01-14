#include "selfdrive/ui/sunnypilot/qt/onroad/debug_panel.h"

#include <QPainter>
#include <QStyleOption>
#include "selfdrive/ui/qt/util.h"

DebugPanel::DebugPanel(QWidget *parent) : QWidget(parent), is_hidden(false) {
  // Usar la misma ruta que mqtt_comandos.py para compatibilidad con todos los dispositivos
  // En dispositivos reales, /tmp puede no ser persistente, pero mqtt_comandos.py ya maneja esto
  debug_file = "/tmp/mqtt_debug_messages.txt";

  // Limpiar mensajes anteriores al arrancar
  QFile file(debug_file);
  if (file.exists()) {
    file.remove();
  }

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

  // Botón ocultar/mostrar (ahora a la izquierda del header)
  toggle_btn = new QPushButton(this);
  toggle_btn->setFixedSize(120, 120);  // Botones un poco más pequeños
  toggle_btn->setStyleSheet(
    "QPushButton {"
    "  background-color: rgba(0, 150, 255, 150);"
    "  border: 4px solid rgba(255, 255, 255, 200);"
    "  border-radius: 60px;"
    "  color: white;"
    "  font-size: 70px;"
    "  font-weight: bold;"
    "}"
    "QPushButton:pressed {"
    "  background-color: rgba(0, 120, 200, 200);"
    "}"
  );
  // Estado inicial: abierto, así que la flecha apunta a la derecha (▶ para ocultar hacia la derecha)
  toggle_btn->setText("▶");
  connect(toggle_btn, &QPushButton::clicked, this, &DebugPanel::onToggleClicked);
  header_layout->addWidget(toggle_btn);

  // Título
  title_label = new QLabel("MQTT DEBUG", this);
  title_label->setStyleSheet(
    "QLabel {"
    "  color: #FFFFFF;"
    "  font-size: 64px;"  // Título más pequeño
    "  font-weight: bold;"
    "  background: transparent;"
    "}"
  );
  header_layout->addWidget(title_label);
  header_layout->addStretch();

  // Botón limpiar (papelera)
  clear_btn = new QPushButton(this);
  clear_btn->setFixedSize(120, 120);  // Botones un poco más pequeños
  clear_btn->setStyleSheet(
    "QPushButton {"
    "  background-color: rgba(255, 0, 0, 150);"
    "  border: 4px solid rgba(255, 255, 255, 200);"
    "  border-radius: 60px;"
    "  color: white;"
    "  font-size: 70px;"
    "  font-weight: bold;"
    "}"
    "QPushButton:pressed {"
    "  background-color: rgba(200, 0, 0, 200);"
    "}"
  );
  clear_btn->setText("🗑");
  connect(clear_btn, &QPushButton::clicked, this, &DebugPanel::onClearClicked);
  header_layout->addWidget(clear_btn);

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
    "  font-size: 72px;"  // Texto más grande
    "  font-family: 'Courier New', monospace;"
    "  background-color: transparent;"
    "  padding: 20px;"
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

  // Verificar si el archivo existe y es legible
  // Intentar abrir el archivo con permisos de lectura
  if (file.exists()) {
    if (file.open(QIODevice::ReadOnly | QIODevice::Text)) {
      QTextStream in(&file);
      // Limitar el tamaño del archivo leído para evitar problemas de memoria (máximo 50KB)
      QString content = in.read(50000);  // Leer máximo 50KB (reducido para ahorrar memoria)
      file.close();

      if (content.trimmed().isEmpty()) {
        messages_html = "<span style='color: #888888;'>Esperando mensajes MQTT...</span>";
      } else {
        // Dividir por doble salto de línea (separador de mensajes)
        // Usamos QString::SkipEmptyParts para compatibilidad con la versión de Qt del comma
        QStringList messages = content.split("\n\n", QString::SkipEmptyParts);

        // Mostrar los últimos 30 mensajes (reducido para ahorrar memoria)
        int start = messages.size() > 30 ? messages.size() - 30 : 0;
        for (int i = start; i < messages.size(); i++) {
          QString message = messages[i].trimmed();
          if (!message.isEmpty()) {
            // Formatear el mensaje completo (hora, topic y mensaje)
            messages_html += formatMessage(message) + "<br><br>"; // Separador entre mensajes
          }
        }
      }
    } else {
      // Archivo existe pero no se puede abrir (posible problema de permisos)
      messages_html = "<span style='color: #ff6666;'>Error: No se puede leer el archivo de debug</span>";
    }
  } else {
    // Archivo no existe aún (normal al inicio o si el modo debug no está activo)
    messages_html = "<span style='color: #888888;'>Esperando mensajes MQTT...<br>(Activa el modo debug para ver mensajes)</span>";
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

QString DebugPanel::formatMessage(const QString &message) {
  // Formato: hora (salto de línea) topic (1 palabra) (salto de línea) mensaje (solo valor)
  // Formato esperado: "[HH:MM:SS] topic\npayload"
  QString hora = "";
  QString topic = "";
  QString mensaje = "";

  QStringList lines = message.split('\n');
  if (lines.size() >= 1) {
    QString first_line = lines[0].trimmed();

    // Extraer hora (formato [HH:MM:SS])
    if (first_line.startsWith("[")) {
      int end_bracket = first_line.indexOf("]");
      if (end_bracket > 0) {
        hora = first_line.left(end_bracket + 1);
        first_line = first_line.mid(end_bracket + 1).trimmed();
      }
    }

    // Extraer solo la última palabra del topic (después del último /)
    // Ejemplo: "telemetry_config/DongleID/left" -> "left"
    if (first_line.contains("/")) {
      int last_slash = first_line.lastIndexOf("/");
      if (last_slash >= 0) {
        topic = first_line.mid(last_slash + 1).trimmed();
        // Eliminar espacios adicionales si los hay
        int space_pos = topic.indexOf(" ");
        if (space_pos > 0) {
          topic = topic.left(space_pos);
        }
      }
    }
  }

  // El payload está en la segunda línea (si existe)
  if (lines.size() >= 2) {
    QString payload = lines[1].trimmed();

    // Extraer solo el valor del payload
    // Si es JSON, extraer el valor (ej: {"enabled": true} -> true)
    if (payload.startsWith("{") && payload.contains(":")) {
      // Intentar extraer el valor del JSON
      // Buscar patrones como: "enabled": true, "speed_increase": true, etc.
      QRegExp json_value_regex(":\"?(true|false|-?\\d+)\"?");
      if (json_value_regex.indexIn(payload) >= 0) {
        mensaje = json_value_regex.cap(1);
      } else {
        // Si no coincide, intentar extraer cualquier valor después de ":"
        int colon_pos = payload.indexOf(":");
        if (colon_pos >= 0) {
          QString value_part = payload.mid(colon_pos + 1).trimmed();
          // Eliminar comillas y llaves
          value_part = value_part.remove("\"").remove("}").remove("{").trimmed();
          if (!value_part.isEmpty()) {
            mensaje = value_part;
          }
        }
      }
    } else {
      // Si no es JSON, usar el payload directamente (puede ser "true", "false", "1", "-1", etc.)
      mensaje = payload;
    }
  }

  // Formatear: cada elemento en su propia línea
  QString result = "";
  if (!hora.isEmpty()) {
    result += QString("<span style='color: #00FF00; font-weight: bold;'>%1</span><br>").arg(hora);
  }
  if (!topic.isEmpty()) {
    result += QString("<span style='color: #00BFFF; font-weight: bold;'>%1</span><br>").arg(topic);
  }
  if (!mensaje.isEmpty()) {
    // Colorear valores: true en verde, false en rojo
    if (mensaje == "true") {
      mensaje = QString("<span style='color: #00FF00; font-weight: bold;'>%1</span>").arg(mensaje);
    } else if (mensaje == "false") {
      mensaje = QString("<span style='color: #FF0000; font-weight: bold;'>%1</span>").arg(mensaje);
    } else if (mensaje == "1" || mensaje == "-1") {
      mensaje = QString("<span style='color: #FFD700;'>%1</span>").arg(mensaje);
    }
    result += mensaje;
  }

  return result.isEmpty() ? message : result;
}

void DebugPanel::updateMessages() {
  if (!is_hidden) {
    loadMessages();
  }
}

void DebugPanel::updateSize() {
  if (is_hidden) {
    // Cuando está oculto: card pequeño pegado al borde derecho que cubre bien el botón
    int panel_width = 150;  // Más ancho para cubrir bien el botón de 120x120
    int panel_height = 150;  // Más alto para cubrir bien el botón
    setFixedSize(panel_width, panel_height);

    if (parentWidget()) {
      int parent_width = parentWidget()->width();
      int parent_height = parentWidget()->height();
      int x_pos = parent_width - panel_width;  // Pegado al borde derecho
      int y_pos = (parent_height - panel_height) / 2;
      move(x_pos, y_pos);
    } else {
      move(0, 0);
    }
  } else {
    // Cuando está abierto: mitad de pantalla
    int panel_width = parentWidget() ? parentWidget()->width() / 2 : 960;
    int panel_height = parentWidget() ? parentWidget()->height() : 1080;
    setFixedSize(panel_width, panel_height);
    if (parentWidget()) {
      int parent_width = parentWidget()->width();
      int x_pos = parent_width - panel_width;  // Pegado al borde derecho
      move(x_pos, 0);
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
    // Cuando está oculto: fondo negro tipo card pequeño alrededor de la flecha (borde izquierdo ahora)
    setStyleSheet(
      "DebugPanel {"
      "  background-color: rgba(0, 0, 0, 220);"
      "  border-top-left-radius: 20px;"
      "  border-bottom-left-radius: 20px;"
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
    // Ocultar: solo mostrar una flecha pegada al borde derecho
    scroll_area->hide();
    title_label->hide();
    clear_btn->hide();
    toggle_btn->setText("◀");  // Flecha apunta a la izquierda (para abrir hacia la izquierda)

    // Centrar el botón en el card pequeño
    header_layout->setContentsMargins(8, 15, 8, 15);

    // Actualizar tamaño y posición
    updateSize();

    // Actualizar estilo: fondo negro tipo card pequeño
    updatePanelStyle();
  } else {
    // Mostrar: restaurar tamaño completo (1/3 de pantalla)
    scroll_area->show();
    title_label->show();
    clear_btn->show();
    toggle_btn->setText("▶");  // Flecha apunta a la derecha (para ocultar hacia la derecha)

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
