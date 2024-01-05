{ sources ? import ./nix/sources.nix, rsources ? import (sources.mutwo-nix.outPath + "/nix/sources.nix"), pkgs ? import rsources.nixpkgs {}}:

with pkgs;
with pkgs.python310Packages;

let

  mutwo-music = import (sources.mutwo-nix.outPath + "/mutwo.music/default.nix") {};

in

  buildPythonPackage rec {
    name = "mutwo.mmml";
    src = ./.;
    nativeCheckInputs = [ pytest ];
    checkInputs = [ pytest ];
    propagatedBuildInputs = [ 
      mutwo-music
      chevron
    ];
    checkPhase = ''
      runHook preCheck
      # pytest
      # pytest --doctest-modules mutwo
      runHook postCheck
    '';
    doCheck = true;
  }
