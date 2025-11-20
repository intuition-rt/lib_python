{
  lib,
  buildPythonPackage,
  setuptools,
  fetchPypi,
  keyboard,
}:
buildPythonPackage rec {
  pname = "keyboard-crossplatform";
  version = "0.1.0";
  pyproject = true;

  src = fetchPypi {
    pname = "keyboard_crossplatform";
    inherit version;
    hash = "sha256-UWP9VZQbVyp7hoRS9qxUf4fmm8tIR3LeD3S+eTCnmho=";
  };

  build-system = [setuptools];

  dependencies = [keyboard];

  meta = {
    description = "Control ilo robot using python command";
    license = lib.licenses.mit;
  };
}
