let
  nixpkgs = fetchTarball "channel:nixos-22.11";
  pkgs = import nixpkgs {};

  recipe = { python39, fetchurl }:
    with python39.pkgs;

    buildPythonApplication rec {
      pname = "smount";
      version = "0.5";

      propagatedBuildInputs = [ pyyaml ];

      prePatch = ''
          substituteInPlace setup.py \
          --replace "pyyml" "pyyaml"
          '';

      src = fetchurl {
        url= "https://github.com/Lqp1/smount/archive/refs/tags/v${version}.tar.gz";
        sha256 = "02fa0d88af23db8783cade056e8b8f9235c0aacc05d0ab97731e268fe131d8ce";
      };
    };

in pkgs.callPackage recipe {}


