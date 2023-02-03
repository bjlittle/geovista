"""
This module provides command line interface (CLI) support for the geovista entry-point.

Notes
-----
.. versionadded:: 0.1.0

"""
import importlib
import pathlib
import pkgutil
from shutil import rmtree
from typing import List, Optional, Tuple

import click
from click_default_group import DefaultGroup
import pooch
import pyvista as pv

from . import examples as scripts
from . import logger
from ._version import version as __version__
from .cache import CACHE
from .config import resources
from .geoplotter import GeoPlotter

__all__ = ["main"]

CONTEXT_SETTINGS = dict(help_option_names=["-h", "--help"])

ALL: str = "all"
NE_ROOT: str = "natural_earth"
NE_GROUPS: List[str] = sorted(["physical"])
NE_CHOICES: List[str] = [ALL]
NE_CHOICES.extend(NE_GROUPS)

DEFAULT_FG_COLOUR: str = "cyan"

SCRIPTS: List[str] = [ALL] + [
    submodule.name for submodule in pkgutil.iter_modules(scripts.__path__)
]

pooch_logger = pooch.get_logger()


def _download_group(
    fnames: List[str],
    name: Optional[str] = None,
    fg_colour: Optional[str] = None,
    summary: Optional[bool] = True,
) -> None:
    """
    Common utility to download and populate the geovista cache with requested
    assets.

    Only assets which are not in the cache will be downloaded and verified via
    :mod:`pooch`.

    Parameters
    ----------
    fnames : list of str
        The list of assets to be downloaded.
    name : str, optional
        The name of the asset collection within the cache e.g., raster or pantry
    fg_color : str, default="cyan"
        Foreground colour to highlight the asset name during download.
    summary : bool, default=True
        Whether to provide a download summary to the user.

    Notes
    -----
    .. versionadded:: 0.1.0

    """
    if fg_colour is None:
        fg_colour = DEFAULT_FG_COLOUR

    name: str = "" if name is None else f"{name} "

    n_fnames: int = len(fnames)
    width: int = len(str(n_fnames))

    pooch_logger.setLevel("ERROR")

    click.echo(f"Downloading {n_fnames} {name}registered resource{_plural(n_fnames)}:")
    for i, fname in enumerate(fnames):
        click.echo(f"[{i+1:0{width}d}] Downloading ", nl=False)
        click.secho(f"{fname} ", nl=False, fg=fg_colour)
        click.echo("... ", nl=False)
        CACHE.fetch(fname)
        click.secho("done!", fg="green")

    if summary:
        click.echo("\nResources are available in the cache directory ", nl=False)
        click.secho(f"{CACHE.abspath}", fg=fg_colour)
        click.echo("👍 All done!")

    pooch_logger.setLevel("INFO")


def _plural(quantity: int) -> str:
    """
    Convenience to determine whether the provided amount is textually plural.

    Parameters
    ----------
    quantity : int
        The quantity under consideration.

    Returns
    -------
    str
        A "s" for a plural quantity, otherwise and empty string.

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
    "-v",
    "--version",
    is_flag=True,
    help="Show geovista package version.",
)
def main(version: bool, cache: bool) -> None:
    """
    To get help for geovista commands, simply use "geovista COMMAND --help".

    """
    if version:
        click.echo("version ", nl=False)
        click.secho(f"{__version__}", fg=DEFAULT_FG_COLOUR)

    if cache:
        click.echo("cache directory ", nl=False)
        click.secho(f"{CACHE.abspath}", fg=DEFAULT_FG_COLOUR)


@main.command(no_args_is_help=True)
@click.option(
    "-a",
    "--all",
    "pull",
    is_flag=True,
    help="Download all registered resources.",
)
@click.option(
    "-c",
    "--clean",
    is_flag=True,
    help="Delete all cached resources.",
)
@click.option(
    "-d",
    "--dry-run",
    is_flag=True,
    help="Show URLs of registered resources.",
)
@click.option(
    "-l",
    "--list",
    "show",
    is_flag=True,
    help="Show names of registered resources.",
)
@click.option(
    "-m",
    "--mesh",
    is_flag=True,
    help="Download mesh resources.",
)
@click.option(
    "-ne",
    "--natural-earth",
    "pull_ne",
    multiple=True,
    type=click.Choice(NE_CHOICES, case_sensitive=False),
    is_flag=False,
    flag_value=ALL,
    help="Download Natural Earth feature resources.",
)
@click.option(
    "-o",
    "--output",
    type=click.Path(file_okay=False, resolve_path=True, path_type=pathlib.Path),
    help=f"Download target directory (default: {CACHE.abspath})",
)
@click.option("-p", "--pantry", is_flag=True, help="Download sample data resources.")
@click.option(
    "-r",
    "--raster",
    is_flag=True,
    help="Download raster resources.",
)
@click.option(
    "-v",
    "--verify",
    is_flag=True,
    help="Verify availability of registered resources (no download).",
)
def download(
    pull: bool,
    clean: bool,
    dry_run: bool,
    show: bool,
    mesh: bool,
    pull_ne: Tuple[str],
    output: Optional[pathlib.Path],
    pantry: bool,
    raster: bool,
    verify: bool,
) -> None:
    """
    Download and cache geovista resources (offline support).

    """
    fnames: List[str] = sorted(CACHE.registry_files)

    if not fnames:
        click.secho("No resources are registered with geovista.", fg="red")
        return

    n_fnames: int = len(fnames)
    width: int = len(str(n_fnames))
    fg_colour: str = DEFAULT_FG_COLOUR

    if clean:
        msg = "Are you sure you want to delete all cached geovista resources"
        if click.confirm(f"\n{msg}?", abort=True):
            target = resources["cache_dir"]

            if target.exists():
                if target.is_symlink():
                    rmtree(target.readlink())
                    target.unlink()
                else:
                    rmtree(target)

                click.echo("\nDeleted the cache directory ", nl=False)
                click.secho(f"{target}", fg=DEFAULT_FG_COLOUR)
                click.echo("👍 All done!")
            else:
                click.echo("\nThere are no cached resources to delete.")

    if output:
        output.mkdir(exist_ok=True)
        previous_path = CACHE.path
        CACHE.path = output

    def collect(prefix):
        return list(filter(lambda item: item.startswith(prefix), fnames))

    if pull:
        _download_group(fnames)
    else:
        if pull_ne:
            if ALL in pull_ne:
                pull_ne = NE_GROUPS
            pull_ne = sorted(set(pull_ne))
            n_groups = len(pull_ne)
            for i, group in enumerate(pull_ne):
                prefix = f"{NE_ROOT}/{group}"
                name = f"Natural Earth {group}"
                _download_group(collect(prefix), name=name, summary=(i + 1 == n_groups))

        if raster:
            name = "raster"
            _download_group(collect(name), name=name)

        if mesh:
            name = "mesh"
            _download_group(collect(name), name=name)

        if pantry:
            name = "pantry"
            _download_group(collect(name), name=name)

    if verify:
        unavailable = 0
        click.echo("Verifying remote availablity of registered resources:")
        for i, fname in enumerate(fnames):
            click.echo(f"[{i+1:0{width}d}] ", nl=False)
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
            click.echo(f"\n{n_fnames} resource{_plural(n_fnames)} ", nl=False)
            click.secho("available", fg="green", nl=False)
            click.echo(".")
            click.echo("👍 All done!")
        else:
            click.echo("\n💥 ", nl=False)
            if unavailable == n_fnames:
                click.echo(f"{n_fnames} resource{_plural(n_fnames)} ", nl=False)
                click.secho("unavailable", fg="red", nl=False)
                click.echo(". Nuts!")
            else:
                available = n_fnames - unavailable
                click.echo(f"{available} resource{_plural(available)} ", nl=False)
                click.secho("available", fg="green", nl=False)
                click.echo(
                    f", but {unavailable} resource{_plural(unavailable)} ", nl=False
                )
                click.secho("unavailable", fg="red", nl=False)
                click.echo(". Dang!")

    if dry_run:
        click.echo("URLs of registered resources:")
        for i, fname in enumerate(fnames):
            click.echo(f"[{i+1:0{width}d}] ", nl=False)
            click.secho(f"{CACHE.get_url(fname)}", fg=fg_colour)
        click.echo("\n👍 All done!")

    if show:
        click.echo("Names of registered resources:")
        for i, fname in enumerate(fnames):
            click.echo(f"[{i+1:0{width}d}] ", nl=False)
            click.secho(f"{fname}", fg=fg_colour)
        click.echo("\n👍 All done!")

    if output:
        CACHE.path = previous_path


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
def plot(fname, axes, base) -> None:
    """
    Load and render a VTK mesh.

    """
    # pylint: disable-next=import-outside-toplevel,unused-import
    import geovista.theme

    mesh = pv.read(fname)
    plotter = GeoPlotter()
    plotter.add_mesh(mesh)
    if base:
        plotter.add_base_layer()
    if axes:
        plotter.add_axes()
    plotter.show()


@main.command(no_args_is_help=True)
@click.option(
    "-a",
    "--all",
    "run_all",
    is_flag=True,
    help="Execute all examples.",
)
@click.option(
    "-l",
    "--list",
    "show",
    is_flag=True,
    help="Show names of available examples to run.",
)
@click.option(
    "-r",
    "--run",
    type=click.Choice(SCRIPTS, case_sensitive=False),
    is_flag=False,
    help="Execute the example.",
)
@click.option(
    "-v",
    "--verbose",
    is_flag=True,
    help="Enable example diagnostics.",
)
def examples(run_all, show, run, verbose):
    """
    Execute a geovista example script.

    """
    # account for the "all" option
    n_scripts = len(SCRIPTS) - 1

    if show:
        click.echo("Names of available examples:")
        width = len(str(n_scripts))
        for i, script in enumerate(SCRIPTS[1:]):
            click.echo(f"[{i + 1:0{width}d}] ", nl=False)
            click.secho(f"{script}", fg="green")
        click.echo("\n👍 All done!")
        return

    run_all = True if run == ALL else run_all

    if verbose:
        logger.setLevel("INFO")

    if run_all:
        for i, script in enumerate(SCRIPTS[1:]):
            msg = f"Running example {script!r} ({i+1} of {n_scripts}) ..."
            click.secho(msg, fg="green")
            module = importlib.import_module(f"geovista.examples.{script}")
            if verbose:
                print(module.main.__doc__)
            module.main()
        click.echo("\n👍 All done!")
        return

    msg = f"Running example {run!r} ..."
    click.secho(msg, fg="green")
    module = importlib.import_module(f"geovista.examples.{run}")
    if verbose:
        print(module.main.__doc__)
    module.main()
    click.echo("\n👍 All done!")
