{
  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";

  outputs = {
    self,
    nixpkgs,
  }: let
    forAllSystems = function:
      nixpkgs.lib.genAttrs [
        "x86_64-linux"
        "aarch64-linux"
      ] (system:
        function {
          inherit system;
          pkgs = nixpkgs.legacyPackages.${system};
        });
  in {
    devShells = forAllSystems ({
      pkgs,
      system,
    }: {
      default = pkgs.mkShell {
        inputsFrom = [self.packages.${system}.ilo];

        env.LD_LIBRARY_PATH = pkgs.lib.makeLibraryPath [
          pkgs.stdenv.cc.cc
        ];

        packages = with pkgs; [
          stdenv.cc.cc.lib
          xclip
          scom
        ];
      };
    });

    formatter = forAllSystems ({pkgs, ...}: pkgs.alejandra);

    packages = forAllSystems ({
      pkgs,
      system,
    }: {
      ilo = pkgs.python3.pkgs.callPackage ./nix/ilo.nix {
        inherit (self.packages.${system}) keyboard-crossplatform;
      };

      keyboard-crossplatform =
        pkgs.python3.pkgs.callPackage
        ./nix/keyboard-crossplatform.nix {};
    });
  };
}
