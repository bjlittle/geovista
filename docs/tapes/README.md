# 📼 VHS Tapes

This directory contains [VHS](https://github.com/charmbracelet/vhs) scripts to
record the CLI in a virtual terminal.

The ``tape`` scripts are self-packaged with ``pixi`` and may be run directly
on the command line e.g.,

```shell

$ ./pixi_shell_geovista_dark.tape
```

Or they can be run with ``vhs`` e.g.,

```shell
$ pixi shell
$ vhs pixi_shell_geovista_dark.tape
```

If the resulting ``gif`` is large then use ``vhs`` to publish it
to the cloud and reference the provided URL e.g.,

```shell
$ pixi shell
$ vhs publish pixi_shell_geovista_dark.tape
```
Otherwise, smaller GIFs may be stored in the ``docs/tapes`` directory.

Ensure to create both ``light`` and ``dark`` tape versions using the
``rose-pine-dawn`` and ``rose-pine-moon`` themes respectively.
