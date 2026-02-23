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

from . import __version__
from .cache import CACHE, DATA_VERSION, pooch_mute
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


class Downloader:
    """Asset downloader and manager.

    Notes
    -----
    .. versionadded:: 0.6.0

    """

    def __init__(self) -> None:
        """Asset downloader and manager.

        Notes
        -----
        .. versionadded:: 0.6.0

        """
        self.fnames: list[str] = sorted(CACHE.registry_files)

    @staticmethod
    def plural(quantity: int) -> str:
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

    def clean(self) -> None:
        """Remove all cached assets.

        Notes
        -----
        .. versionadded:: 0.1.0

        """
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

    def tidy(self) -> None:
        """Remove old cached assets except the current data version.

        Removes all versioned asset directories from the geovista cache directory
        *except* the current :data:`DATA_VERSION` directory.

        Notes
        -----
        .. versionadded:: 0.6.0

        """
        msg = (
            "Are you sure you want to delete all cached geovista assets "
            f"other than the current data version ({DATA_VERSION!r})"
        )
        if not click.confirm(f"\n{msg}?", abort=True):
            return

        asset_dirs = list(
            filter(
                lambda target: target.name != DATA_VERSION,
                pathlib.Path(resources["cache_dir"]).glob("*/"),
            )
        )

        if not asset_dirs:
            click.echo("\nThere are no cached assets to delete.")
            return

        for target in asset_dirs:
            try:
                if target.is_symlink():
                    link_target = target.readlink()
                    if link_target.exists() and link_target.name != DATA_VERSION:
                        rmtree(link_target)
                    target.unlink()
                else:
                    rmtree(target)
                click.echo("Deleted old assets directory:", nl=False)
                click.secho(f"{target}", fg=FG_COLOUR)
            except (FileNotFoundError, OSError, PermissionError) as e:
                click.secho(f"⚠️ Failed to remove {target}. Reason: {e}", fg="red")

    def collect(self, prefix: str, /, *, invert: bool = False) -> list[str]:
        """Filter the asset names by the starting `prefix`.

        Parameters
        ----------
        prefix : str
            The `prefix` to filter the asset names.
        invert : bool, default=False
            Negate the `prefix` match i.e., filter the asset names that do not
            match the `prefix`.

        Returns
        -------
        list of str
            The sorted list of assets with matching `prefix`. Also see `invert`.

        Notes
        -----
        .. versionadded:: 0.1.0

        """
        result = list(filter(lambda item: item.startswith(prefix), self.fnames))
        if invert:
            result = list(set(self.fnames) - set(result))
        return sorted(result)

    def download(
        self,
        /,
        fnames: list[str] | None = None,
        *,
        decompress: bool | None = False,
        name: str | None = None,
        fg_colour: str | None = FG_COLOUR,
        summary: bool | None = True,
    ) -> None:
        """Download and populate the geovista cache with requested assets.

        Only assets which are not in the cache will be downloaded and verified via
        :mod:`pooch`.

        Parameters
        ----------
        fnames : list of str, optional
            The list of assets to be downloaded. Defaults to the ``CACHE``
            registry filenames.
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
        if fnames is None:
            fnames = self.fnames

        name_post: str = "" if name is None else f"{name} "
        n_fnames: int = len(fnames)
        width: int = len(str(n_fnames))
        count = 0
        previous = pooch_mute(silent=True)
        if n_fnames:
            click.echo(
                f"Downloading {n_fnames} {name_post}"
                f"registered asset{self.plural(n_fnames)}:"
            )
        else:
            click.echo(f"There are no {name_post}registered assets.")

        for i, fname in enumerate(fnames):
            click.echo(f"[{i + 1:0{width}d}/{n_fnames}] Downloading ", nl=False)
            click.secho(f"{fname} ", nl=False, fg=fg_colour)
            click.echo("... ", nl=False)
            processor = None
            name_path = pathlib.Path(fname)

            if (
                decompress
                and (suffix := name_path.suffix) in pooch.Decompress.extensions
            ):
                processor = pooch.Decompress(
                    method="auto", name=name_path.stem.removesuffix(suffix)
                )
            CACHE.fetch(fname, processor=processor)
            click.secho("done!", fg="green")
            count += 1

        if summary:
            if count:
                click.echo("\nAssets are available in the cache directory ", nl=False)
                click.secho(f"{CACHE.abspath}", fg=fg_colour)
            else:
                click.echo("\nNo assets were downloaded.")
            click.echo("👍 All done!")

        _ = pooch_mute(silent=previous)

    def dry_run(self, /, *, fg_colour: str | None = FG_COLOUR) -> None:
        """Show the URLs of all registered assets.

        Parameters
        ----------
        fg_colour : str, default="cyan"
            Foreground colour to highlight the asset URL.

        Notes
        -----
        .. versionadded:: 0.1.0

        """
        n_fnames: int = len(self.fnames)
        width: int = len(str(n_fnames))
        click.echo("URLs of registered assets:")

        for i, fname in enumerate(self.fnames):
            click.echo(f"[{i + 1:0{width}d}/{n_fnames}] ", nl=False)
            click.secho(f"{CACHE.get_url(fname)}", fg=fg_colour)

        click.echo("\n👍 All done!")

    def show(self, /, *, fg_colour: str | None = FG_COLOUR) -> None:
        """Show the names of all registered assets.

        Parameters
        ----------
        fg_colour : str, default="cyan"
            Foreground colour to highlight the asset URL.

        Notes
        -----
        .. versionadded:: 0.1.0

        """
        n_fnames: int = len(self.fnames)
        width: int = len(str(n_fnames))
        click.echo("Names of registered assets:")

        for i, fname in enumerate(self.fnames):
            click.echo(f"[{i + 1:0{width}d}/{n_fnames}] ", nl=False)
            click.secho(f"{fname}", fg=fg_colour)

        click.echo("\n👍 All done!")

    def verify(self, /, *, fg_colour: str | None = FG_COLOUR) -> None:
        """Check the remote availability of each registered asset.

        Parameters
        ----------
        fg_colour : str, default="cyan"
            Foreground colour to highlight the asset URL.

        Notes
        -----
        .. versionadded:: 0.1.0

        """
        n_fnames: int = len(self.fnames)
        width: int = len(str(n_fnames))
        unavailable = 0
        click.echo("Verifying availability of registered assets:")

        for i, fname in enumerate(self.fnames):
            click.echo(f"[{i + 1:0{width}d}/{n_fnames}] ", nl=False)
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
            click.echo(f"\n{n_fnames} asset{self.plural(n_fnames)} ", nl=False)
            click.secho("available", fg="green", nl=False)
            click.echo(".")
            click.echo("👍 All done!")
        else:
            click.echo("\n💥 ", nl=False)
            if unavailable == n_fnames:
                click.echo(f"{n_fnames} asset{self.plural(n_fnames)} ", nl=False)
                click.secho("unavailable", fg="red", nl=False)
                click.echo(". Nuts!")
            else:
                available = n_fnames - unavailable
                click.echo(f"{available} asset{self.plural(available)} ", nl=False)
                click.secho("available", fg="green", nl=False)
                click.echo(
                    f", but {unavailable} asset{self.plural(unavailable)} ", nl=False
                )
                click.secho("unavailable", fg="red", nl=False)
                click.echo(". Dang!")


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
    "-d",
    "--data-version",
    is_flag=True,
    help="Show geovista data version.",
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
def main(
    version: bool, report: bool, data_version: bool, cache: bool
) -> None:  # numpydoc ignore=PR01
    """To get help for geovista commands, simply use "geovista COMMAND --help"."""
    if version:
        click.secho(f"{__version__}", fg=FG_COLOUR)

    if report:
        click.echo(Report())

    if data_version:
        click.secho(f"{CACHE.abspath.name}", fg=FG_COLOUR)

    if cache:
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
    help="Delete all cached assets; see also `--tidy`.",
)
@click.option(
    "-d",
    "--decompress",
    is_flag=True,
    help="Decompress all cached assets.",
)
@click.option(
    "--doc-images", is_flag=True, help="Download documentation test image assets."
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Show URLs of registered assets (no download).",
)
@click.option("-i", "--images", is_flag=True, help="Download all test image assets.")
@click.option(
    "-l",
    "--list",
    "show",
    is_flag=True,
    help="Show names of registered assets (no download).",
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
    "--rasters",
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
    "--tidy",
    is_flag=True,
    help="Delete all cached assets except the current data version.",
)
@click.option("--unit-images", is_flag=True, help="Download unit test image assets.")
@click.option(
    "-v",
    "--verify",
    is_flag=True,
    help="Verify availability of registered assets (no download).",
)
def download(  # noqa: PLR0913
    pull: bool,
    clean: bool,
    decompress: bool,
    doc_images: bool,
    dry_run: bool,
    images: bool,
    show: bool,
    natural_earth: Iterable[str],
    operational: bool,
    pantry: bool,
    rasters: bool,
    target: pathlib.Path | None,
    tidy: bool,
    unit_images: bool,
    verify: bool,
) -> None:  # numpydoc ignore=PR01
    """Download and cache geovista assets (offline support)."""
    if not CACHE.registry_files:
        click.secho("No assets are registered with geovista.", fg="red")
        return

    downloader = Downloader()

    if dry_run:
        downloader.dry_run()
        return

    if show:
        downloader.show()
        return

    if verify:
        downloader.verify()
        return

    if clean:
        downloader.clean()
        return

    if tidy:
        downloader.tidy()
        return

    if target:
        target.mkdir(exist_ok=True)
        previous_path = CACHE.path
        CACHE.path = target

    if pull:
        downloader.download(decompress=decompress)
    elif operational:
        assets = downloader.collect("tests", invert=True)
        downloader.download(assets, decompress=decompress, name="operational")
    else:
        if images:
            assets = downloader.collect("tests")
            downloader.download(assets, decompress=decompress, name="test image")
        else:
            if doc_images:
                assets = downloader.collect("tests/docs")
                downloader.download(
                    assets, decompress=decompress, name="documentation test image"
                )

            if unit_images:
                assets = downloader.collect("tests/unit")
                downloader.download(
                    assets, decompress=decompress, name="unit test image"
                )

        if pantry:
            name = "pantry"
            assets = downloader.collect(name)
            downloader.download(assets, decompress=decompress, name=name)

        if natural_earth:
            if ALL in natural_earth:
                natural_earth = NE_GROUPS
            natural_earth = sorted(set(natural_earth))
            n_groups = len(natural_earth)
            for i, group in enumerate(natural_earth):
                prefix = f"{NE_ROOT}/{group}"
                name = f"Natural Earth {group}"
                assets = downloader.collect(prefix)
                downloader.download(
                    assets,
                    decompress=decompress,
                    name=name,
                    summary=(i + 1 == n_groups),
                )

        if rasters:
            name = "raster"
            assets = downloader.collect(name)
            downloader.download(assets, decompress=decompress, name=name)

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
        groups_new = _groups()
        n_groups = len(groups_new)
        width = len(str(n_groups))
        for i, group in enumerate(groups_new):
            click.echo(f"[{i + 1:0{width}d}/{n_groups}] ", nl=False)
            click.secho(f"{group}", fg="green")
        click.echo("\n👍 All done!")
        return

    run_all = ALL in (run, run_group) or run_all

    if run_all:
        for i, script in enumerate(EXAMPLES[1:]):
            msg = f"Running example {script!r} ({i + 1} of {n_examples}) ..."
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
        filtered = [script for script in EXAMPLES[1:] if script.startswith(run_group)]
        n_group = len(filtered)
        for i, script in enumerate(filtered):
            msg = f"Running {run_group!r} example {script!r} ({i + 1} of {n_group}) ..."
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
    p = GeoPlotter()
    p.add_mesh(mesh)
    if base:
        p.add_base_layer()
    if axes:
        p.add_axes()
    p.show()
