let
  nixpkgs = fetchTarball "channel:nixos-20.03";
  pkgs = import nixpkgs {};

  recipe = { python38, fetchurl }:
    with python38.pkgs;

    buildPythonApplication rec {
      pname = "smount";
      version = "0.3";

      propagatedBuildInputs = [ pyyaml ];

      prePatch = ''
          substituteInPlace setup.py \
          --replace "pyyml" "pyyaml"
          '';

      src = fetchurl {
        url= "https://github.com/Lqp1/smount/archive/refs/tags/v${version}.tar.gz";
        sha256 = "8f9f44408394b505a92703e312676865394816a270e64c7a50b92d8fc630aed0";
      };
    };

in pkgs.callPackage recipe {}


