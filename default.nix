let
  nixpkgs = fetchTarball {
      url = "channel:nixpkgs-unstable";
  };
  pkgs = import nixpkgs {};

  recipe = { python3, fetchurl }:
    with python3.pkgs;

    buildPythonApplication rec {
      pname = "smount";
      version = "0.9";
      pyproject = true;

      propagatedBuildInputs = [ pyyaml ];
      nativeBuildInputs = [ setuptools ];
      nativeCheckInputs = [ pyfakefs ];
      doCheck = true;

      prePatch = ''
          substituteInPlace setup.py \
          --replace "pyyml" "pyyaml"
          '';

      src = fetchurl {
        url= "https://github.com/Lqp1/smount/archive/refs/tags/v${version}.tar.gz";
        sha256 = "61828217acb2fe67d7fd54a6fd1685cf91b3d5f549f1e0e0e5e5209c27e88b06";
      };
    };

in pkgs.callPackage recipe {}


