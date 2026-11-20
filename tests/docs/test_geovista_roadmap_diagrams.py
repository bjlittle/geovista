# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Unit-tests for the diagrams of the order between roadmap rows (diagram spec §4.4).

The extension is ``docs/src/_ext/geovista_roadmap_diagrams.py``. It sits in the
corpus the grammar governs, so these fixtures build each state's emoji, the
section sign and an ordering's opener by name, as the extension does.

"""

from __future__ import annotations

import html
import importlib.util
import io
from pathlib import Path
import re
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

#: The specifications of the real build.
SPECS = Path(__file__).parents[2] / "docs" / "src" / "developer" / "specs"

#: What the fixtures write, built by name rather than written.
SECTION = "\N{SECTION SIGN}"
ELLIPSIS = "\N{HORIZONTAL ELLIPSIS}"
LANDED = "\N{WHITE HEAVY CHECK MARK} landed (2026-01-01, 1)"
NOT_STARTED = "\N{CLIPBOARD} not started"
LINKED = " \N{MIDDLE DOT} \N{LINK SYMBOL}"

#: The configuration of the end-to-end build.
CONF = """
extensions = [
    "myst_parser",
    "sphinxcontrib.mermaid",
    "geovista_citation_xrefs",
    "geovista_roadmap_diagrams",
]
suppress_warnings = ["app", "myst.header"]
"""

#: Where a diagram, and the key beneath it, are drawn.
CONTAINER = '<div class="roadmap-diagram docutils container">'

#: A Mermaid block of a built page.
PRE = re.compile(r'<pre\b[^>]*\bclass="mermaid"[^>]*>\s*(.*?)\s*</pre>', re.DOTALL)


def specification(slug: str, *roadmaps: list[tuple[str, str]]) -> str:
    """Write a specification under ``<slug> spec``, a roadmap in each section from 3.

    Section 2 is a specification's Decisions, whose rows are not named.
    """
    prefix = slug.replace("-", " ")
    text = (
        f"# {slug.title()}\n\n"
        f"- **Citation prefix:** `{prefix} spec {SECTION}{ELLIPSIS}`\n\n"
        f"({slug}-spec-1)=\n## 1. Purpose\n\nText.\n"
    )
    for number, rows in enumerate(roadmaps, start=3):
        table = "".join(
            f"| {n} | {scope} | {status} |\n"
            for n, (scope, status) in enumerate(rows, start=1)
        )
        text += (
            f"\n({slug}-spec-{number})=\n## {number}. Roadmap\n\n"
            f"| # | Scope | Status |\n|---|---|---|\n{table}"
        )
    return text


#: The specifications of the project: demo orders against other, lone orders
#: nothing, and past's rows have all landed, one after the other.
PROJECT = {
    "2026-01-01-demo-design.md": specification(
        "demo",
        [
            ("One", LANDED),
            (f"Two{LINKED} after row 1", NOT_STARTED),
            (f"Three{LINKED} with row 1 of other spec {SECTION}3", NOT_STARTED),
        ],
    ),
    "2026-01-02-other-design.md": specification(
        "other", [("Theirs", NOT_STARTED), ("Unrelated", NOT_STARTED)]
    ),
    "2026-01-03-lone-design.md": specification("lone", [("Alone", NOT_STARTED)]),
    "2026-01-04-past-design.md": specification(
        "past", [("Then", LANDED), (f"Later{LINKED} after row 1", LANDED)]
    ),
}

#: The specifications index, which draws the open work.
INDEX = """Specifications
==============

.. toctree::

{toctree}

Open Work
---------

.. roadmap-open-work::
"""


@pytest.fixture(scope="module")
def diagrams(require: Callable[[str], NoReturn]) -> ModuleType:
    """Load the extension by path, or skip without sphinx."""
    try:
        import sphinx  # noqa: F401, PLC0415
        import sphinxcontrib.mermaid  # noqa: F401, PLC0415
    except ImportError:
        require("sphinx and sphinxcontrib-mermaid are needed")
    sys.path.insert(0, str(EXT))
    try:
        found = importlib.util.spec_from_file_location(
            "geovista_roadmap_diagrams", EXT / "geovista_roadmap_diagrams.py"
        )
        module = importlib.util.module_from_spec(found)
        sys.modules[found.name] = module
        found.loader.exec_module(module)
    finally:
        sys.path.remove(str(EXT))
    return module


def project(src: Path, specs: dict[str, str] | None = None, page: str = "") -> Path:
    """Write the project: its configuration, the specifications and their index."""
    specs = PROJECT if specs is None else specs
    folder = src / "developer" / "specs"
    folder.mkdir(parents=True, exist_ok=True)
    (src / "conf.py").write_text(CONF, encoding="utf-8")
    for name, text in specs.items():
        (folder / name).write_text(text, encoding="utf-8")
    toctree = textwrap.indent("\n".join(Path(name).stem for name in specs), " " * 3)
    (folder / "index.rst").write_text(INDEX.format(toctree=toctree), encoding="utf-8")
    pages = ["developer/specs/index"]
    if page:
        (src / "page.md").write_text(page, encoding="utf-8")
        pages.append("page")
    root = textwrap.indent("\n".join(pages), " " * 3)
    (src / "index.rst").write_text(
        f"Root\n====\n\n.. toctree::\n\n{root}\n", encoding="utf-8"
    )
    return src


def build(
    src: Path, out: Path, *, parallel: int = 0, builder: str = "html"
) -> tuple[Path, str]:
    """Build ``src``, returning its output and its warnings."""
    return built_with_status(src, out, parallel=parallel, builder=builder)[:2]


def built_with_status(
    src: Path, out: Path, *, parallel: int = 0, builder: str = "html"
) -> tuple[Path, str, str]:
    """Build ``src``, returning its output, its warnings and what it said it read.

    Each builder writes to a folder of its own, beside the doctrees they share.
    """
    from sphinx.application import Sphinx  # noqa: PLC0415
    from sphinx.util.docutils import docutils_namespace  # noqa: PLC0415

    warning = io.StringIO()
    status = io.StringIO()
    with pytest.MonkeyPatch.context() as patch, docutils_namespace():
        patch.syspath_prepend(str(EXT))
        app = Sphinx(
            str(src),
            str(src),
            str(out / builder),
            str(out / "doctrees"),
            builder,
            status=status,
            warning=warning,
            parallel=parallel,
        )
        app.build()
    return out / builder, warning.getvalue(), status.getvalue()


def updated(status: str) -> str:
    """Read what an incremental build found to update, as sphinx reports it."""
    plain = re.sub(r"\x1b\[[0-9;]*m", "", status)
    found = re.search(r"updating environment: (?:\[[^]]*\] )?(.*?) removed", plain)
    assert found is not None, plain
    return found[1] + " removed"


def blocks(page: Path) -> list[str]:
    """Read the Mermaid text of each diagram a built page draws."""
    return [html.unescape(m[1]) for m in PRE.finditer(page.read_text("utf-8"))]


def expected(diagrams: ModuleType, src: Path, docname: str | None) -> str:
    """Draw, with the grammar, the diagram a page should carry.

    ``docname`` is a specification's stem, or ``None`` for the open work.
    """
    citations = diagrams.geovista_citations
    specs = citations.specifications(src / "developer" / "specs")
    names = citations.namespace(specs)
    texts = {spec: spec.read_text(encoding="utf-8") for spec in specs}
    edges = citations.ordering_edges(texts, names)
    statuses = citations.row_statuses(texts, names)
    stems = {prefix: spec.stem for spec, prefix in names.owners.items()}
    if docname is None:
        rows, small = citations.open_work(edges, statuses), set()
    else:
        owner = next(p for s, p in names.owners.items() if s.stem == docname)
        rows, small = citations.roadmap_view(owner, edges, statuses)

    def href(anchor: str) -> str:
        stem = stems[citations.LABEL.match(anchor)["prefix"]]
        page = "" if stem == docname else f"{stem}.html"
        return f"{page}#{anchor}"

    return diagrams.FRONT_MATTER + citations.diagram(
        rows,
        edges,
        statuses,
        citations.row_labels(texts, names),
        small=small,
        links={anchor: href(anchor) for anchor in rows},
    )


def spec_page(html_dir: Path, stem: str) -> Path:
    """Locate a built specification."""
    return html_dir / "developer" / "specs" / f"{stem}.html"


@pytest.fixture(scope="module")
def built(diagrams, tmp_path_factory) -> tuple[Path, Path, str]:  # noqa: ARG001
    """Build the project once, for the tests that only read it."""
    root = tmp_path_factory.mktemp("built")
    src = project(root / "src", page=PAGE)
    html_dir, warning = build(src, root)
    return src, html_dir, warning


#: A page that is no specification, holding a table headed as a roadmap is.
PAGE = "# Page\n\n| # | Scope | Status |\n|---|---|---|\n| 1 | A row | Done |\n"


def test_a_specification_draws_its_diagram_under_its_roadmap_table(diagrams, built):
    """Directly after the roadmap table, the diagram drawn from the graph, then its key.

    Holds diagram spec §2 decision 3 and diagram spec §2 decision 2.
    """
    src, html_dir, warning = built
    text = spec_page(html_dir, "2026-01-01-demo-design").read_text("utf-8")

    assert warning == ""
    assert re.search(r"</table>\s*" + re.escape(CONTAINER), text)
    assert text.count(CONTAINER) == 1
    assert blocks(spec_page(html_dir, "2026-01-01-demo-design")) == [
        expected(diagrams, src, "2026-01-01-demo-design").strip(),
        (diagrams.KEY_FRONT_MATTER + diagrams.geovista_citations.diagram_key()).strip(),
    ]


@pytest.mark.usefixtures("diagrams")
def test_a_diagram_draws_light_at_its_own_size(built):
    """Each diagram, and its key, keeps its colours and its size on either theme.

    The page's dark theme would invert the colours of diagram spec §4.2, and the
    page shrinks a diagram to its width, which leaves the open work, many
    specifications wide, unreadable; the stylesheet of
    :func:`test_the_real_build_styles_the_diagrams` lets it scroll instead.
    """
    _, html_dir, _ = built
    theme = "---\nconfig:\n  theme: default\n  darkMode: false\n"
    # a small font and tight boxes, as the boxes show the row's number alone
    tight = (
        "  themeVariables:\n    fontSize: 12px\n  flowchart:\n    useMaxWidth: false\n"
    )
    for page in (
        spec_page(html_dir, "2026-01-01-demo-design"),
        html_dir / "developer" / "specs" / "index.html",
    ):
        drawn, key = blocks(page)
        assert drawn.startswith(
            theme + tight + "    padding: 6\n    nodeSpacing: 25\n    rankSpacing: 35\n"
        ), page.name
        assert key.startswith(
            theme + tight + "    padding: 6\n    nodeSpacing: 15\n    rankSpacing: 20\n"
        ), page.name


def test_a_roadmap_no_ordering_touches_draws_its_rows_alone(diagrams, built):
    """A roadmap with no ordering in or out draws its rows, with no arrow.

    Holds diagram spec §2 decision 10.
    """
    src, html_dir, _ = built
    page = spec_page(html_dir, "2026-01-03-lone-design")
    (drawn, _) = blocks(page)

    assert page.read_text("utf-8").count(CONTAINER) == 1
    assert drawn == expected(diagrams, src, "2026-01-03-lone-design").strip()
    assert '    lone_spec_3_row_1["1"]' in drawn.splitlines()
    assert not any(arrow in drawn for arrow in (" --> ", " <==> ", " -.-> "))


def test_a_diagram_draws_other_rows_small_in_their_own_colour(built):
    """Another specification's row is drawn small, in its state's colour.

    Other's row 1 lands with demo's row 3, and nothing either waits on has to land,
    so it is ready, and drawn so. Holds diagram spec §2 decision 10.
    """
    _, html_dir, _ = built
    (drawn, _) = blocks(spec_page(html_dir, "2026-01-01-demo-design"))

    assert "  class other_spec_3_row_1 gv_ready_small\n" in drawn
    assert "other_spec_3_row_2" not in drawn


def test_a_link_names_the_page_and_the_row_without_reading_it(built):
    """A row links to its own anchor, on its page; one of another page by its name.

    Holds diagram spec §2 decision 7.
    """
    _, html_dir, _ = built
    (drawn, _) = blocks(spec_page(html_dir, "2026-01-01-demo-design"))
    other = spec_page(html_dir, "2026-01-02-other-design").read_text("utf-8")

    lines = drawn.splitlines()
    assert '  click demo_spec_3_row_1 href "#demo-spec-3-row-1" "1: One"' in lines
    assert (
        "  click other_spec_3_row_1 href "
        '"2026-01-02-other-design.html#other-spec-3-row-1" "1: Theirs"'
    ) in lines
    assert 'id="other-spec-3-row-1"' in other


def test_the_index_draws_the_open_work(diagrams, built):
    """The index's directive draws the open work, and its key.

    Holds diagram spec §2 decision 1 and diagram spec §2 decision 4.
    """
    src, html_dir, _ = built

    drawn = blocks(html_dir / "developer" / "specs" / "index.html")

    # past's rows are history, which only its own diagram draws
    assert "past_spec" not in drawn[0]
    assert drawn == [
        expected(diagrams, src, None).strip(),
        (diagrams.KEY_FRONT_MATTER + diagrams.geovista_citations.diagram_key()).strip(),
    ]


def test_a_page_that_is_no_specification_draws_nothing(built):
    """Review Focus 2 of its plan: a roadmap's header elsewhere draws nothing."""
    _, html_dir, _ = built

    assert CONTAINER not in (html_dir / "page.html").read_text("utf-8")


@pytest.mark.usefixtures("diagrams")
def test_a_diagram_follows_the_last_roadmap_table(tmp_path):
    """Review Focus 1 of its plan: two roadmap tables, one diagram, after the second."""
    specs = dict(PROJECT)
    specs["2026-01-01-demo-design.md"] = specification(
        "demo",
        [("One", LANDED)],
        [(f"Two{LINKED} after row 1 of {SECTION}3", NOT_STARTED)],
    )
    src = project(tmp_path / "src", specs)

    html_dir, _ = build(src, tmp_path)
    text = spec_page(html_dir, "2026-01-01-demo-design").read_text("utf-8")

    assert text.count(CONTAINER) == 1
    assert text.index(CONTAINER) > text.rindex("</table>")


def test_an_incremental_build_redraws_after_another_specification_changes(
    diagrams, tmp_path
):
    """Review Focus 4 of its plan: another roadmap's row lands, a diagram follows."""
    src = project(tmp_path / "src")
    build(src, tmp_path)
    other = src / "developer" / "specs" / "2026-01-02-other-design.md"
    other.write_text(
        specification("other", [("Theirs", LANDED), ("Unrelated", NOT_STARTED)]),
        encoding="utf-8",
    )

    html_dir, _ = build(src, tmp_path)
    (drawn, _) = blocks(spec_page(html_dir, "2026-01-01-demo-design"))

    assert drawn == expected(diagrams, src, "2026-01-01-demo-design").strip()
    assert "  class other_spec_3_row_1 gv_landed_small\n" in drawn


def test_an_incremental_build_redraws_after_a_specification_is_added(
    diagrams, tmp_path
):
    """A new specification ordering against demo's row redraws demo's diagram."""
    src = project(tmp_path / "src")
    build(src, tmp_path)
    folder = src / "developer" / "specs"
    (folder / "2026-01-05-new-design.md").write_text(
        specification(
            "new", [(f"Later{LINKED} after row 2 of demo spec {SECTION}3", NOT_STARTED)]
        ),
        encoding="utf-8",
    )
    index = (folder / "index.rst").read_text("utf-8")
    (folder / "index.rst").write_text(
        index.replace(
            "2026-01-04-past-design\n",
            "2026-01-04-past-design\n   2026-01-05-new-design\n",
        ),
        encoding="utf-8",
    )

    html_dir, _ = build(src, tmp_path)
    (drawn, _) = blocks(spec_page(html_dir, "2026-01-01-demo-design"))

    assert "new_spec_3_row_1" in drawn
    assert drawn == expected(diagrams, src, "2026-01-01-demo-design").strip()


@pytest.mark.usefixtures("diagrams")
def test_an_unchanged_build_reads_nothing_again(tmp_path):
    """A build after one that changed nothing re-reads no page.

    A dependency sphinx cannot read as a file, as a folder, marks its page changed
    on every build, so each specification would be read again every time.
    """
    src = project(tmp_path / "src")
    build(src, tmp_path)

    _, _, status = built_with_status(src, tmp_path)

    assert updated(status) == "0 added, 0 changed, 0 removed"


@pytest.mark.usefixtures("diagrams")
def test_an_edit_reads_again_only_the_pages_that_draw_a_diagram(tmp_path):
    """Another roadmap's row lands: each page drawing a diagram is read again.

    The root page draws none, so it is left alone.
    """
    src = project(tmp_path / "src")
    build(src, tmp_path)
    other = src / "developer" / "specs" / "2026-01-02-other-design.md"
    other.write_text(
        specification("other", [("Theirs", LANDED), ("Unrelated", NOT_STARTED)]),
        encoding="utf-8",
    )

    _, _, status = built_with_status(src, tmp_path)

    assert updated(status) == "0 added, 5 changed, 0 removed"


@pytest.mark.usefixtures("diagrams")
def test_the_extension_brings_the_rows_it_links_to(tmp_path):
    """A row's link lands, though the configuration names only this extension.

    It sets up ``geovista_citation_xrefs``, which names each row its link points
    to, and reads every page again when a specification comes or goes.
    """
    src = project(tmp_path / "src")
    conf = (src / "conf.py").read_text("utf-8")
    (src / "conf.py").write_text(
        conf.replace('    "geovista_citation_xrefs",\n', ""), encoding="utf-8"
    )

    html_dir, _ = build(src, tmp_path)

    assert 'id="other-spec-3-row-1"' in spec_page(
        html_dir, "2026-01-02-other-design"
    ).read_text("utf-8")


@pytest.mark.usefixtures("diagrams")
def test_a_dirhtml_build_after_html_links_its_own_pages(tmp_path):
    """A link is the page's builder's, though another builder read the page first.

    The doctrees are shared, so a link worked out as the page was read would keep
    the html builder's file name in the dirhtml build.
    """
    src = project(tmp_path / "src")
    build(src, tmp_path)

    out, _ = build(src, tmp_path, builder="dirhtml")
    page = out / "developer" / "specs" / "2026-01-01-demo-design" / "index.html"
    (drawn, _) = blocks(page)

    assert (
        "  click other_spec_3_row_1 href "
        '"../2026-01-02-other-design/#other-spec-3-row-1" "1: Theirs"'
    ) in drawn.splitlines()


@pytest.mark.usefixtures("diagrams")
def test_an_html_build_after_a_text_build_links_other_pages(tmp_path):
    """A builder whose pages have no address first leaves html's links whole."""
    src = project(tmp_path / "src")
    build(src, tmp_path, builder="text")

    out, _ = build(src, tmp_path)
    (drawn, _) = blocks(out / "developer" / "specs" / "index.html")

    assert (
        "  click other_spec_3_row_1 href "
        '"2026-01-02-other-design.html#other-spec-3-row-1" "1: Theirs"'
    ) in drawn.splitlines()


@pytest.mark.usefixtures("diagrams")
def test_a_latex_build_draws_without_raising(tmp_path):
    """A builder that cannot link a page draws its rows without links.

    The document holds demo's page alone, so latex can address no other page,
    and the rows of other specifications demo's diagram draws go unlinked.
    """
    src = project(tmp_path / "src")
    conf = (src / "conf.py").read_text("utf-8")
    (src / "conf.py").write_text(
        conf
        + 'mermaid_cmd = "false"\n'
        + "latex_documents = [\n"
        + '    ("developer/specs/2026-01-01-demo-design", "demo.tex", "Demo", "a",'
        + ' "manual"),\n'
        + "]\n",
        encoding="utf-8",
    )

    out, _ = build(src, tmp_path, builder="latex")

    assert any(out.glob("*.tex"))


def test_each_diagram_carries_its_id(built):
    """The diagram and its key carry ids, which a full-screen copy keeps.

    The stylesheet reads them there, outside the diagram's container, so a dark
    page draws the copy in its own colours too.
    """
    _, html_dir, _ = built
    text = spec_page(html_dir, "2026-01-01-demo-design").read_text("utf-8")

    assert re.search(r'<pre\s+id="roadmap-diagram"\s+class="mermaid">', text)
    assert re.search(r'<pre\s+id="roadmap-diagram-key"\s+class="mermaid">', text)


def test_a_parallel_build_draws_as_a_serial_build(diagrams, tmp_path):  # noqa: ARG001
    """Review Focus 5 of its plan: two workers draw every page as one does."""
    serial, _ = build(project(tmp_path / "serial" / "src"), tmp_path / "serial")
    parallel, _ = build(
        project(tmp_path / "parallel" / "src"), tmp_path / "parallel", parallel=2
    )

    pages = sorted(p.relative_to(serial) for p in serial.rglob("*.html"))
    assert pages
    for page in pages:
        assert blocks(parallel / page) == blocks(serial / page), page


def test_the_extension_builds_its_emoji_by_name():
    """The module sits in the corpus it serves, so writes no emoji literally (#2787)."""
    source = (EXT / "geovista_roadmap_diagrams.py").read_text(encoding="utf-8")

    assert not [char for char in source if ord(char) > 0x2000]


def test_the_real_build_draws_every_specification(html_root, diagrams):
    """On the real build, every specification draws one diagram, ordered or not.

    Holds diagram spec §2 decision 2.
    """
    citations = diagrams.geovista_citations
    specs = citations.specifications(SPECS)
    names = citations.namespace(specs)
    texts = {spec: spec.read_text(encoding="utf-8") for spec in specs}
    edges = citations.ordering_edges(texts, names)
    statuses = citations.row_statuses(texts, names)
    folder = html_root / "developer" / "specs"

    for spec, owner in names.owners.items():
        rows, _ = citations.roadmap_view(owner, edges, statuses)
        page = (folder / f"{spec.stem}.html").read_text(encoding="utf-8")
        assert page.count('class="roadmap-diagram') == 1, spec.name
        if not rows:
            continue
        before = page[: page.index('class="roadmap-diagram')]
        table = before[before.rindex("<table") :]
        own = [row for row in rows if row.startswith(f"{owner}-")]
        assert f'id="{own[-1]}"' in table, spec.name
    for page in [*folder.glob("*.html")]:
        for block in blocks(page):
            for target in re.findall(r'click \S+ href "([^"]*)"', block):
                where, _, anchor = target.partition("#")
                linked = (folder / where) if where else page
                assert f'id="{anchor}"' in linked.read_text("utf-8"), target
    assert (folder / "index.html").read_text("utf-8").count(
        'class="roadmap-diagram'
    ) == 1


def test_the_real_build_styles_the_diagrams(html_root):
    """The real build carries the stylesheet that lets a diagram keep its size.

    It applies to the diagrams of this extension alone, and sets their ground, so
    a dark page shows their arrows.
    """
    page = (html_root / "developer" / "specs" / "index.html").read_text("utf-8")
    sheet = (html_root / "_static" / "roadmap_diagrams.css").read_text("utf-8")

    assert "roadmap_diagrams.css" in page
    rules = [line for line in sheet.splitlines() if "{" in line]
    assert rules
    assert all("roadmap-diagram" in line for line in rules)
    assert "max-width: none !important" in sheet
    assert "background" in sheet
    # the theme inverts a diagram on a dark page, which would turn ready from green,
    # and a full-screen copy leaves the container, so the rule reads the id
    assert 'html[data-theme=dark] pre.mermaid[id^="roadmap-diagram"] > svg {' in sheet
    assert "filter: none" in sheet
