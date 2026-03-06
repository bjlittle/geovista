# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Entry-point for geovista command line interface (CLI)."""

from __future__ import annotations

from geovista.cli import main as entry


def main() -> None:
    """Execute the CLI entry-point."""
    entry()


if __name__ == "__main__":
    main()
