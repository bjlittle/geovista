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

#: A marker naming one extra alone, as the build writes it.
EXTRA = re.compile(r'extra\s*==\s*"(?P<name>[^"]+)"')


def requirements(wheel: str, extras: set[str]) -> list[str]:
    """Return the requirements of the wheel's core and of the given extras.

    A requirement under any other marker raises, rather than being kept or
    dropped by a guess.
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

    found = []
    for line in metadata.get_all("Requires-Dist") or []:
        requirement, _, marker = line.partition(";")
        marker = marker.strip()
        if not marker:
            found.append(requirement.strip())
        elif match := EXTRA.fullmatch(marker):
            if match["name"] in extras:
                found.append(requirement.strip())
        else:
            message = f"cannot read the marker of {line!r}"
            raise ValueError(message)
    return found


def main(argv: list[str]) -> int:
    """Print each requirement on a line of its own, and return the exit status."""
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
