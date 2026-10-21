# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Unit-tests for the parallel build parity extension in ``docs/src/_ext``.

Each test builds a small project with ``--jobs 2``, once with the extension and
once without, so that the upstream behaviour it works around is pinned down as
well as the fix. Once a test of the bare build fails, upstream has fixed that
behaviour and the matching part of the extension can go.

"""

from __future__ import annotations

import io
import os
from pathlib import Path
import pickle
import re
import textwrap
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from collections.abc import Callable
    from typing import NoReturn

EXT = Path(__file__).parents[2] / "docs" / "src" / "_ext"

#: The pages of the project, enough that a worker writes most of them.
PAGES = [f"page{index}" for index in range(6)]

#: A module whose constant is an instance of a class from another module, so
#: that ``viewcode`` follows it there.
MODULE = '''
"""A module re-exporting an instance from the standard library."""

from fractions import Fraction

#: One half.
HALF = Fraction(1, 2)


def double(value):
    """Double the value."""
    return 2 * value
'''

#: A module re-exporting a function, documented on a page read before the page
#: of the module defining it, as the "geovista" package page is read before the
#: page of each module it re-exports from.
REEXPORT = '''
"""A module re-exporting a function."""

from parity_module import double

__all__ = ["double"]
'''

#: A link from a module code page back to the documentation of an object.
BACK = re.compile(r'class="viewcode-back" href="([^"#]+)#([^"]+)"')

#: The configuration, recording the process that reads each page. The page that
#: sorts first is slow to read, so that its worker always finishes, and has its
#: reads merged, last.
CONF = """
import os
from pathlib import Path
import time

extensions = {extensions!r}


def record(app, docname, source):
    path = Path(app.outdir).parent / "pids" / docname
    path.parent.mkdir(exist_ok=True)
    path.write_text(str(os.getpid()))
    if docname == "a_reexport":
        time.sleep(1)


def setup(app):
    app.connect("source-read", record)
"""

#: The script that "sphinx-tippy" writes for each page, as the page names it.
TIPS = re.compile(r'src="(_static/tippy/[^"]+\.js)"')


def _docs(html: Path) -> list[str]:
    """Load the pages the build environment records, in its order."""
    with (html.parent / "doctrees" / "environment.pickle").open("rb") as handle:
        env = pickle.load(handle)  # noqa: S301
    return list(env.all_docs)


def _build(root: Path, *, parity: bool) -> tuple[Path, str]:
    """Build the project in parallel, with or without the extension."""
    from sphinx.application import Sphinx  # noqa: PLC0415
    from sphinx.util.docutils import docutils_namespace  # noqa: PLC0415

    src = root / "src"
    src.mkdir()
    extensions = ["sphinx.ext.autodoc", "sphinx.ext.viewcode", "sphinx_tippy"]
    if parity:
        extensions.insert(0, "parallel_build")
    (src / "conf.py").write_text(CONF.format(extensions=extensions))
    (src / "parity_module.py").write_text(MODULE)
    (src / "parity_reexport.py").write_text(REEXPORT)
    (src / "a_reexport.rst").write_text(
        "Re-export\n=========\n\n.. automodule:: parity_reexport\n"
        "   :members:\n   :imported-members:\n"
    )
    toctree = textwrap.indent("\n".join([*PAGES, "a_reexport", "api"]), " " * 3)
    (src / "index.rst").write_text(f"Index\n=====\n\n.. toctree::\n\n{toctree}\n")
    for page in PAGES:
        (src / f"{page}.rst").write_text(f"{page}\n{'=' * len(page)}\n\nText.\n")
    (src / "api.rst").write_text(
        "API\n===\n\n.. automodule:: parity_module\n   :members:\n"
    )

    warning = io.StringIO()
    # each build registers its nodes and directives with docutils, which
    # warns of any a previous build in the process left behind, so scope them
    # to the build as "sphinx-build" does
    with pytest.MonkeyPatch.context() as patch, docutils_namespace():
        # the build imports the module and the extension by bare name, and the
        # workers it forks inherit the path
        patch.syspath_prepend(str(src))
        patch.syspath_prepend(str(EXT))
        app = Sphinx(
            str(src),
            str(src),
            str(root / "html"),
            str(root / "doctrees"),
            "html",
            status=None,
            warning=warning,
            parallel=2,
        )
        app.build()

    return root / "html", warning.getvalue()


@pytest.fixture(scope="module")
def prerequisites(require: Callable[[str], NoReturn]) -> None:
    """Skip, or fail under ``--browser-strict``, without the build packages."""
    try:
        import sphinx  # noqa: F401, PLC0415
    except ImportError:
        require("sphinx is not installed")

    try:
        import sphinx_tippy  # noqa: F401, PLC0415
    except ImportError:
        require("sphinx-tippy is not installed")


@pytest.fixture(scope="module")
def bare(prerequisites, tmp_path_factory) -> Path:  # noqa: ARG001
    """Provide a parallel build without the extension."""
    html, _ = _build(tmp_path_factory.mktemp("bare"), parity=False)
    return html


@pytest.fixture(scope="module")
def parity(prerequisites, tmp_path_factory) -> tuple[Path, str]:  # noqa: ARG001
    """Provide a parallel build with the extension, and its warnings."""
    return _build(tmp_path_factory.mktemp("parity"), parity=True)


def _missing_tips(html: Path) -> list[str]:
    """Find each page whose tippy script was never written."""
    missing = []
    for page in ["index", "a_reexport", "api", *PAGES]:
        scripts = TIPS.findall((html / f"{page}.html").read_text())
        if not scripts or not all((html / script).is_file() for script in scripts):
            missing.append(page)
    return missing


def test_tippy_loses_the_tips_of_a_page_written_by_a_worker(bare):
    """Test sphinx-tippy alone loses the tips of a page written in parallel.

    When this fails, sphinx-tippy writes in parallel safely, and the serial
    write in the extension can go. See sphinx-extensions2/sphinx-tippy#9.

    """
    assert _missing_tips(bare)


def test_viewcode_renders_a_module_nothing_documented_is_in(bare):
    """Test viewcode alone renders a module a parallel read only passed through.

    When this fails, viewcode merges its parallel reads as a serial read would
    leave them, and the pruning in the extension can go. See
    sphinx-doc/sphinx#14675.

    """
    assert (bare / "_modules" / "fractions.html").is_file()


def _broken_back_links(html: Path) -> list[str]:
    """Find each module code link back to an object its page does not hold."""
    page = html / "_modules" / "parity_module.html"
    links = BACK.findall(page.read_text())
    assert links, "no back links found, so there is nothing to check"
    return [
        f"{target}#{anchor}"
        for target, anchor in links
        if f'id="{anchor}"' not in (page.parent / target).read_text()
    ]


def test_viewcode_links_back_to_the_module_first_read(bare):
    """Test viewcode alone links back by the module of the first page read.

    The page re-exporting the function is read first, so viewcode links back
    to the function by that module, which its own page does not use. A serial
    build does the same. When this fails, viewcode links back correctly, and
    the relinking in the extension can go. See sphinx-doc/sphinx#6651.

    """
    assert _broken_back_links(bare) == ["../api.html#parity_reexport.double"]


def test_sphinx_records_the_pages_in_the_order_their_reads_merge(bare):
    """Test sphinx alone records the pages in the order the reads merge.

    The worker reading the first pages finishes last, so they are recorded
    last. A serial build records them in the order it reads them, which is
    sorted, and ``sphinx-llms-txt`` follows this order where a page has no
    toctree. When this fails, sphinx records the pages in a stable order, and
    the sorting in the extension can go. See jdillard/sphinx-llms-txt#76,
    whose fix would make the order of the pages irrelevant to it.

    """
    docs = _docs(bare)
    assert docs != sorted(docs)


def test_pages_recorded_sorted(parity):
    """Test the pages are recorded in the order a serial build reads them."""
    html, _ = parity
    docs = _docs(html)
    assert docs == sorted(docs)


def test_back_links_land(parity):
    """Test every module code link back to an object lands on it."""
    html, _ = parity
    assert _broken_back_links(html) == []


def test_tips_kept(parity):
    """Test every page keeps its tips."""
    html, _ = parity
    assert _missing_tips(html) == []


def test_module_code_documented_only(parity):
    """Test the module code pages are those of the documented modules only."""
    html, _ = parity
    assert (html / "_modules" / "parity_module.html").is_file()
    assert not (html / "_modules" / "fractions.html").exists()


def _alive(pid: int) -> bool:
    """Report whether the process is running, rather than a zombie or gone."""
    try:
        state = Path(f"/proc/{pid}/stat").read_text().rsplit(")", 1)[1].split()[0]
    except FileNotFoundError:
        return False
    return state != "Z"


def test_gallery_workers_released(require, monkeypatch):
    """Test the idle gallery workers stop before the pages are read.

    sphinx-gallery runs the examples in a reusable pool of loky workers, which
    otherwise stay alive and keep their memory for five minutes, and so through
    reading the pages beside the processes reading them. See
    sphinx-gallery/sphinx-gallery#1658.

    """
    try:
        from joblib import Parallel, delayed  # noqa: PLC0415
    except ImportError:
        require("joblib is not installed")

    if not Path("/proc").is_dir():
        pytest.skip("requires /proc to inspect the workers")

    monkeypatch.syspath_prepend(str(EXT))
    import parallel_build  # noqa: PLC0415

    # as sphinx-gallery runs the examples
    pids = set(Parallel(n_jobs=2, backend="loky")(delayed(os.getpid)() for _ in "ab"))
    assert pids
    assert all(_alive(pid) for pid in pids)

    parallel_build.release_gallery_workers(None, None, [])

    assert not any(_alive(pid) for pid in pids)


def test_read_in_parallel(parity):
    """Test the pages are still read by more than one process."""
    html, _ = parity
    pids = {path.read_text() for path in (html.parent / "pids").iterdir()}
    assert len(pids) > 1
    assert str(os.getpid()) not in pids


def test_serial_write_unwarned(parity):
    """Test writing serially warns of nothing, as ``--fail-on-warning`` would fail.

    Sphinx warns when an extension is unsafe for parallel writing, and again
    that it is writing serially. Other tests leave directives registered, which
    a build here warns of too, so only the warnings of serial writing count.

    """
    _, warnings = parity
    assert "parallel writing" not in warnings
    assert "doing serial" not in warnings
