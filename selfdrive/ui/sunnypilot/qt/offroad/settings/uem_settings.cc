#include "selfdrive/ui/sunnypilot/qt/offroad/settings/uem_settings.h"
#include <tuple>
#include <vector>

#include "common/model.h"

UemPanel::UemPanel(QWidget *parent, int edit) : QFrame(parent) {
  main_layout = new QStackedLayout(this);


  ListWidgetSP *list = new ListWidgetSP(this, false);
  // Encabezado principal
  {
    QWidget *header = new QWidget(this);
    QVBoxLayout *hl = new QVBoxLayout(header);
    hl->setContentsMargins(30, 20, 30, 10);
    QLabel *title = new QLabel(tr("Configuración UEM"), header);
    title->setStyleSheet("font-size: 70px; font-weight: 700; color: white;");
    QLabel *subtitle = new QLabel(tr("Ajustes y utilidades del sistema UEM"), header);
    subtitle->setStyleSheet("font-size: 45px; color: #BDBDBD;");
    hl->addWidget(title);
    hl->addWidget(subtitle);
    list->addItem(header);
    list->addItem(horizontal_line());
  }
  std::vector<std::tuple<QString, QString, QString, QString>> toggle_defs{
    {
      "telemetria_uem",
      tr("TELEMETRIA UEM"),
      tr("EXPLICACION TELEMETRIA UEM"),
      "../assets/offroad/icon_blank.png",
    },
    {
      "c_carril",
      tr("FUNC CAMBIO CARRIL"),
      tr("EXPL CC"),
      "../assets/offroad/icon_blank.png",
    },
    {
  "show_blindspot",
  tr("MOSTRAR ÁNGULO MUERTO"),
  tr("Muestra estado de ángulo muerto en AnnotatedCamera."),
  "../assets/offroad/icon_blank.png",
    },
  {
  "sic_adelantar_bsm",
  tr("ACTIVAR ADELANTAR (con BSM)"),
  tr("Usar BSM para adelantar automáticamente."),
  "../assets/offroad/icon_blank.png",
},
{
  "sic_adelantar_nobsm",
  tr("ACTIVAR ADELANTAR (sin BSM)"),
  tr("Adelantamiento automático sin usar BSM."),
  "../assets/offroad/icon_blank.png",
},

    /**
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
    }*/
  };

  // Subpanel para TELEMETRIA UEM
  SubPanelButton *madsSettings = new SubPanelButton(tr("Conf. TELEMETRIA UEM"));
  madsSettings->setObjectName("mads_btn");
  QVBoxLayout* madsSettingsLayout = new QVBoxLayout;
  madsSettingsLayout->setContentsMargins(0, 0, 0, 30);
  madsSettingsLayout->addWidget(madsSettings);

  // Crear instancia de TelUemSettings y agregarla al layout
  mads_settings = new TelUemSettings(this);  // Instancia de TelUemSettings
  main_layout->addWidget(mads_settings);     // AÑADIR TelUemSettings AL QStackedLayout

  // Subpanel para Configuración de IPs de Servidores
  SubPanelButton *serverIpSettingsBtn = new SubPanelButton(tr("Conf. IP Servidores"));
  serverIpSettingsBtn->setObjectName("server_ip_btn");
  QVBoxLayout* serverIpSettingsLayout = new QVBoxLayout;
  serverIpSettingsLayout->setContentsMargins(0, 0, 0, 30);
  serverIpSettingsLayout->addWidget(serverIpSettingsBtn);

  // Crear instancia de ServerIpSettings y agregarla al layout
  server_ip_settings = new ServerIpSettings(this);
  main_layout->addWidget(server_ip_settings);

/*
SubPanelButton *madsSettings2 = new SubPanelButton(tr("INFO SOFTWARE UEM"));
  madsSettings2->setObjectName("mads_btn2");
  QVBoxLayout* madsSettingsLayout2 = new QVBoxLayout;

  madsSettingsLayout2->setContentsMargins(0, 0, 0, 30);
  madsSettingsLayout2->addWidget(madsSettings2);

  // Crear instancia de TelUemSettings y agregarla al layout
  mads_settings2 = new InfoUem(this);  // Instancia de TelUemSettings
  main_layout->addWidget(mads_settings2);     // AÑADIR TelUemSettings AL QStackedLayout


SubPanelButton *madsSettings3 = new SubPanelButton(tr("Sender UEM"));
  madsSettings3->setObjectName("mads_btn3");
  QVBoxLayout* madsSettingsLayout3 = new QVBoxLayout;

  madsSettingsLayout3->setContentsMargins(0, 0, 0, 30);
  madsSettingsLayout3->addWidget(madsSettings3);

  // Crear instancia de TelUemSettings y agregarla al layout
  mads_settings3 = new SenderUem(this);  // Instancia de TelUemSettings
  main_layout->addWidget(mads_settings3);     // AÑADIR TelUemSettings AL QStackedLayout

*/

  connect(madsSettings, &QPushButton::clicked, [=]() {
    scrollView->setLastScrollPosition();
    main_layout->setCurrentWidget(mads_settings);  // Cambiar al panel de TelUemSettings
  });
/*
  connect(madsSettings2, &QPushButton::clicked, [=]() {
    scrollView->setLastScrollPosition();
    main_layout->setCurrentWidget(mads_settings2);  // Cambiar al panel de TelUemSettings
  });

  connect(madsSettings3, &QPushButton::clicked, [=]() {
    scrollView->setLastScrollPosition();
    main_layout->setCurrentWidget(mads_settings3);  // Cambiar al panel de TelUemSettings
  });
*/
  // Conectar el evento backPress para regresar a la pantalla principal
  connect(mads_settings, &TelUemSettings::backPress, [=]() {
    scrollView->restoreScrollPosition();
    main_layout->setCurrentWidget(sunnypilotScreen);  // Volver a la pantalla principal
  });

  // Conectar el botón de configuración de IPs
  connect(serverIpSettingsBtn, &QPushButton::clicked, [=]() {
    scrollView->setLastScrollPosition();
    main_layout->setCurrentWidget(server_ip_settings);  // Cambiar al panel de ServerIpSettings
  });

  // Conectar el evento backPress de ServerIpSettings para regresar a la pantalla principal
  connect(server_ip_settings, &ServerIpSettings::backPress, [=]() {
    scrollView->restoreScrollPosition();
    main_layout->setCurrentWidget(sunnypilotScreen);  // Volver a la pantalla principal
  });

/*
    connect(mads_settings2, &InfoUem::backPress, [=]() {
    scrollView->restoreScrollPosition();
    main_layout->setCurrentWidget(sunnypilotScreen);  // Volver a la pantalla principal
  });

     connect(mads_settings3, &SenderUem::backPress, [=]() {
        scrollView->restoreScrollPosition();
        main_layout->setCurrentWidget(sunnypilotScreen);  // Volver a la pantalla principal
      });
*/

  // Sección: Funcionalidad
  {
    QWidget *section = new QWidget(this);
    QHBoxLayout *sl = new QHBoxLayout(section);
    sl->setContentsMargins(30, 10, 30, 0);
    QLabel *label = new QLabel(tr("Funciones"), section);
    label->setStyleSheet("font-size: 55px; font-weight: 600; color: #E0E0E0;");
    sl->addWidget(label, 0, Qt::AlignLeft);
    sl->addStretch(1);
    list->addItem(section);
  }

  // Añadir toggles y el botón de "Conf. TELEMETRIA UEM"
  for (auto &[param, title, desc, icon] : toggle_defs) {



    auto toggle = new ParamControlSP(param, title, desc, icon, this);
    list->addItem(toggle);
    toggles[param.toStdString()] = toggle;


  if (param == "sic_adelantar_bsm") {
  connect(toggle, &ToggleControlSP::toggleFlipped, [=](bool state) {
    if (state) {
      toggles["sic_adelantar_nobsm"]->setEnabled(false);
      toggles["sic_adelantar_nobsm"]->setValue("0");  // ✅ usar QString
    } else {
      toggles["sic_adelantar_nobsm"]->setEnabled(true);
    }
  });
}

    if (param == "sic_adelantar_nobsm") {
      connect(toggle, &ToggleControlSP::toggleFlipped, [=](bool state) {
        if (state) {
          toggles["sic_adelantar_bsm"]->setEnabled(false);
          toggles["sic_adelantar_bsm"]->setValue("0");  // ✅ usar QString
        } else {
          toggles["sic_adelantar_bsm"]->setEnabled(true);
        }
      });
    }



    if (param == "telemetria_uem") {
      list->addItem(madsSettingsLayout);  // Añadir el botón debajo del toggle de TELEMETRIA UEM
      // Sección: Configuración
      list->addItem(horizontal_line());
      QWidget *section = new QWidget(this);
      QHBoxLayout *sl = new QHBoxLayout(section);
      sl->setContentsMargins(30, 0, 30, 0);
      QLabel *label = new QLabel(tr("Configuración"), section);
      label->setStyleSheet("font-size: 55px; font-weight: 600; color: #E0E0E0;");
      sl->addWidget(label, 0, Qt::AlignLeft);
      sl->addStretch(1);
      list->addItem(section);
      list->addItem(serverIpSettingsLayout);  // Añadir el botón de configuración de IPs
    }
     //list->addItem(madsSettingsLayout3);  // Añadir el botón debajo del toggle de TELEMETRIA UEM
      list->addItem(horizontal_line());   // Separador
     // list->addItem(madsSettingsLayout2);  // Añadir el botón debajo del toggle de TELEMETRIA UEM


  }

  sunnypilotScreen = new QWidget(this);
  QVBoxLayout* vlayout = new QVBoxLayout(sunnypilotScreen);
  vlayout->setContentsMargins(0, 0, 50, 20);
  scrollView = new ScrollViewSP(list, this);
  vlayout->addWidget(scrollView, 1);
  main_layout->addWidget(sunnypilotScreen);  // AÑADIR la pantalla principal al layout

  // Establecer la pantalla principal como la pantalla predeterminada
  main_layout->setCurrentWidget(sunnypilotScreen);
connect(toggles["telemetria_uem"], &ToggleControlSP::toggleFlipped, [=](bool state) {
    madsSettings->setEnabled(state);
  });
    madsSettings->setEnabled(toggles["telemetria_uem"]->isToggled());

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
    #back_btn:pressed { background-color: #4a4a4a; }

    /* Estilo de botones de subpanel */
    SubPanelButton {
      font-size: 55px;
      font-weight: 600;
    }
  )");
}

void UemPanel::showEvent(QShowEvent *event) {
  updateToggles();
}

void UemPanel::hideEvent(QHideEvent *event) {
  main_layout->setCurrentWidget(sunnypilotScreen);  // Volver a la pantalla principal al ocultar
}

void UemPanel::updateToggles() {


  if (!isVisible()) {
    return;
  }
}
