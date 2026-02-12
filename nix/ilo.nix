{
  lib,
  buildPythonPackage,
  setuptools,
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
  version = "0.0.62";
  pyproject = true;

  src = ./..;

  build-system = [setuptools];

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

  meta = {
    description = "Control ilo robot using python command";
    license = lib.licenses.mit;
  };
}
