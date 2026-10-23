# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Tests that every repository check is documented, and that its failures say where.

Each module that holds the repository to a rule of ``geovista``'s own declares the
name of its section on the repository checks page, as ``CHECK``. A failure of such
a check ends with a link to that section, which says why the rule exists and how
to declare an exception to it.

See "docs/src/developer/specs/2026-10-23-repository-checks-design.md".

"""

from __future__ import annotations

import ast
from pathlib import Path
import re
import sys

import pytest

#: The section of the repository checks page that documents this check.
CHECK = "repository-checks"

#: The repository root.
REPO = Path(__file__).parents[1]

#: The module holding the text of the breadcrumb.
BREADCRUMB = REPO / ".github" / "scripts" / "breadcrumb.py"

#: A check module for "pytester" to run: one failure, one setup error, one skip
#: and one pass, so that each kind of report is seen.
DEMO = """
import pytest

CHECK = "demo"


@pytest.fixture
def broken():
    raise RuntimeError("setup fails")


def test_fails():
    assert 1 == 2


def test_errors(broken):
    pass


def test_skips():
    pytest.skip("skipped")


def test_passes():
    pass
"""


def test_breadcrumb_names_the_section(breadcrumb):
    """The breadcrumb is the text of checks spec §3.3, naming the section."""
    assert breadcrumb.breadcrumb("image-marker") == (
        "Why this check exists, and how to declare an exception:\n"
        "https://geovista.readthedocs.io/en/latest/developer/checks.html"
        "#gv-developer-checks-image-marker"
    )


def test_breadcrumb_needs_no_dependency():
    """The changelog workflow runs its script with "click" and "towncrier" alone."""
    tree = ast.parse(BREADCRUMB.read_text(encoding="utf-8"))
    imported = {
        alias.name.partition(".")[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    } | {
        node.module.partition(".")[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module
    }
    assert imported <= set(sys.stdlib_module_names) | {"__future__"}


@pytest.mark.parametrize("workers", [[], ["-n", "2"]], ids=["serial", "xdist"])
def test_hook_adds_the_breadcrumb(pytester, monkeypatch, workers):
    """A failure and an error in a check module end with its breadcrumb.

    A skip and a pass do not. Every CI test job runs under "pytest-xdist", so the
    breadcrumb must also survive a report's trip from a worker.

    """
    pytester.makepyfile(test_demo=DEMO)
    monkeypatch.setenv("PYTHONPATH", str(REPO))
    result = pytester.runpytest_subprocess(
        "-p", "tests.conftest", "-p", "no:cacheprovider", *workers
    )
    assert result.ret == pytest.ExitCode.TESTS_FAILED
    assert result.stdout.str().count("#gv-developer-checks-demo") == 2


def test_hook_ignores_a_module_without_check(pytester, monkeypatch):
    """A failure in a module that declares no check carries no breadcrumb."""
    pytester.makepyfile(test_plain=DEMO.replace('CHECK = "demo"', ""))
    monkeypatch.setenv("PYTHONPATH", str(REPO))
    result = pytester.runpytest_subprocess(
        "-p", "tests.conftest", "-p", "no:cacheprovider"
    )
    assert result.ret == pytest.ExitCode.TESTS_FAILED
    assert "gv-developer-checks-" not in result.stdout.str()


#: The page that documents every repository check.
PAGE = REPO / "docs" / "src" / "developer" / "checks.rst"

#: A well-formed name: lower-case words joined by hyphens.
NAME = re.compile(r"[a-z0-9]+(-[a-z0-9]+)*")

#: The label of a check's section, and of its tooltip.
LABEL = re.compile(r"^\.\. _(?P<tippy>tippy-)?gv-developer-checks-(?P<name>[^:]+):$")

#: The target of a row's cross-reference to a check's section.
ROW = re.compile(r":ref:`[^`<]*<gv-developer-checks-(?P<name>[^>]+)>`")

#: How a check's module declares it.
CONSTANT = "CHECK"

#: Where every message points, for the rules the gate holds.
SEE = "see checks spec §3.4"


def declared(root: Path) -> dict[str | None, list[Path]]:
    """Gather the name each check module declares, and where.

    Parameters
    ----------
    root : Path
        The repository root, whose ``tests`` and ``.github/scripts`` are read.

    Returns
    -------
    dict
        Each name, with the modules declaring it. A ``CHECK`` the gate cannot
        read, as it is not a literal string assigned at the top of its module,
        is gathered under ``None``, so that it is reported rather than taken for
        a module with no check. That covers unpacking, a binding inside a block,
        and an import, any of which the pytest hook would still read.

    """
    modules = [
        *sorted((root / "tests").rglob("*.py")),
        *sorted((root / ".github" / "scripts").glob("*.py")),
    ]
    found: dict[str | None, list[Path]] = {}
    for module in modules:
        tree = ast.parse(module.read_text(encoding="utf-8"))
        read: set[int] = set()
        for node in tree.body:
            if isinstance(node, ast.Assign):
                targets, value = node.targets, node.value
            elif isinstance(node, ast.AnnAssign) and node.value is not None:
                targets, value = [node.target], node.value
            else:
                continue
            named = [t for t in targets if isinstance(t, ast.Name) and t.id == CONSTANT]
            if named:
                read.update(id(target) for target in named)
                literal = isinstance(value, ast.Constant) and isinstance(
                    value.value, str
                )
                name = value.value if literal else None
                found.setdefault(name, []).append(module.relative_to(root))
        # any other binding of the module's name, which the gate cannot read
        if any(id(node) not in read for node in _bindings(tree)):
            found.setdefault(None, []).append(module.relative_to(root))
    return found


def _bindings(tree: ast.Module) -> list[ast.AST]:
    """Find every node that binds ``CHECK`` in a module's own namespace.

    That is what the pytest hook reads, as ``item.module.CHECK``, so this follows
    Python's scopes. A function, a lambda or a class runs its body in a scope of
    its own, which binds nothing in the module unless that scope itself declares
    the name ``global``. Its decorators, defaults and bases run in the enclosing
    scope, though. A comprehension's loop targets are its own, but an assignment
    expression inside it binds the enclosing scope. An import binds the name it
    is given ``as``, or the first part of the module it imports.

    Parameters
    ----------
    tree : ast.Module
        The parsed module.

    Returns
    -------
    list of ast.AST
        The binding nodes, each an ``ast.Name`` stored to or an ``ast.alias``.

    """
    found: list[ast.AST] = []
    scopes = ast.FunctionDef | ast.AsyncFunctionDef | ast.Lambda | ast.ClassDef

    def declared(scope: ast.AST) -> set[str]:
        """Return the names a scope itself declares global, not its inner ones."""
        names: set[str] = set()
        pending = list(ast.iter_child_nodes(scope))
        while pending:
            node = pending.pop()
            if isinstance(node, ast.Global):
                names.update(node.names)
            if not isinstance(node, scopes):
                pending.extend(ast.iter_child_nodes(node))
        return names

    def visit(node: ast.AST, *, module: bool, shared: set[str]) -> None:
        enclosing = {"module": module, "shared": shared}
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef | ast.Lambda):
            outer = [*node.args.defaults, *node.args.kw_defaults]
            if not isinstance(node, ast.Lambda):
                outer += node.decorator_list
            for part in outer:
                if part is not None:
                    visit(part, **enclosing)
            body = [node.body] if isinstance(node, ast.Lambda) else node.body
            for part in body:
                visit(part, module=False, shared=declared(node))
        elif isinstance(node, ast.ClassDef):
            for part in [*node.decorator_list, *node.bases, *node.keywords]:
                visit(part, **enclosing)
            for part in node.body:
                visit(part, module=False, shared=declared(node))
        elif isinstance(
            node, ast.ListComp | ast.SetComp | ast.DictComp | ast.GeneratorExp
        ):
            # the loop targets are the comprehension's own, so they are skipped
            for generator in node.generators:
                for part in [generator.iter, *generator.ifs]:
                    visit(part, **enclosing)
            for name in ("elt", "key", "value"):
                if (part := getattr(node, name, None)) is not None:
                    visit(part, **enclosing)
        else:
            stored = (
                isinstance(node, ast.Name)
                and node.id == CONSTANT
                and isinstance(node.ctx, ast.Store)
            )
            imported = (
                isinstance(node, ast.alias)
                and (node.asname or node.name.partition(".")[0]) == CONSTANT
            )
            if (stored or imported) and (module or CONSTANT in shared):
                found.append(node)
            for child in ast.iter_child_nodes(node):
                visit(child, **enclosing)

    visit(tree, module=True, shared=set())
    return found


def documented(text: str) -> tuple[list[str], list[str], set[str]]:
    """Read the sections and the rows of the repository checks page.

    Parameters
    ----------
    text : str
        The page, as text.

    Returns
    -------
    tuple
        The names of the sections carrying both labels, and the names the rows
        of the lookup table link to, which are the cross-references before the
        first section, each in page order with any duplicate kept; and every name
        that has any label, so that a half-deleted section is still seen.

    """
    lines = text.splitlines()
    labels = [
        (i, match) for i, line in enumerate(lines) if (match := LABEL.match(line))
    ]
    first = labels[0][0] if labels else len(lines)
    plain = [m["name"] for _, m in labels if not m["tippy"]]
    tippy = {m["name"] for _, m in labels if m["tippy"]}
    sections = [name for name in plain if name in tippy]
    rows = [m["name"] for line in lines[:first] for m in ROW.finditer(line)]
    labelled = {m["name"] for _, m in labels}
    return sections, rows, labelled


def disagreements(root: Path, page: Path) -> list[str]:
    """Report every way the checks and the page disagree.

    Parameters
    ----------
    root : Path
        The repository root.
    page : Path
        The repository checks page.

    Returns
    -------
    list of str
        One message for each fault, empty when they agree.

    """
    found = declared(root)
    sections, rows, labelled = documented(page.read_text(encoding="utf-8"))
    names = {name for name in found if name is not None}
    messages = [
        f"{module}: {CONSTANT} is not a literal string assigned at the top of the "
        f"module: {SEE}"
        for module in found.get(None, [])
    ]
    for name in sorted(names):
        modules = ", ".join(str(module) for module in found[name])
        if not NAME.fullmatch(name):
            messages.append(
                f"{name!r} in {modules} is not lower-case words joined by hyphens: "
                f"{SEE}"
            )
        if len(found[name]) > 1:
            messages.append(
                f"{name!r} is declared by {len(found[name])} modules, {modules}: {SEE}"
            )
        if name not in sections:
            messages.append(f"{name!r} has no section carrying both labels: {SEE}")
        if name not in rows:
            messages.append(f"{name!r} has no row in the lookup table: {SEE}")
    messages += [
        f"the section for {name!r} documents no check: {SEE}"
        for name in sorted(labelled - names)
    ]
    messages += [
        f"the row for {name!r} links to no check: {SEE}"
        for name in sorted(set(rows) - names)
    ]
    messages += [
        f"{name!r} has {kind} more than once: {SEE}"
        for kind, entries in (("a section", sections), ("a row", rows))
        for name in sorted({entry for entry in entries if entries.count(entry) > 1})
    ]
    return messages


def _tree(
    root: Path, checks: dict[str, str], rows: list[str], sections: list[str]
) -> Path:
    """Write a repository of checks and a page documenting them, for the gate."""
    for relative, value in checks.items():
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"CHECK = {value}\n", encoding="utf-8")
    lines = [".. _gv-developer-checks:", "", "Checks", "======", ""]
    lines += [f"* :ref:`{name} <gv-developer-checks-{name}>`" for name in rows]
    for labels in sections:
        lines += ["", *labels.split("|"), "", "Section", "-------"]
    page = root / "checks.rst"
    page.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return page


def _labels(name: str) -> str:
    """Return both labels of a section, as "_tree" takes them."""
    return f".. _gv-developer-checks-{name}:|.. _tippy-gv-developer-checks-{name}:"


def test_the_page_and_the_checks_agree():
    """Every check has a row and a section, and every row and section a check."""
    assert disagreements(REPO, PAGE) == []
    # a gate that read no check would agree with an empty page
    assert declared(REPO), "the gate found no CHECK to hold the page to"


def test_a_section_without_a_check_fails(tmp_path):
    """A check that has gone takes its row and section with it."""
    page = _tree(tmp_path, {}, ["gone"], [_labels("gone")])
    found = disagreements(tmp_path, page)
    assert any("'gone'" in message and "no check" in message for message in found)


def test_a_check_without_a_section_fails(tmp_path):
    """A new check has a section for its failures to link to."""
    page = _tree(tmp_path, {"tests/test_a.py": '"new"'}, ["new"], [])
    found = disagreements(tmp_path, page)
    assert any("'new'" in message and "no section" in message for message in found)


def test_a_check_without_a_row_fails(tmp_path):
    """A new check has a row in the lookup table."""
    page = _tree(tmp_path, {"tests/test_a.py": '"new"'}, [], [_labels("new")])
    found = disagreements(tmp_path, page)
    assert any("'new'" in message and "no row" in message for message in found)


def test_a_name_declared_twice_fails(tmp_path):
    """One module enforces one check, so a name is declared once."""
    checks = {"tests/test_a.py": '"twice"', ".github/scripts/s.py": '"twice"'}
    page = _tree(tmp_path, checks, ["twice"], [_labels("twice")])
    found = disagreements(tmp_path, page)
    assert any("'twice'" in message and "2 modules" in message for message in found)


def test_a_section_missing_its_tippy_label_fails(tmp_path):
    """A section carries both labels, as every section of the guide does."""
    labels = ".. _gv-developer-checks-new:"
    page = _tree(tmp_path, {"tests/test_a.py": '"new"'}, ["new"], [labels])
    found = disagreements(tmp_path, page)
    assert any("'new'" in message and "no section" in message for message in found)


def test_a_computed_check_fails(tmp_path):
    """A name the gate cannot read is a fault, not a module with no check."""
    page = _tree(tmp_path, {"tests/test_a.py": '"a" + "b"'}, [], [])
    found = disagreements(tmp_path, page)
    assert any("test_a.py" in message and "literal" in message for message in found)


def test_a_half_deleted_section_fails(tmp_path):
    """A label left behind by a check that has gone is reported too."""
    page = _tree(tmp_path, {}, [], [".. _gv-developer-checks-gone:"])
    found = disagreements(tmp_path, page)
    assert any("'gone'" in message and "no check" in message for message in found)


@pytest.mark.parametrize(
    "source",
    [
        pytest.param('CHECK, OTHER = "hidden", 1\n', id="tuple"),
        pytest.param('if True:\n    CHECK = "nested"\n', id="nested"),
        pytest.param("from elsewhere import CHECK\n", id="imported"),
        pytest.param("from elsewhere import other as CHECK\n", id="imported-as"),
        pytest.param('with open(".") as f:\n    CHECK = "nested"\n', id="with"),
        pytest.param('def f():\n    global CHECK\n    CHECK = "late"\n', id="global"),
        pytest.param(
            'values = [(CHECK := "hidden") for _ in range(1)]\n',
            id="comprehension-walrus",
        ),
        pytest.param(
            'def f(value=(CHECK := "hidden")):\n    pass\n', id="default-walrus"
        ),
        pytest.param(
            'class A:\n    global CHECK\n    CHECK = "hidden"\n', id="class-global"
        ),
    ],
)
def test_a_check_bound_out_of_reach_fails(tmp_path, source):
    """The hook reads any CHECK a module binds, so the gate reports any it can't.

    A name bound by unpacking, inside a block, or by an import, is one the gate
    cannot read from the source, yet a failure would still link to its section.

    """
    module = tmp_path / "tests" / "test_a.py"
    module.parent.mkdir(parents=True)
    module.write_text(source, encoding="utf-8")
    page = _tree(tmp_path, {}, [], [])
    found = disagreements(tmp_path, page)
    assert any("test_a.py" in message and "literal" in message for message in found)


@pytest.mark.parametrize(
    "source",
    [
        pytest.param('def f():\n    CHECK = "local"\n', id="function-local"),
        pytest.param('class A:\n    CHECK = "attribute"\n', id="class-attribute"),
        pytest.param("x = [CHECK for CHECK in range(3)]\n", id="comprehension"),
        pytest.param("f = lambda CHECK: CHECK\n", id="lambda"),
        pytest.param(
            "from upstream import CHECK as dependency_check\n", id="imported-as"
        ),
        pytest.param(
            'CHECK = "demo"\n'
            "def outer():\n"
            '    CHECK = "local"\n'
            "    def inner():\n"
            "        global CHECK\n"
            "        return CHECK\n"
            "    return inner()\n",
            id="nested-global",
        ),
    ],
)
def test_a_name_that_binds_no_module_check_passes(tmp_path, source):
    """Only a binding of the module's own CHECK is one the hook would read."""
    module = tmp_path / "tests" / "test_a.py"
    module.parent.mkdir(parents=True)
    module.write_text(source, encoding="utf-8")
    names = [name for name in declared(tmp_path) if name is not None]
    page = _tree(tmp_path, {}, names, [_labels(name) for name in names])
    assert disagreements(tmp_path, page) == []


def test_an_ill_formed_name_fails(tmp_path):
    """A name is the stem of a label, so it is lower-case words and hyphens."""
    name = "Image_Marker"
    page = _tree(tmp_path, {"tests/test_a.py": f'"{name}"'}, [name], [_labels(name)])
    found = disagreements(tmp_path, page)
    assert any(f"'{name}'" in message and "hyphens" in message for message in found)
