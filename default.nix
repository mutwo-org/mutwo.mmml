with import <nixpkgs> {};
with pkgs.python3Packages;

let

  mutwo-core-archive = builtins.fetchTarball "https://github.com/mutwo-org/mutwo.core/archive/97aea97f996973955889630c437ceaea405ea0a7.tar.gz";
  mutwo-core = import (mutwo-core-archive + "/default.nix");

  mutwo-music-archive = builtins.fetchTarball "https://github.com/mutwo-org/mutwo.music/archive/4e4369c1c9bb599f47ec65eb86f87e9179e17d97.tar.gz";
  mutwo-music = import (mutwo-music-archive + "/default.nix");

in

  buildPythonPackage rec {
    name = "mutwo.mmml";
    src = fetchFromGitHub {
      owner = "mutwo-org";
      repo = name;
      rev = "c2cc56052a97df7291c4a51b6c3ad31e45fcadcb";
      sha256 = "sha256-cqVXtHE60bqdN7YHzIBswUY2pFMKPon/Yrpno5lSrWk=";
    };
    propagatedBuildInputs = [
      mutwo-core
      mutwo-music
    ];
    doCheck = true;
  }
