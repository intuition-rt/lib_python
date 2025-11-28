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
}:
buildPythonPackage {
  pname = "ilo";
  version = "0.0.61";
  pyproject = true;

  src = ./../ilo;

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
  ];

  meta = {
    description = "Control ilo robot using python command";
    license = lib.licenses.mit;
  };
}
