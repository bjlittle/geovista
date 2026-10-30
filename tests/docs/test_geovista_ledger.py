# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Tests of the summary line the build writes under each Verification table.

The extension is ``docs/src/_ext/geovista_ledger.py``, loaded here by path as the
citation transform's tests load theirs. This module sits inside the corpus the
citation grammar governs, so it builds its emojis rather than write them.

"""

from __future__ import annotations

import importlib.util
import io
from pathlib import Path
import sys
import textwrap
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from collections.abc import Callable
    from types import ModuleType
    from typing import NoReturn

#: The extensions, which import one another by bare name, as a build does.
EXT = Path(__file__).parents[2] / "docs" / "src" / "_ext"

#: The states of ledger spec §3.4, built by name: see the module docstring.
PENDING = "\N{HOURGLASS WITH FLOWING SAND} pending"
VERIFIED = "\N{WHITE HEAVY CHECK MARK} verified"
SIGNED_OFF = "\N{WRITING HAND}\N{VARIATION SELECTOR-16} signed off"
RETIRED = "\N{FILE CABINET}\N{VARIATION SELECTOR-16} retired"


@pytest.fixture(scope="module")
def ledger(require: Callable[[str], NoReturn]) -> ModuleType:
    """Load the extension by path, or skip without sphinx."""
    try:
        import sphinx  # noqa: F401, PLC0415
    except ImportError:
        require("sphinx is not installed")
    sys.path.insert(0, str(EXT))
    try:
        spec = importlib.util.spec_from_file_location(
            "geovista_ledger", EXT / "geovista_ledger.py"
        )
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
    finally:
        sys.path.remove(str(EXT))
    return module


def test_summary_counts_each_state(ledger):
    """The line the build writes for ledger spec §2 decision 5 counts every state."""
    statuses = [VERIFIED, VERIFIED, VERIFIED, PENDING, RETIRED, SIGNED_OFF]

    assert ledger.summary(statuses) == (
        f"{VERIFIED[0]} 3 · {SIGNED_OFF[:2]} 1 · {PENDING[0]} 1 · {RETIRED[:2]} 1: "
        "4 of 5 decisions in force verified"
    )


def test_summary_reads_a_status_with_its_parenthetical(ledger):
    """A status carries its date and pull request, which the count reads past."""
    assert ledger.summary([f"{VERIFIED} (2026-10-30, {{pull}}`1`)"]).endswith(
        "1 of 1 decisions in force verified"
    )


def test_summary_reads_a_state_without_its_variation_selector(ledger):
    """A retirement typed without U+FE0F still counts as one."""
    summary = ledger.summary(["\N{FILE CABINET} retired", PENDING])

    assert summary.endswith("0 of 1 decisions in force verified")


#: The configuration of the end-to-end build.
CONF = """
extensions = ["geovista_ledger", "myst_parser"]
suppress_warnings = ["app"]
"""

#: A specification with a ledger of two decisions, one verified.
SPEC = f"""# Demo

(demo-spec-1)=
## 1. Verification

| Decision | Status | Evidence |
|---|---|---|
| 1 | {VERIFIED} (2026-10-30, 1) | `x.py` |
| 2 | {PENDING} | |

After the table.
"""


def build(src: Path, out: Path) -> tuple[Path, str]:
    """Build ``src``, returning its HTML and its warnings."""
    from sphinx.application import Sphinx  # noqa: PLC0415
    from sphinx.util.docutils import docutils_namespace  # noqa: PLC0415

    warning = io.StringIO()
    with pytest.MonkeyPatch.context() as patch, docutils_namespace():
        patch.syspath_prepend(str(EXT))
        app = Sphinx(
            str(src),
            str(src),
            str(out / "html"),
            str(out / "doctrees"),
            "html",
            status=None,
            warning=warning,
        )
        app.build()
    return out / "html", warning.getvalue()


@pytest.mark.usefixtures("ledger")
def test_a_build_writes_the_summary_under_the_table(tmp_path):
    """The summary follows the table, so nobody keeps it up to date by hand."""
    src = tmp_path / "src"
    src.mkdir()
    (src / "conf.py").write_text(CONF, encoding="utf-8")
    (src / "spec.md").write_text(SPEC, encoding="utf-8")
    toctree = textwrap.indent("spec", " " * 3)
    (src / "index.rst").write_text(f"Index\n=====\n\n.. toctree::\n\n{toctree}\n")

    html, warning = build(src, tmp_path)
    page = (html / "spec.html").read_text(encoding="utf-8")

    assert warning == ""
    table_end = page.index("</table>")
    summary = page.index("1 of 2 decisions in force verified")
    assert table_end < summary < page.index("After the table.")
    assert 'class="ledger-summary"' in page
