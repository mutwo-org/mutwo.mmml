with import <nixpkgs> {};
with pkgs.python310Packages;

let

  mutwo-core-archive = builtins.fetchTarball "https://github.com/mutwo-org/mutwo.core/archive/61ebb657ef5806eb067f5df6885254fdbae8f44c.tar.gz";
  mutwo-core = import (mutwo-core-archive + "/default.nix");

  mutwo-music-archive = builtins.fetchTarball "https://github.com/mutwo-org/mutwo.music/archive/d90b6db7d433d64c25f039adcd6b41075c05c013.tar.gz";
  mutwo-music = import (mutwo-music-archive + "/default.nix");

in

  buildPythonPackage rec {
    name = "mutwo.mmml";
    src = fetchFromGitHub {
      owner = "mutwo-org";
      repo = name;
      rev = "b57f0cd2c91a08f75e79312e90aa455347a3b8ad";
      sha256 = "sha256-xVVC7EXp09n+5LR9CwreOgEWRGlJOc1rSkN4elp580Q=";
    };
    propagatedBuildInputs = [
      mutwo-core
      mutwo-music
    ];
    doCheck = true;
  }
