{
  description = "Nix Flake package for smount";
  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
  outputs = { self, nixpkgs }:
    let
      pkgName = "smount";
      supportedSystems = [ "x86_64-linux" "x86_64-darwin" "aarch64-linux" "aarch64-darwin" ];
      forAllSystems = nixpkgs.lib.genAttrs supportedSystems;
      nixpkgsFor = forAllSystems (system: import nixpkgs { inherit system; });
    in
    {
      formatter.x86_64-linux = nixpkgs.legacyPackages.x86_64-linux.nixpkgs-fmt;
      packages = forAllSystems (system:
        let
          pkgs = nixpkgsFor.${system};
          pp = pkgs.python3Packages;
        in
        {
          ${pkgName} = pp.buildPythonApplication rec {
            pname = pkgName;
            src = ./.;
            propagatedBuildInputs = [ pp.pyyaml ];
            nativeCheckInputs = [ pp.pyfakefs ];
            version = "0.8";
            doCheck = false; # To be fixed

            prePatch = ''
              substituteInPlace setup.py \
              --replace "pyyml" "pyyaml"
            '';
          };
        }
      );
      devShells = forAllSystems (system:
        let
          pkgs = nixpkgsFor.${system};
          pp = pkgs.python3Packages;
        in
        {
          default = pkgs.mkShell {
            buildInputs = with pp; [ pkgs.python3 pyyaml pyfakefs pytest pylint ipython ];
          };
        }
      );
      defaultPackage = forAllSystems (system: self.packages.${system}.${pkgName});
    };
}
