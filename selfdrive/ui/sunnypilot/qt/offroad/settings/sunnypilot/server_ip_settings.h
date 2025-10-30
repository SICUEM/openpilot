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

#pragma once

#include <QObject>
#include <QWidget>
#include <QVBoxLayout>
#include <QHBoxLayout>
#include <QLabel>
#include <QLineEdit>
#include <QPushButton>
#include <QFile>
#include <QJsonDocument>
#include <QJsonObject>
#include "selfdrive/ui/sunnypilot/qt/widgets/controls.h"
#include "selfdrive/ui/sunnypilot/qt/widgets/scrollview.h"

class ServerIpSettings : public QWidget {
  Q_OBJECT

public:
  explicit ServerIpSettings(QWidget* parent = nullptr);
  void showEvent(QShowEvent* event) override;
  bool eventFilter(QObject* watched, QEvent* event) override;

signals:
  void backPress();

private slots:
  void saveAdriPilotIp();
  void saveSicuemIp();
  void loadIps();

private:
  QVBoxLayout* main_layout;
  QLabel* adripilot_label;
  QLabel* sicuem_label;
  QLabel* adripilot_current_ip_label;
  QLabel* sicuem_current_ip_label;
  QLineEdit* adripilot_input;
  QLineEdit* sicuem_input;
  QPushButton* adripilot_save_btn;
  QPushButton* sicuem_save_btn;

  QString adripilot_config_path;
  QString sicuem_config_path;

  void setupAdriPilotSection();
  void setupSicuemSection();
  QString loadIpFromJson(const QString& file_path, const QString& key_path);
  bool saveIpToJson(const QString& file_path, const QString& key_path, const QString& ip);
};

