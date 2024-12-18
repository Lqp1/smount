let
  nixpkgs = fetchTarball {
      url = "channel:nixos-24.11";
      sha256 = "sha256:0nvd0nfv7ayw4gn916r4bgxk76np6w41w72izich6zvygdn8agwp";
  };
  pkgs = import nixpkgs {};

  recipe = { python312, fetchurl }:
    with python312.pkgs;

    buildPythonApplication rec {
      pname = "smount";
      version = "0.8";

      propagatedBuildInputs = [ pyyaml ];
      nativeCheckInputs = [ pyfakefs ];
      doCheck = false; # To be fixed

      prePatch = ''
          substituteInPlace setup.py \
          --replace "pyyml" "pyyaml"
          '';

      src = fetchurl {
        url= "https://github.com/Lqp1/smount/archive/refs/tags/v${version}.tar.gz";
        sha256 = "1a0955aada716d46750a2c16f0829246c8395ca5c33bfe96f3c6d253b52e5974";
      };
    };

in pkgs.callPackage recipe {}


