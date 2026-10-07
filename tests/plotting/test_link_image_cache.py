# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Unit-tests for :func:`tests.plotting.link_image_cache`."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import threading

import pytest

from . import link_image_cache


@pytest.fixture
def paths(tmp_path):
    """Fixture provides the link and the target directory it should resolve to."""
    return tmp_path / "unit_image_cache", tmp_path / "cache" / "tests" / "unit"


def test_absent(paths):
    """Test the link and its target are created."""
    link, target = paths
    link_image_cache(link, target)
    assert link.is_symlink()
    assert link.readlink() == target
    assert target.is_dir()


def test_current(paths):
    """Test an existing link to the target is kept."""
    link, target = paths
    target.mkdir(parents=True)
    link.symlink_to(target)
    (target / "baseline.png").touch()
    link_image_cache(link, target)
    assert link.readlink() == target
    assert (link / "baseline.png").is_file()


@pytest.mark.parametrize("broken", [False, True])
def test_stale(paths, broken):
    """Test a link to another cache version, or to nothing, is replaced."""
    link, target = paths
    stale = target.parent / "stale"
    if not broken:
        stale.mkdir(parents=True)
    link.symlink_to(stale)
    link_image_cache(link, target)
    assert link.readlink() == target


def test_directory(paths):
    """Test a real directory, as pytest-pyvista may create, is replaced."""
    link, target = paths
    link.mkdir()
    (link / "generated.png").touch()
    link_image_cache(link, target)
    assert link.readlink() == target


@pytest.mark.parametrize("stale", [False, True])
def test_concurrent(paths, stale):
    """Test concurrent callers, such as pytest-xdist workers, all succeed."""
    link, target = paths
    if stale:
        link.symlink_to(target.parent / "stale")
    workers = 16
    barrier = threading.Barrier(workers)

    def call() -> None:
        barrier.wait()
        link_image_cache(link, target)

    for _ in range(20):
        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = [executor.submit(call) for _ in range(workers)]
        for future in futures:
            future.result()
        assert link.readlink() == target
        link.unlink()
        if stale:
            link.symlink_to(target.parent / "stale")
