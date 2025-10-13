# Navi

TUI app navigator and launcher for Hyprland - my terminal is already configured.

## Install 
### pipx
```bash
pipx install git+https://github.com/janthmueller/navi.git@v1.0.3
```
### Home Manager

```nix
{ pkgs, ... }:

let
  navi = pkgs.python3Packages.buildPythonPackage rec {
    pname = "navi";
    version = "1.0.3";

    src = pkgs.fetchurl {
      url = "https://github.com/janthmueller/navi/archive/refs/tags/v${version}.tar.gz";
      sha256 ="1shk7vr8jbcjvz2fyb2fv4765sdh00wdccrx59cd036x7mjfh4in";
    };

    pyproject = true;
    build-system = [ pkgs.python3Packages.setuptools ];


    pythonImportsCheck = [ "navi" ];
  };
in
{
  home.packages = [ navi ];
}
```


## Hyprland Conf:

```conf

bind = $mainMod, D, exec, ghostty --class=com.janthmueller.navi --command=navi
windowrulev2 = float, class:com.janthmueller.navi
windowrulev2 = size 400 400, class:com.janthmueller.navi
windowrulev2 = center, class:com.janthmueller.navi
```
