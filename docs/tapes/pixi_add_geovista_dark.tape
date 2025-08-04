#!/usr/bin/env -S pixi exec -c https://prefix.dev/conda-forge -s vhs -s ffmpeg -s ttyd -- vhs

Output pixi_add_geovista_dark.gif

Require pixi

Set Shell bash
Set FontSize 32
Set Width 1920
Set Height 800
Set Theme "rose-pine-moon"
Set TypingSpeed 40ms
Set CursorBlink false

Env PS1 "> "

Hide
Type "rm -rf .pixi"
Enter
Wait+Line@120s
Type "rm -rf myenv"
Enter
Wait+Line@120s
Type "clear"
Enter
Wait+Line
Sleep 1
Show

Type "pixi init myenv"
Sleep 500ms
Enter
Wait+Line
Sleep 1

Type "cd myenv"
Sleep 500ms
Enter
Wait+Line
Sleep 1

Type "pixi add geovista"
Sleep 500ms
Enter
Wait+Line@180s
Sleep 3

Type "clear"
Sleep 500ms
Enter
Wait+Line
Sleep 1

Type "pixi shell"
Sleep 500ms
Enter
Wait+Line
Sleep 2

Type "python"
Sleep 500ms
Enter
Wait+Line />>>/
Sleep 1

Type "import geovista"
Sleep 500ms
Enter
Wait+Line />>>/

Sleep 5
