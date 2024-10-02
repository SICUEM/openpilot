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

Last updated: July 29, 2024
***/

#include "selfdrive/ui/sunnypilot/qt/offroad/settings/uem_settings.h"
#include <tuple>
#include <vector>

#include "common/model.h"

UemPanel::UemPanel(QWidget *parent, int edit) : QFrame(parent) {
  main_layout = new QStackedLayout(this);

  ListWidgetSP *list = new ListWidgetSP(this, false);
  std::vector<std::tuple<QString, QString, QString, QString>> toggle_defs{
    {
      "telemetria_uem",
      tr("TELEMETRIA UEM"),
      tr("EXPLICACION TELEMETRIA UEM"),
      "../assets/offroad/icon_blank.png",
    },
    {
      "toggle_op1",
      tr("op1"),
      tr(""),
      "../assets/offroad/icon_blank.png",
    },
    {
      "toggle_op2",
      tr("op2"),
      tr(""),
      "../assets/offroad/icon_blank.png",
    },
    {
      "toggle_op3",
      tr("op3"),
      tr(""),
      "../assets/offroad/icon_blank.png",
    }
  };

  // Subpanel para TELEMETRIA UEM
  SubPanelButton *madsSettings = new SubPanelButton(tr("Conf. TELEMETRIA UEM"));
  madsSettings->setObjectName("mads_btn");
  QVBoxLayout* madsSettingsLayout = new QVBoxLayout;
  madsSettingsLayout->setContentsMargins(0, 0, 0, 30);
  madsSettingsLayout->addWidget(madsSettings);

  connect(madsSettings, &QPushButton::clicked, [=]() {
    scrollView->setLastScrollPosition();
    main_layout->setCurrentWidget(mads_settings);
  });

  mads_settings = new TelUemSettings(this, edit);  // Instancia de TelUemSettings
  connect(mads_settings, &TelUemSettings::backPress, [=]() {
    scrollView->restoreScrollPosition();
    main_layout->setCurrentWidget(sunnypilotScreen);
  });

  for (auto &[param, title, desc, icon] : toggle_defs) {
    auto toggle = new ParamControlSP(param, title, desc, icon, this);
    list->addItem(toggle);
    toggles[param.toStdString()] = toggle;

    if (param == "telemetria_uem") {
      list->addItem(madsSettingsLayout);
      list->addItem(horizontal_line());
    }
  }

  sunnypilotScreen = new QWidget(this);
  QVBoxLayout* vlayout = new QVBoxLayout(sunnypilotScreen);
  vlayout->setContentsMargins(0, 0, 50, 20);
  scrollView = new ScrollViewSP(list, this);
  vlayout->addWidget(scrollView, 1);
  main_layout->addWidget(sunnypilotScreen);

  setStyleSheet(R"(
    #back_btn {
      font-size: 50px;
      margin: 0px;
      padding: 15px;
      border-width: 0;
      border-radius: 30px;
      color: #dddddd;
      background-color: #393939;
    }
    #back_btn:pressed {
      background-color:  #4a4a4a;
    }
  )");

  main_layout->setCurrentWidget(sunnypilotScreen);
}

void UemPanel::showEvent(QShowEvent *event) {
  updateToggles();
}

void UemPanel::hideEvent(QHideEvent *event) {
  main_layout->setCurrentWidget(sunnypilotScreen);
}

void UemPanel::updateToggles() {
  if (!isVisible()) {
    return;
  }
}
