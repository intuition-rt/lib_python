{
  lib,
  buildPythonPackage,
  setuptools,
  fetchPypi,
  keyboard,
}:
buildPythonPackage rec {
  pname = "keyboard-crossplatform";
  version = "0.2.0";
  pyproject = true;

  src = fetchPypi {
    pname = "keyboard_crossplatform";
    inherit version;
    hash = "sha256-9OLjpN0uspAdlKNCV8wnK+SxehcZ4R/K8/MtgfoI+uU=";
  };

  build-system = [setuptools];

  dependencies = [keyboard];

  meta = {
    description = "Control ilo robot using python command";
    license = lib.licenses.mit;
  };
}
