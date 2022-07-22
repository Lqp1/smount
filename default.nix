let
  nixpkgs = fetchTarball "channel:nixos-20.03";
  pkgs = import nixpkgs {};

  recipe = { python38, fetchurl }:
    with python38.pkgs;

    buildPythonApplication rec {
      pname = "smount";
      version = "0.4";

      propagatedBuildInputs = [ pyyaml ];

      prePatch = ''
          substituteInPlace setup.py \
          --replace "pyyml" "pyyaml"
          '';

      src = fetchurl {
        url= "https://github.com/Lqp1/smount/archive/refs/tags/v${version}.tar.gz";
        sha256 = "e85cecb8f8491aff8cf67976c955d866b639efc01854e385012ba5a81150dfbf";
      };
    };

in pkgs.callPackage recipe {}


