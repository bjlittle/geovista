#!/usr/bin/env -S pixi exec -c https://prefix.dev/conda-forge -s vhs -s ffmpeg -s ttyd -- vhs

Output pixi_shell_geovista_dark.gif

Require pixi

Set Shell bash
Set FontSize 32
Set Width 1920
Set Height 600
Set Theme "rose-pine-moon"
Set TypingSpeed 40ms
Set CursorBlink false

Env PS1 "> "

Type "pixi shell --environment geovista"
Sleep 500ms
Enter
Wait+Line@120s

Type "pre-commit install"
Sleep 500ms
Enter
Wait+Line
Enter

Type "python"
Sleep 500ms
Enter
Wait+Line />>>/

Type "import geovista"
Sleep 500ms
Enter
Wait+Line />>>/

Sleep 5
