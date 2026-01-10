# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Unit-tests for :func:`geovista.cli.main`."""

from __future__ import annotations

import os
from pathlib import Path
import subprocess

import pytest

from geovista import __version__ as version
from geovista.cache import CACHE, DATA_VERSION

CONDA_PREFIX: str = os.environ.get("CONDA_PREFIX", "")
ENTRYPOINT: str = str(Path(CONDA_PREFIX) / "bin" / "geovista")


@pytest.mark.skipif(
    "CONDA_PREFIX" not in os.environ, reason="requires conda environment"
)
def test_option_cache():
    """Test the --cache option returns the cache directory."""
    result = subprocess.run(  # noqa: S603
        [ENTRYPOINT, "--cache"],
        capture_output=True,
        text=True,
        check=True,
    )
    assert result.stdout.strip() == str(CACHE.abspath)


@pytest.mark.skipif(
    "CONDA_PREFIX" not in os.environ, reason="requires conda environment"
)
def test_option_data_version():
    """Test the --data-version option returns the data version."""
    result = subprocess.run(  # noqa: S603
        [ENTRYPOINT, "--data-version"],
        capture_output=True,
        text=True,
        check=True,
    )
    assert result.stdout.strip() == DATA_VERSION


@pytest.mark.skipif(
    "CONDA_PREFIX" not in os.environ, reason="requires conda environment"
)
def test_option_version():
    """Test the --version option returns the geovista version."""
    result = subprocess.run(  # noqa: S603
        [ENTRYPOINT, "--version"],
        capture_output=True,
        text=True,
        check=True,
    )
    assert result.stdout.strip() == version
