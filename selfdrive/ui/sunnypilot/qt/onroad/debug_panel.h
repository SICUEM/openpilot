#pragma once

#include <QWidget>
#include <QVBoxLayout>
#include <QHBoxLayout>
#include <QScrollArea>
#include <QScrollBar>
#include <QLabel>
#include <QPushButton>
#include <QTimer>
#include <QFile>
#include <QTextStream>
#include <QPaintEvent>

class DebugPanel : public QWidget {
  Q_OBJECT

public:
  explicit DebugPanel(QWidget *parent = nullptr);
  void updateMessages();
  void updateSize();  // Actualizar tamaño según estado

private slots:
  void onClearClicked();
  void onToggleClicked();

private:
  void setupUI();
  void loadMessages();
  QString formatMessage(const QString &line);
  void updatePanelStyle();

  QVBoxLayout *main_layout;
  QHBoxLayout *header_layout;
  QLabel *title_label;
  QPushButton *clear_btn;
  QPushButton *toggle_btn;
  QScrollArea *scroll_area;
  QLabel *messages_label;
  QWidget *scroll_content;

  bool is_hidden;
  QString debug_file;
  QTimer *update_timer;

  void paintEvent(QPaintEvent *event) override;
};
