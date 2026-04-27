#include <clocale>
#include <sys/resource.h>

#include <QApplication>
#include <QLocale>
#include <QTranslator>

#include "system/hardware/hw.h"
#include "selfdrive/ui/qt/qt_window.h"
#include "selfdrive/ui/qt/util.h"

#ifdef SUNNYPILOT
#include "selfdrive/ui/sunnypilot/qt/window.h"
#define MainWindow MainWindowSP
#else
#include "selfdrive/ui/qt/window.h"
#endif

int main(int argc, char *argv[]) {
  setpriority(PRIO_PROCESS, 0, -20);

  qInstallMessageHandler(swagLogMessageHandler);
  initApp(argc, argv);

  QTranslator translator;
  QString translation_file = QString::fromStdString(Params().get("LanguageSetting"));
  if (!translator.load(QString(":/%1").arg(translation_file)) && translation_file.length()) {
    qCritical() << "Failed to load translation file:" << translation_file;
  }

  QApplication a(argc, argv);

  // Forzar parseo numerico estilo C en TODO el proceso UI. CRITICO ponerlo
  // DESPUES de construir QApplication: el constructor de QApplication llama
  // internamente a setlocale(LC_ALL, "") y pisa cualquier locale anterior, asi
  // que si lo poniamos antes Qt lo restauraba a es_ES y std::stof("0.5") seguia
  // dando 0. Solo afecta a numeros (LC_NUMERIC); idioma/fecha/orden se mantienen.
  std::setlocale(LC_NUMERIC, "C");
  // Y para Qt mismo (QString::toFloat, QLocale::toFloat), forzamos C-locale.
  QLocale::setDefault(QLocale::c());

  a.installTranslator(&translator);
  MainWindow w;
  setMainWindow(&w);
  a.installEventFilter(&w);
  return a.exec();
}
