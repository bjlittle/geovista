# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Print the requirements a wheel declares for its core and the given extras.

``uv``'s ``--resolution lowest-direct`` takes a wheel's own requirements as
transitive, and so resolves them at their highest. The ``floors-pypi`` action
passes these lines to ``uv`` as direct requirements beside the wheel, so that
each resolves at the floor the wheel promises (floors spec §2 decision 7).

Usage: ``python wheel_requirements.py <wheel> <extra>[,<extra>...]``

"""

from __future__ import annotations

from email.parser import HeaderParser
import re
import sys
import zipfile

#: How to call the script.
USAGE = "usage: python wheel_requirements.py <wheel> <extra>[,<extra>...]"
#: A marker naming one extra alone, as the build writes it.
EXTRA = re.compile(r'extra\s*==\s*"(?P<name>[^"]+)"')
#: The marker of an extra's requirement that has a marker of its own, which the
#: build writes before the extra, joined by "and".
EXTRA_AFTER = re.compile(r'(?P<own>.+?)\s+and\s+extra\s*==\s*"(?P<name>[^"]+)"')


def _wrapped(marker: str) -> bool:
    """Say whether the marker is one parenthesised whole."""
    if not (marker.startswith("(") and marker.endswith(")")):
        return False
    depth = 0
    for at, char in enumerate(marker):
        depth += {"(": 1, ")": -1}.get(char, 0)
        if depth == 0 and at < len(marker) - 1:
            return False
    return True


def _split(line: str, marker: str) -> tuple[str | None, str | None]:
    """Return the extra a marker names, if any, and the marker of its own.

    A marker naming no extra is the requirement's own, for ``uv`` to evaluate.
    One naming an extra any other way than the build writes it raises, rather
    than being kept or dropped by a guess.
    """
    if "extra" not in marker:
        return None, marker
    if match := EXTRA.fullmatch(marker):
        return match["name"], None
    match = EXTRA_AFTER.fullmatch(marker)
    if match is None or "extra" in match["own"]:
        message = f"cannot read the extra of {line!r}"
        raise ValueError(message)
    own = match["own"]
    if " or " in own and not _wrapped(own):
        # "a or b and extra" reads as "a or (b and extra)", which no split keeps
        message = f"cannot read the extra of {line!r}"
        raise ValueError(message)
    return match["name"], own


def requirements(wheel: str, extras: set[str]) -> list[str]:
    """Return the requirements of the wheel's core and of the given extras.

    Each keeps any marker of its own, for ``uv`` to evaluate.
    """
    with zipfile.ZipFile(wheel) as archive:
        names = [
            name
            for name in archive.namelist()
            if name.count("/") == 1 and name.endswith(".dist-info/METADATA")
        ]
        if len(names) != 1:
            message = f"{wheel} holds {len(names)} METADATA files, not one"
            raise ValueError(message)
        metadata = HeaderParser().parsestr(archive.read(names[0]).decode("utf-8"))

    # an extra renamed or dropped would lose its floors in silence
    missing = sorted(extras - set(metadata.get_all("Provides-Extra") or []))
    if missing:
        message = f"{wheel} provides no extra {', '.join(missing)}"
        raise ValueError(message)

    found = []
    for line in metadata.get_all("Requires-Dist") or []:
        requirement, _, marker = (part.strip() for part in line.partition(";"))
        extra, own = _split(line, marker) if marker else (None, None)
        if extra is not None and extra not in extras:
            continue
        found.append(f"{requirement}; {own}" if own else requirement)
    return found


def main(argv: list[str]) -> int:
    """Print each requirement on a line of its own, and return the exit status."""
    if len(argv) != 2:
        print(USAGE, file=sys.stderr)
        return 2
    wheel, extras = argv
    try:
        found = requirements(wheel, set(extras.split(",")))
    except (ValueError, zipfile.BadZipFile) as error:
        print(error, file=sys.stderr)
        return 1
    for requirement in found:
        print(requirement)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
