# Navi

TUI app navigator and launcher for Hyprland - since my terminal is already configured.

## Install 

### pipx
```bash
pipx install git+https://github.com/janthmueller/navi.git
```

## Hyprland Conf:

```conf
bind = $mainMod, D, exec, ghostty --class=com.janthmueller.navi --command=navi
windowrulev2 = float, class:com.janthmueller.navi
windowrulev2 = size 400 400, class:com.janthmueller.navi
windowrulev2 = center, class:com.janthmueller.navi
```

## TODO
- Workspace Naviagtion by App Names 
- Browser Tab Navigation. Expose Tab Info from (Zen) Browser
- Either here or separate TUI: Status Info like time, network etc.
