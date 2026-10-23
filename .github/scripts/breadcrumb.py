# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""The link from a failed repository check to the section that documents it.

Every check ``geovista`` enforces on its own repository has a section on the
repository checks page, and a failure of the check ends with a link to it. The
text is defined here, once, for the pytest hook in "tests/conftest.py" and for the
scripts that run as checks in CI, which load this module by path.

It imports nothing beyond the standard library, as "ci-changelog.yml" runs its
script with "click" and "towncrier" installed and nothing else.

See "docs/src/developer/specs/2026-10-23-repository-checks-design.md", section 3.3.

"""

from __future__ import annotations

__all__ = ["LABEL", "PAGE", "breadcrumb"]

#: The published page that documents every repository check. It is the
#: documentation of "main", which a contributor's branch is compared against.
PAGE = "https://geovista.readthedocs.io/en/latest/developer/checks.html"

#: The stem of the label of each check's section, completed by the check's name.
LABEL = "gv-developer-checks-"


def breadcrumb(name: str) -> str:
    """Return the lines that end a failure of a repository check.

    Parameters
    ----------
    name : str
        The name of the check, as its module declares it in ``CHECK``.

    Returns
    -------
    str
        Two lines: what the link is for, and the link to the check's section.

    """
    return (
        f"Why this check exists, and how to declare an exception:\n{PAGE}#{LABEL}{name}"
    )
