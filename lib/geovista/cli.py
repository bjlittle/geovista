import pathlib
from typing import List, Optional, Tuple

import click
from click_default_group import DefaultGroup
import pooch
import pyvista as pv

from . import GeoPlotter
from ._version import version as __version__
from .cache import CACHE

CONTEXT_SETTINGS = dict(help_option_names=["-h", "--help"])

ALL: str = "all"
NE_ROOT: str = "natural_earth"
NE_GROUPS: List[str] = sorted(["physical"])
NE_CHOICES: List[str] = [ALL]
NE_CHOICES.extend(NE_GROUPS)

DEFAULT_FG: str = "cyan"

logger = pooch.get_logger()


def _download_group(
    fnames: List[str],
    name: Optional[str] = None,
    fg: Optional[str] = None,
    summary: Optional[bool] = True,
) -> None:
    if fg is None:
        fg = DEFAULT_FG

    name: str = "" if name is None else f"{name} "

    N: int = len(fnames)
    n: int = len(str(N))

    logger.setLevel("ERROR")

    click.echo(f"Downloading {N} {name}registered resource{_plural(N)}:")
    for i, fname in enumerate(fnames):
        click.echo(f"[{i+1:0{n}d}] Downloading ", nl=False)
        click.secho(f"{fname} ", nl=False, fg=fg)
        click.echo("... ", nl=False)
        CACHE.fetch(fname)
        click.secho("done!", fg="green")

    if summary:
        click.echo("\nAll done! 👍")
        click.echo("Resources are available in the cache directory ", nl=False)
        click.secho(f"{CACHE.abspath}", fg=fg, nl=False)
        click.echo(".")

    logger.setLevel("INFO")


def _plural(value: int) -> bool:
    return "s" if (value == 0 or value > 1) else ""


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
        click.secho(f"{__version__}", fg=DEFAULT_FG)

    if cache:
        click.echo("cache directory ", nl=False)
        click.secho(f"{CACHE.abspath}", fg=DEFAULT_FG)


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
    "--check",
    is_flag=True,
    help="Check availability of registered resources (no download).",
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
    "-ne",
    "--natural-earth",
    "pull_ne",
    multiple=True,
    type=click.Choice(NE_CHOICES, case_sensitive=False),
    is_flag=False,
    flag_value=ALL,
    help="Natural Earth feature category.",
)
@click.option(
    "-o",
    "--output",
    type=click.Path(file_okay=False, resolve_path=True, path_type=pathlib.Path),
    help=f"Download target directory (default: {CACHE.abspath})",
)
def download(
    pull: bool,
    check: bool,
    dry_run: bool,
    show: bool,
    pull_ne: Tuple[str],
    output: Optional[pathlib.Path],
) -> None:
    """
    Download and cache geovista resources (offline support).

    """
    fnames: List[str] = sorted(CACHE.registry_files)

    if not fnames:
        click.secho("No resources are registered with geovista.", fg="red")
        return

    N: int = len(fnames)
    n: int = len(str(N))
    fg: str = DEFAULT_FG

    if output:
        output.mkdir(exist_ok=True)
        previous_path = CACHE.path
        CACHE.path = output

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
                items = list(filter(lambda item: item.startswith(prefix), fnames))
                name = f"Natural Earth {group}"
                _download_group(items, name=name, summary=(i + 1 == n_groups))

    if check:
        unavailable = 0
        click.echo("Checking remote availablity of registered resources:")
        for i, fname in enumerate(fnames):
            click.echo(f"[{i+1:0{n}d}] ", nl=False)
            click.secho(f"{fname} ", nl=False, fg=fg)
            click.echo("is ... ", nl=False)
            status, sfg = (
                ("available!", "green")
                if (available := CACHE.is_available(fname))
                else ("unavailable!", "red")
            )
            if not available:
                unavailable += 1
            click.secho(status, fg=sfg)
        click.echo("\nAll done! ", nl=False)

        if not unavailable:
            click.echo("👍")
            click.echo(f"{N} resource{_plural(N)} ", nl=False)
            click.secho("available", fg="green", nl=False)
            click.echo(".")
        else:
            click.echo("🤔")
            if unavailable == N:
                click.echo(f"{N} resource{_plural(N)} ", nl=False)
                click.secho("unavailable", fg="red", nl=False)
                click.echo(". Nuts!")
            else:
                available = N - unavailable
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
            click.echo(f"[{i+1:0{n}d}] ", nl=False)
            click.secho(f"{CACHE.get_url(fname)}", fg=fg)
        click.echo("\nAll done! 👍")

    if show:
        click.echo("Names of registered resources:")
        for i, fname in enumerate(fnames):
            click.echo(f"[{i+1:0{n}d}] ", nl=False)
            click.secho(f"{fname}", fg=fg)
        click.echo("\nAll done! 👍")

    if output:
        CACHE.path = previous_path


@main.command(no_args_is_help=True)
@click.argument(
    "fname",
    type=click.Path(exists=True, dir_okay=False, readable=True),
)
@click.option(
    "-b",
    "--base",
    is_flag=True,
    help="Add a base layer",
)
def plot(fname, base) -> None:
    """
    Load and render a VTK mesh.

    """
    mesh = pv.read(fname)
    plotter = GeoPlotter()
    plotter.add_mesh(mesh)
    if base:
        plotter.add_base_layer()
    plotter.show()
