let
  nixpkgs = fetchTarball "channel:nixos-20.03";
  pkgs = import nixpkgs {};

  recipe = { python38, fetchurl }:
    with python38.pkgs;

    buildPythonApplication rec {
      pname = "smount";
      version = "0.2";

      propagatedBuildInputs = [ pyyaml ];

      prePatch = ''
          substituteInPlace setup.py \
          --replace "pyyml" "pyyaml"
          '';

      src = fetchurl {
        url= "https://github.com/Lqp1/smount/archive/refs/tags/v${version}.tar.gz";
        sha256 = "c893047f5739bc52103fa8fc3e39b75267f0014d4f088e5f34756dc0bde72634";
      };
    };

in pkgs.callPackage recipe {}


