{
  lib,
  buildPythonPackage,
  hatchling,
  pyserial,
  psutil,
  websocket-client,
  bleak,
  prettytable,
  pyperclip,
  keyboard-crossplatform,
  requests,
  keyboard,
  numpy,
  matplotlib,
  tkinter,
  webcolors,
}:
buildPythonPackage {
  pname = "ilo";
  version = "0.1.2";
  pyproject = true;

  src = ./..;

  build-system = [hatchling];

  dependencies = [
    bleak
    pyserial
    psutil
    websocket-client
    prettytable
    pyperclip
    keyboard-crossplatform
    requests
    keyboard
    numpy
    matplotlib
    tkinter
    webcolors
  ];

  pythonRelaxDeps = [
    "bleak"
    "requests"
    "websocket-client"
  ];

  meta = {
    description = "Control ilo robot using python command";
    license = lib.licenses.mit;
  };
}
