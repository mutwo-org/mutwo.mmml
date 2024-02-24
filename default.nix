let
  sourcesTarball = fetchTarball "https://github.com/mutwo-org/mutwo-nix/archive/refs/heads/main.tar.gz";
  mutwo-mmml = import (sourcesTarball + "/mutwo.mmml/default.nix") {};
  mutwo-mmml-local = mutwo-mmml.overrideAttrs (
    finalAttrs: previousAttrs: {
       src = ./.;
    }
  );
in
  mutwo-mmml-local
