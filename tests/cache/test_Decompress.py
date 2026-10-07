# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Unit-tests for :class:`geovista.cache.Decompress`."""

from __future__ import annotations

import bz2
import hashlib
from pathlib import Path
import shutil
import subprocess
import sys
import time
from typing import TYPE_CHECKING

import pytest

from geovista import cache
from geovista.cache import READ_MODE, Decompress

if TYPE_CHECKING:
    from typing import IO

PAYLOAD = b"geovista" * 2**20
"""A payload large enough that decompression is not instantaneous."""

DIGEST = hashlib.sha256(PAYLOAD).hexdigest()


@pytest.fixture
def compressed(tmp_path):
    """Fixture provides a bzip2 compressed file of the payload."""
    fname = tmp_path / "payload.bin.bz2"
    fname.write_bytes(bz2.compress(PAYLOAD))
    return fname


WORKER = """
import hashlib, pathlib, sys, time
from geovista.cache import Decompress
fname, ready, go = sys.argv[1:]
pathlib.Path(ready).touch()
while not pathlib.Path(go).exists():
    time.sleep(0.001)
result = Decompress(method="auto", name="payload.bin")(fname, "fetch", None)
print(hashlib.sha256(pathlib.Path(result).read_bytes()).hexdigest())
"""
"""Decompress then immediately read the payload, as a racing process would."""


@pytest.mark.parametrize(
    ("name", "expected"), [(None, "payload.bin.bz2.decomp"), ("data", "data")]
)
def test_decompress(compressed, name, expected):
    """Test the payload is decompressed to the same target name as pooch."""
    result = Decompress(method="auto", name=name)(str(compressed), "download", None)
    assert result == str(compressed.parent / expected)
    assert Path(result).read_bytes() == PAYLOAD


def test_readable(compressed):
    """Test the decompressed file is community readable."""
    result = Decompress(method="auto")(str(compressed), "download", None)
    assert Path(result).stat().st_mode & READ_MODE == READ_MODE


def test_atomic(compressed, mocker):
    """Test the target never exists while its content is being written."""
    target = compressed.parent / "payload.bin"
    copyfileobj = shutil.copyfileobj

    def spy(fsrc: IO[bytes], fdst: IO[bytes]) -> None:
        assert not target.exists()
        copyfileobj(fsrc, fdst)
        assert not target.exists()

    mocker.patch.object(cache.shutil, "copyfileobj", side_effect=spy)
    Decompress(method="auto", name=target.name)(str(compressed), "download", None)
    assert target.read_bytes() == PAYLOAD
    assert set(compressed.parent.iterdir()) == {compressed, target}


def test_fetch_existing(compressed):
    """Test an existing target is reused when the asset was only fetched."""
    target = compressed.parent / "payload.bin"
    target.write_bytes(b"cached")
    result = Decompress(method="auto", name=target.name)(str(compressed), "fetch", None)
    assert result == str(target)
    assert target.read_bytes() == b"cached"


@pytest.mark.parametrize("action", ["download", "update"])
def test_replace_existing(compressed, action):
    """Test an existing target is replaced when the asset was (re-)downloaded."""
    target = compressed.parent / "payload.bin"
    target.write_bytes(b"stale")
    Decompress(method="auto", name=target.name)(str(compressed), action, None)
    assert target.read_bytes() == PAYLOAD


def test_failure_cleanup(tmp_path):
    """Test a failed decompression leaves neither a target nor a temporary file."""
    corrupt = tmp_path / "corrupt.bin.bz2"
    corrupt.write_bytes(b"not bzip2")
    with pytest.raises(OSError, match="Invalid data stream"):
        Decompress(method="auto", name="corrupt.bin")(str(corrupt), "download", None)
    assert list(tmp_path.iterdir()) == [corrupt]


def test_concurrent(compressed, tmp_path_factory):
    """Test concurrent processes never read a partially decompressed file."""
    sync = tmp_path_factory.mktemp("sync")
    go = sync / "go"
    workers = []
    for i in range(8):
        cmd = [sys.executable, "-c", WORKER, str(compressed), str(sync / f"{i}"), go]
        workers.append(subprocess.Popen(cmd, stdout=subprocess.PIPE, text=True))  # noqa: S603
    # release the workers together, once all are ready, to maximise contention
    deadline = time.monotonic() + 60
    while len(list(sync.iterdir())) < len(workers) and time.monotonic() < deadline:
        time.sleep(0.01)
    go.touch()
    digests = {worker.communicate()[0].strip() for worker in workers}
    assert all(worker.returncode == 0 for worker in workers)
    assert digests == {DIGEST}
