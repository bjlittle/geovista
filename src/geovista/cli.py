# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Command line interface (CLI) support for the :mod:`geovista` entry-point.

Notes
-----
.. versionadded:: 0.1.0

"""

from __future__ import annotations

import importlib
import pathlib
from shutil import rmtree
from typing import TYPE_CHECKING
from warnings import warn

import click
from click_default_group import DefaultGroup
import lazy_loader as lazy

from ._version import version as __version__
from .cache import CACHE, GEOVISTA_POOCH_MUTE, pooch_mute
from .common import get_modules
from .config import resources
from .geoplotter import GeoPlotter
from .report import Report

if TYPE_CHECKING:
    from collections.abc import Iterable

# lazy import third-party dependencies
pooch = lazy.load("pooch")
pv = lazy.load("pyvista")

__all__ = ["main"]

CONTEXT_SETTINGS = {"help_option_names": ["-h", "--help"]}

ALL: str = "all"
NE_ROOT: str = "natural_earth"
NE_GROUPS: list[str] = sorted(["physical"])
NE_CHOICES: list[str] = [ALL]
NE_CHOICES.extend(NE_GROUPS)

FG_COLOUR: str = "cyan"

EXAMPLES: list[str] = [ALL, *get_modules("geovista.examples")]


def _download_group(
    fnames: list[str],
    decompress: bool | None = False,
    name: str | None = None,
    fg_colour: str | None = None,
    summary: bool | None = True,
) -> None:
    """Download and populate the geovista cache with requested assets.

    Only assets which are not in the cache will be downloaded and verified via
    :mod:`pooch`.

    Parameters
    ----------
    fnames : list of str
        The list of assets to be downloaded.
    decompress : bool, default=False
        Decompress the downloaded assets.
    name : str, optional
        The name of the asset collection within the cache e.g., raster or pantry.
    fg_colour : str, default="cyan"
        Foreground colour to highlight the asset name during download.
    summary : bool, default=True
        Whether to provide a download summary to the user.

    Notes
    -----
    .. versionadded:: 0.1.0

    """
    if fg_colour is None:
        fg_colour = FG_COLOUR

    name: str = "" if name is None else f"{name} "

    n_fnames: int = len(fnames)
    width: int = len(str(n_fnames))

    status = GEOVISTA_POOCH_MUTE
    pooch_mute(True)

    click.echo(f"Downloading {n_fnames} {name}registered asset{_plural(n_fnames)}:")
    for i, fname in enumerate(fnames):
        click.echo(f"[{i+1:0{width}d}/{n_fnames}] Downloading ", nl=False)
        click.secho(f"{fname} ", nl=False, fg=fg_colour)
        click.echo("... ", nl=False)
        processor = None
        name = pathlib.Path(fname)
        if decompress and (suffix := name.suffix) in pooch.Decompress.extensions:
            name = name.stem.removesuffix(suffix)
            processor = pooch.Decompress(method="auto", name=name)
        CACHE.fetch(fname, processor=processor)
        click.secho("done!", fg="green")

    if summary:
        click.echo("\nAssets are available in the cache directory ", nl=False)
        click.secho(f"{CACHE.abspath}", fg=fg_colour)
        click.echo("👍 All done!")

    pooch_mute(status)


def _groups() -> list[str]:
    """Filter examples for unique group names.

    Always contains the "all" group.

    Returns
    -------
    list of str
        The sorted list of unique example script groups.

    Notes
    -----
    .. versionadded:: 0.5.0

    """
    result = {ALL}

    for example in EXAMPLES[1:]:
        if "." in example:
            result.add(example.split(".")[0])

    return sorted(result)


def _plural(quantity: int) -> str:
    """Determine whether the provided `quantity`` is textually plural.

    Parameters
    ----------
    quantity : int
        The quantity under consideration.

    Returns
    -------
    str
        A "s" for a plural quantity, otherwise an empty string.

    Notes
    -----
    .. versionadded:: 0.1.0

    """
    return "s" if (quantity == 0 or quantity > 1) else ""


@click.group(
    cls=DefaultGroup,
    default="plot",
    default_if_no_args=True,
    invoke_without_command=True,
    context_settings=CONTEXT_SETTINGS,
)
@click.option(
    "-c",
    "--cache",
    is_flag=True,
    help="Show geovista cache directory.",
)
@click.option(
    "-r",
    "--report",
    is_flag=True,
    help="Show GPU and environment package report.",
)
@click.option(
    "-v",
    "--version",
    is_flag=True,
    help="Show geovista package version.",
)
def main(version: bool, report: bool, cache: bool) -> None:  # numpydoc ignore=PR01
    """To get help for geovista commands, simply use "geovista COMMAND --help"."""
    if version:
        click.echo("version ", nl=False)
        click.secho(f"{__version__}", fg=FG_COLOUR)

    if report:
        click.echo(Report())

    if cache:
        click.echo("cache directory ", nl=False)
        click.secho(f"{CACHE.abspath}", fg=FG_COLOUR)


@main.command(no_args_is_help=True)
@click.option(
    "-a",
    "--all",
    "pull",
    is_flag=True,
    help="Download all registered assets.",
)
@click.option(
    "-c",
    "--clean",
    is_flag=True,
    help="Delete all cached assets.",
)
@click.option(
    "-d",
    "--decompress",
    is_flag=True,
    help="Decompress all cached assets.",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Show URLs of registered assets.",
)
@click.option("-i", "--image", is_flag=True, help="Download image test assets.")
@click.option(
    "-l",
    "--list",
    "show",
    is_flag=True,
    help="Show names of registered assets.",
)
@click.option(
    "-ne",
    "--natural-earth",
    multiple=True,
    type=click.Choice(NE_CHOICES, case_sensitive=False),
    is_flag=False,
    flag_value=ALL,
    help="Download Natural Earth feature assets.",
)
@click.option("-o", "--operational", is_flag=True, help="Download all non-test assets.")
@click.option("-p", "--pantry", is_flag=True, help="Download sample data assets.")
@click.option(
    "-r",
    "--raster",
    is_flag=True,
    help="Download raster assets.",
)
@click.option(
    "-t",
    "--target",
    type=click.Path(file_okay=False, resolve_path=True, path_type=pathlib.Path),
    help=f"Download target directory (default: {CACHE.abspath})",
)
@click.option(
    "-v",
    "--verify",
    is_flag=True,
    help="Verify availability of registered assets (no download).",
)
def download(
    pull: bool,
    clean: bool,
    decompress: bool,
    dry_run: bool,
    image: bool,
    show: bool,
    natural_earth: Iterable[str],
    operational: bool,
    pantry: bool,
    raster: bool,
    target: pathlib.Path | None,
    verify: bool,
) -> None:  # numpydoc ignore=PR01
    """Download and cache geovista assets (offline support)."""
    fnames: list[str] = sorted(CACHE.registry_files)

    if not fnames:
        click.secho("No assets are registered with geovista.", fg="red")
        return

    n_fnames: int = len(fnames)
    width: int = len(str(n_fnames))
    fg_colour: str = FG_COLOUR

    if clean:
        msg = "Are you sure you want to delete all cached geovista assets"
        if click.confirm(f"\n{msg}?", abort=True):
            target = resources["cache_dir"]

            if target.exists():
                if target.is_symlink():
                    rmtree(target.readlink())
                    target.unlink()
                else:
                    rmtree(target)

                click.echo("\nDeleted the cache directory ", nl=False)
                click.secho(f"{target}", fg=FG_COLOUR)
                click.echo("👍 All done!")
            else:
                click.echo("\nThere are no cached assets to delete.")

    if target:
        target.mkdir(exist_ok=True)
        previous_path = CACHE.path
        CACHE.path = target

    def collect(prefix: str) -> list[str]:
        """Filter the asset names with the provided `prefix`.

        Parameters
        ----------
        prefix : str
            The `prefix` to filter the asset names.

        Returns
        -------
        list of str
            The list of assets with the provided `prefix`.

        """
        return list(filter(lambda item: item.startswith(prefix), fnames))

    if pull:
        _download_group(fnames, decompress=decompress)
    elif operational:
        names = sorted(set(fnames) - set(collect("tests")))
        _download_group(names, decompress=decompress, name="operational")
    else:
        if image:
            name = "images"
            _download_group(collect(f"tests/{name}"), decompress=decompress, name=name)

        if pantry:
            name = "pantry"
            _download_group(collect(name), decompress=decompress, name=name)

        if natural_earth:
            if ALL in natural_earth:
                natural_earth = NE_GROUPS
            natural_earth = sorted(set(natural_earth))
            n_groups = len(natural_earth)
            for i, group in enumerate(natural_earth):
                prefix = f"{NE_ROOT}/{group}"
                name = f"Natural Earth {group}"
                _download_group(
                    collect(prefix),
                    decompress=decompress,
                    name=name,
                    summary=(i + 1 == n_groups),
                )

        if raster:
            name = "raster"
            _download_group(collect(name), decompress=decompress, name=name)

    if verify:
        unavailable = 0
        click.echo("Verifying remote availability of registered assets:")
        for i, fname in enumerate(fnames):
            click.echo(f"[{i+1:0{width}d}/{n_fnames}] ", nl=False)
            click.secho(f"{fname} ", nl=False, fg=fg_colour)
            click.echo("is ... ", nl=False)
            status, status_fg_colour = (
                ("available!", "green")
                if (available := CACHE.is_available(fname))
                else ("unavailable!", "red")
            )
            if not available:
                unavailable += 1
            click.secho(status, fg=status_fg_colour)

        if not unavailable:
            click.echo(f"\n{n_fnames} asset{_plural(n_fnames)} ", nl=False)
            click.secho("available", fg="green", nl=False)
            click.echo(".")
            click.echo("👍 All done!")
        else:
            click.echo("\n💥 ", nl=False)
            if unavailable == n_fnames:
                click.echo(f"{n_fnames} asset{_plural(n_fnames)} ", nl=False)
                click.secho("unavailable", fg="red", nl=False)
                click.echo(". Nuts!")
            else:
                available = n_fnames - unavailable
                click.echo(f"{available} asset{_plural(available)} ", nl=False)
                click.secho("available", fg="green", nl=False)
                click.echo(
                    f", but {unavailable} asset{_plural(unavailable)} ", nl=False
                )
                click.secho("unavailable", fg="red", nl=False)
                click.echo(". Dang!")

    if dry_run:
        click.echo("URLs of registered assets:")
        for i, fname in enumerate(fnames):
            click.echo(f"[{i+1:0{width}d}/{n_fnames}] ", nl=False)
            click.secho(f"{CACHE.get_url(fname)}", fg=fg_colour)
        click.echo("\n👍 All done!")

    if show:
        click.echo("Names of registered assets:")
        for i, fname in enumerate(fnames):
            click.echo(f"[{i+1:0{width}d}/{n_fnames}] ", nl=False)
            click.secho(f"{fname}", fg=fg_colour)
        click.echo("\n👍 All done!")

    if target:
        CACHE.path = previous_path


@main.command(no_args_is_help=True)
@click.option(
    "-a",
    "--all",
    "run_all",
    is_flag=True,
    help="Run all examples.",
)
@click.option("-g", "--groups", is_flag=True, help="Show available example groups.")
@click.option(
    "-l",
    "--list",
    "show",
    is_flag=True,
    help="Show available examples.",
)
@click.option(
    "-r",
    "--run",
    type=click.Choice(EXAMPLES, case_sensitive=False),
    is_flag=False,
    help="Run an example.",
)
@click.option(
    "--run-group",
    "run_group",
    type=click.Choice(_groups(), case_sensitive=False),
    is_flag=False,
    help="Run all examples in the group.",
)
@click.option(
    "-v",
    "--verbose",
    is_flag=True,
    help="Enable example diagnostics.",
)
def examples(
    run_all: bool, groups: bool, show: bool, run: str, run_group: str, verbose: bool
) -> None:  # numpydoc ignore=PR01
    """Execute a geovista example or group of examples."""
    # account for the initial "all" option
    n_examples = len(EXAMPLES) - 1

    if show:
        click.echo("Available examples:")
        width = len(str(n_examples))
        for i, script in enumerate(EXAMPLES[1:]):
            click.echo(f"[{i + 1:0{width}d}/{n_examples}] ", nl=False)
            click.secho(f"{script}", fg="green")
        click.echo("\n👍 All done!")
        return

    if groups:
        click.echo("Available example groups:")
        groups = _groups()
        n_groups = len(groups)
        width = len(str(n_groups))
        for i, group in enumerate(groups):
            click.echo(f"[{i + 1:0{width}d}/{n_groups}] ", nl=False)
            click.secho(f"{group}", fg="green")
        click.echo("\n👍 All done!")
        return

    run_all = ALL in (run, run_group) or run_all

    if run_all:
        for i, script in enumerate(EXAMPLES[1:]):
            msg = f"Running example {script!r} ({i+1} of {n_examples}) ..."
            click.secho(msg, fg="green")
            module = importlib.import_module(f"geovista.examples.{script}")
            if verbose:
                print(module.__doc__)
            try:
                module.main()
            except ImportError as err:
                warn(str(err), stacklevel=1)
        click.echo("\n👍 All done!")
        return

    if run_group:
        group = [script for script in EXAMPLES[1:] if script.startswith(run_group)]
        n_group = len(group)
        for i, script in enumerate(group):
            msg = f"Running {run_group!r} example {script!r} ({i+1} of {n_group}) ..."
            click.secho(msg, fg="green")
            module = importlib.import_module(f"geovista.examples.{script}")
            if verbose:
                print(module.__doc__)
            try:
                module.main()
            except ImportError as err:
                warn(str(err), stacklevel=1)
        click.echo("\n👍 All done!")
        return

    if run:
        msg = f"Running example {run!r} ..."
        click.secho(msg, fg="green")
        module = importlib.import_module(f"geovista.examples.{run}")
        if verbose:
            print(module.__doc__)
        module.main()
        click.echo("\n👍 All done!")
    else:
        click.secho("Please select an example to run.", fg="red")


@main.command(no_args_is_help=True)
@click.argument(
    "fname",
    type=click.Path(exists=True, dir_okay=False, readable=True),
)
@click.option(
    "-a",
    "--axes",
    is_flag=True,
    help="Add axes",
)
@click.option(
    "-b",
    "--base",
    is_flag=True,
    help="Add a base layer",
)
def plot(fname: str, axes: bool, base: bool) -> None:  # numpydoc ignore=PR01
    """Load and render a VTK mesh."""
    mesh = pv.read(fname)
    plotter = GeoPlotter()
    plotter.add_mesh(mesh)
    if base:
        plotter.add_base_layer()
    if axes:
        plotter.add_axes()
    plotter.show()
