let
  nixpkgs = fetchTarball "channel:nixos-22.11";
  pkgs = import nixpkgs {};

  recipe = { python39, fetchurl }:
    with python39.pkgs;

    buildPythonApplication rec {
      pname = "smount";
      version = "0.7";

      propagatedBuildInputs = [ pyyaml ];
      nativeCheckInputs = [ pyfakefs ];
      doCheck = false; # To be fixed

      prePatch = ''
          substituteInPlace setup.py \
          --replace "pyyml" "pyyaml"
          '';

      src = fetchurl {
        url= "https://github.com/Lqp1/smount/archive/refs/tags/v${version}.tar.gz";
        sha256 = "cfdac304b4ab66068b2e0d0fe04b1ed24716148db8deab1790a9ba911186390e";
      };
    };

in pkgs.callPackage recipe {}


