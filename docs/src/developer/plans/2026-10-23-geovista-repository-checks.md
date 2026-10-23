# Repository Checks Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Give every check `geovista` enforces on its own repository a section on one "Repository checks" page, link every failure of a check to its section, and gate the page and the checks to each other.

**Architecture:** Each enforcing module declares `CHECK = "<name>"`. A stdlib-only module, `.github/scripts/breadcrumb.py`, owns the breadcrumb text; a `pytest_runtest_makereport` wrapper in `tests/conftest.py` appends it to any failed report of a module declaring `CHECK`, and the two CI scripts print it for a finding. `tests/test_repository_checks.py` reads every `CHECK` and the page as text and fails unless they agree in both directions.

**Tech Stack:** pytest (hook wrapper, `pytester`, `pytest-xdist`), Sphinx reStructuredText, `click`, `towncrier` (stubbed in tests).

**Spec:** `docs/src/developer/specs/2026-10-23-repository-checks-design.md` (`checks spec §…`, merged in #2705). Read it before each task.

## Global Constraints

- The page is `docs/src/developer/checks.rst`, titled "Repository checks" (checks spec §2).
- Breadcrumb text, exactly, as two lines (checks spec §3.3):
  `Why this check exists, and how to declare an exception:` then
  `https://geovista.readthedocs.io/en/latest/developer/checks.html#gv-developer-checks-<name>`
- A name is lower-case words joined by hyphens, `^[a-z0-9]+(-[a-z0-9]+)*$`; its section carries both labels `gv-developer-checks-<name>` and `tippy-gv-developer-checks-<name>` (checks spec §3.2).
- Only the module that enforces a check declares its `CHECK`, as a literal string at module level, once (checks spec §3.2, §3.4).
- The nine names, decided here, and their modules:

  | name | module |
  |---|---|
  | `image-marker` | `tests/test_image_marker.py` |
  | `reading-time-banner` | `tests/docs/test_readingtime_coverage.py` |
  | `strict-typing` | `tests/test_ci_typing.py` |
  | `python-support` | `tests/test_python_support.py` |
  | `parallel-safe-extensions` | `tests/docs/test_ext_parallel.py` |
  | `spec-conventions` | `tests/test_spec_conventions.py` |
  | `changelog-fragment` | `.github/scripts/changelog.py` |
  | `spec-statuses` | `.github/scripts/check_status_references.py` |
  | `repository-checks` | `tests/test_repository_checks.py` |

- `breadcrumb.py` imports nothing outside the standard library: `ci-changelog.yml` runs `changelog.py` from `.github/scripts` with only `click` and `towncrier` installed (checks spec §3.3).
- Scripts print the breadcrumb for a finding only, never for a failure to run (checks spec §3.3).
- No new dependency. `changelog.py` is tested with a `towncrier` stub in `sys.modules` (checks spec §6, §8 item 1, #2704).
- Every commit goes through the hooks: `pixi run --frozen -e geovista git commit ...`.

## Review Focus

1. **A check failing under `pytest-xdist`**, as every CI test job runs: the breadcrumb must survive the report's trip from worker to controller. Task 1 tests it with `-n 2`.
2. **A check failing in a fixture rather than an assertion**, such as `--browser-strict` failing a prerequisite fixture in `tests/docs`: the report's `when` is `setup`, and the breadcrumb must still appear. Task 1 tests it.
3. **A skipped test in a check module** must carry no breadcrumb, nor must a passing one: `tests/docs` skips without `sphinx` or a build. Task 1 tests it.
4. **A script failing to run** (a `towncrier` configuration error, a missing pull request number, no configured types, GitHub unreachable) must print no breadcrumb, and a nightly drift issue must not claim a rule was broken when the check never ran. Tasks 2 and 3 test it.
5. **A `CHECK` the gate cannot read**, computed rather than a literal, or ill-formed: the gate must fail rather than treat the module as declaring nothing. Task 5 tests it.

---

### Task 1: The breadcrumb and the pytest hook

**Files:**
- Create: `.github/scripts/breadcrumb.py`
- Modify: `tests/conftest.py` (add `pytest_plugins` and the hook)
- Create: `tests/test_repository_checks.py` (declares `CHECK = "repository-checks"`; Task 5 adds the gate to it)

**Interfaces:**
- Produces: `breadcrumb.PAGE: str`, the page URL without fragment; `breadcrumb.LABEL: str = "gv-developer-checks-"`; `breadcrumb.breadcrumb(name: str) -> str`, the two lines of the Global Constraints, joined by `"\n"`; `tests/conftest.py::load_breadcrumb() -> ModuleType`, loading `.github/scripts/breadcrumb.py` by path.

- [ ] **Step 1: Write the failing tests** in `tests/test_repository_checks.py`

  - `test_breadcrumb_names_the_section`: `breadcrumb("image-marker")` equals the two exact lines of the Global Constraints for that name.
  - `test_breadcrumb_needs_no_dependency`: parse `breadcrumb.py` with `ast`; every `import`/`from` names a module in `sys.stdlib_module_names` (or `__future__`).
  - `test_hook_adds_the_breadcrumb` parametrised over `[]` and `["-n", "2"]`: `pytester.makepyfile` a module with `CHECK = "demo"`, one failing assertion, one test using a fixture that raises, one `pytest.skip`, one pass; `monkeypatch.setenv("PYTHONPATH", str(REPO))`; `result = pytester.runpytest_subprocess("-p", "tests.conftest", "-p", "no:cacheprovider", *args)`; assert `result.stdout.str().count("#gv-developer-checks-demo") == 2` (the assertion and the setup error) and `result.ret == 1`.
  - `test_hook_ignores_a_module_without_check`: the same failing test without `CHECK`; assert `"gv-developer-checks-" not in result.stdout.str()`.

- [ ] **Step 2: Run them to verify they fail**

  Run: `pixi run --frozen -e geovista pytest -p no:pretty tests/test_repository_checks.py -v`
  Expected: collection or `FileNotFoundError` for `breadcrumb.py`, then, once it exists, the hook tests fail with a count of 0.

- [ ] **Step 3: Implement `breadcrumb.py`**, three names as in Interfaces, with the copyright header and `from __future__ import annotations`.

- [ ] **Step 4: Implement the hook in `tests/conftest.py`**

  Add `pytest_plugins = ("pytester",)` and `load_breadcrumb()` (`importlib.util.spec_from_file_location`, as `tests/test_status_references.py` loads its script). The hook, whose shape was probed on 2026-10-23 to give one breadcrumb per failed report under `pytest-pretty`, serially and with `-n 2`:

  ```python
  @pytest.hookimpl(wrapper=True)
  def pytest_runtest_makereport(item, call):
      report = yield
      name = getattr(getattr(item, "module", None), "CHECK", None)
      if report.failed and isinstance(name, str):
          hint = BREADCRUMB.breadcrumb(name)
          if hasattr(report.longrepr, "addsection"):
              report.longrepr.addsection("repository check", hint)
          else:
              report.sections.append(("repository check", hint))
      return report
  ```

  with `BREADCRUMB = load_breadcrumb()` at module level, and a NumPy docstring saying why (checks spec §3.3).

- [ ] **Step 5: Run the tests to verify they pass**

  Run: `pixi run --frozen -e geovista pytest -p no:pretty tests/test_repository_checks.py -v`
  Expected: PASS.

- [ ] **Step 6: Commit** `tests: add the repository check breadcrumb and its pytest hook`.

### Task 2: Name the six test-module checks

**Files:**
- Modify: the six test modules of the Global Constraints table, adding `CHECK` after the module's imports and constants header comment, as checks spec §3.2 shows.

**Interfaces:**
- Consumes: the hook of Task 1, which keys on `module.CHECK`.

- [ ] **Step 1: Prove the breadcrumb is absent.** In a scratch worktree, break one rule (e.g. append `def test_x(): pv.Plotter().show()` to a test module without the image marker) and run `tests/test_image_marker.py`; the failure carries no `gv-developer-checks-`.
- [ ] **Step 2: Add the six `CHECK` constants**, each with the comment `#: The section of the repository checks page that documents this check.`
- [ ] **Step 3: Re-run the probe of Step 1** on the worktree updated with this task; the failure now ends with the breadcrumb for `image-marker`. Remove the worktree.
- [ ] **Step 4: Run the six modules**: `pixi run --frozen -e geovista pytest -p no:pretty tests/test_image_marker.py tests/docs/test_readingtime_coverage.py tests/test_ci_typing.py tests/test_python_support.py tests/docs/test_ext_parallel.py tests/test_spec_conventions.py`. Expected: PASS, nothing new skipped.
- [ ] **Step 5: Commit** `tests: name the six repository checks the test suite enforces`.

### Task 3: The scripts print the breadcrumb for a finding

**Files:**
- Modify: `.github/scripts/changelog.py`, `.github/scripts/check_status_references.py`
- Create: `tests/test_changelog_script.py`
- Modify: `tests/test_status_references.py`

**Interfaces:**
- Consumes: `breadcrumb.breadcrumb(name)`, loaded by each script by path from `Path(__file__).parent / "breadcrumb.py"`, since a test loads the scripts by path and `.github/scripts` is not then on `sys.path`.
- Produces: `changelog.CHECK = "changelog-fragment"`, `check_status_references.CHECK = "spec-statuses"`.

- [ ] **Step 1: Write the failing tests.**

  `tests/test_changelog_script.py`, which declares no `CHECK` (checks spec §3.2): a `script` fixture that `monkeypatch.setitem`s `sys.modules["towncrier"]` and `sys.modules["towncrier._settings"]` with a `ModuleType` carrying `ConfigError` (an `Exception` subclass with a `message` attribute) and `load_config_from_options`, then loads `changelog.py` by path; `monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(tmp_path / "summary.md"))` before loading, as the module reads it at import.
  - `test_finding_prints_the_breadcrumb`: `pytest.raises(SystemExit)` around `script.failure(["bad fragment"])`; the breadcrumb for `changelog-fragment` is in `capsys` stdout and in the summary file, and `towncrier.html#changelog` is in neither.
  - `test_failure_to_run_prints_none` parametrised over the three non-findings, driven through `script.main` with `click.testing.CliRunner`: an empty `pr` argument; `load_config_from_options` raising `ConfigError`; a config whose `types` is `{}`. Assert exit code 1 and no `gv-developer-checks-` in the output or the summary.

  `tests/test_status_references.py`: extend `test_main_findings` to assert the breadcrumb for `spec-statuses` is in stdout; extend `test_main_unexpected` to assert `gv-developer-checks-` is in neither stream.

- [ ] **Step 2: Run them to verify they fail.**

  Run: `pixi run --frozen -e test-py313 pytest -p no:pretty tests/test_changelog_script.py tests/test_status_references.py -v`
  Expected: the breadcrumb assertions fail; the "prints none" cases pass already, except where the old link prints.

- [ ] **Step 3: Implement.** `changelog.py`: add `CHECK`; rename `failure`'s parameter `url` to `finding: bool | None = True`, whose docstring says a finding ends with the breadcrumb of checks spec §3.3; when it is true, `failure` prints `breadcrumb(CHECK)` through `summary()` in place of the `URL` line, which goes, as does the `URL` constant. The calls for a missing pull request number, no configured types and a `ConfigError` pass `finding=False`. `check_status_references.py`: add `CHECK`; when `problems` is non-empty, print the breadcrumb to stdout after them, before the summary line.

- [ ] **Step 4: Run the tests to verify they pass** with the Step 2 command. Expected: PASS.

- [ ] **Step 5: Run the script as CI does.** `cd .github/scripts && pixi run --frozen -e docs python changelog.py 9999 "changelog/2706.enhancement.rst"` fails for the wrong pull request, and its last lines are the breadcrumb.

- [ ] **Step 6: Commit** `ci: print the repository check breadcrumb for a script finding`.

### Task 4: The page

**Files:**
- Create: `docs/src/developer/checks.rst`
- Modify: `docs/src/developer/index.rst` (card and toctree), `docs/src/developer/changelog.md` (one label), `tests/docs/test_readingtime_coverage.py` (`EXEMPT`)

**Interfaces:**
- Produces: the labels `gv-developer-checks-<name>` and `tippy-gv-developer-checks-<name>` for the nine names, and the page labels `gv-developer-checks` and `tippy-gv-developer-checks`, which Task 5's gate reads.

- [ ] **Step 1: Prove the reading-time gate governs the new page.** Create `checks.rst` with only its title; `pixi run --frozen -e geovista pytest -p no:pretty tests/docs/test_readingtime_coverage.py` fails naming it.
- [ ] **Step 2: Add it to `EXEMPT`** under the existing `# lookup:` comment: `"developer/checks.rst",  # a table of checks, each consulted on its own`. The gate passes.
- [ ] **Step 3: Write the page.** Header as `testing.rst`'s (`.. include:: ../common.txt`, the page labels, title `:fa:`shield-halved` Repository checks`, already branded in `color.css`), no `readingtime`. Then:
  - one line: if a check failed, find it below; each section says why it exists and how to declare an exception.
  - a `.. note::` that third-party tools (`ruff`, type-ignore comments, `filterwarnings`, `nitpick_ignore_regex`, `zizmor`) are not yet covered, citing `checks spec §4` with a `:ref:` to `checks-spec-4`.
  - two `list-table`s, under the group headings "A test failed" and "A CI job failed", columns "Check" and "Where an exception goes", each check a `:ref:` to its section. Tests: the seven test-module names of the Global Constraints, `repository-checks` included. CI: `changelog-fragment`, `spec-statuses`.
  - one section per name, in table order, each with both labels and six `rubric`-free bold-led paragraphs in the order of checks spec §3.1. Facts per section, from the module docstrings and the spec:

  | name | exception | more |
  |---|---|---|
  | `image-marker` | `EXEMPT` in the module, name to reason | `gv-developer-testing-image-tests-markers` |
  | `reading-time-banner` | `EXEMPT`, with the reason as a comment; `EXCLUDED_DIRS` is not an exception | `gv-developer-documentation-sphinx-directives-readingtime` |
  | `strict-typing` | `RELAXED`, only for a relaxation the type coverage spec gives a reason for; never inline, never `ignore_errors` | `typing-spec-6` |
  | `python-support` | none | SPEC 0, external |
  | `parallel-safe-extensions` | none | `gv-developer-documentation-parallel` |
  | `spec-conventions` | none; `CEILING` is the trigger of `docs-spec-4` rows 2 to 4, not an exception | `docs-spec-3-5` |
  | `changelog-fragment` | the `skip-changelog` label, added by a maintainer | `gv-developer-changelog-quality-assurance` |
  | `spec-statuses` | none: correct the status | `gv-developer-specs-statuses` |
  | `repository-checks` | none | `checks-spec-3-4` |

- [ ] **Step 4: Add the label** `(gv-developer-changelog-quality-assurance)=` and `(tippy-gv-developer-changelog-quality-assurance)=` above the "Changelog Quality Assurance" heading of `changelog.md`.
- [ ] **Step 5: Add the card and toctree entry** to `developer/index.rst`: a "Repository checks" card between Packaging and Specifications, `:link: gv-developer-checks`, reusing `../_static/images/icons/glossary.svg` as a lookup page's icon, body "Why a check failed."; `checks` in the toctree after `testing`.
- [ ] **Step 6: Build.** `pixi run --frozen -e docs make` succeeds (it is `--fail-on-warning`), and `grep -c 'id="gv-developer-checks-' docs/_build/html/developer/checks.html` is 9.
- [ ] **Step 7: Commit** `docs: add the repository checks page`.

### Task 5: The gate

**Files:**
- Modify: `tests/test_repository_checks.py`

**Interfaces:**
- Consumes: Task 4's labels, Task 2's and Task 3's `CHECK` constants.
- Produces: `declared(root: Path) -> dict[str, list[Path]]`; `documented(text: str) -> tuple[list[str], list[str]]` (section names, row names, each in page order, duplicates kept); `disagreements(root: Path, page: Path) -> list[str]`.

- [ ] **Step 1: Write the failing tests.**
  - `test_the_page_and_the_checks_agree`: `disagreements(REPO, PAGE) == []`, and `len(declared(REPO)) == 9`.
  - `test_a_section_without_a_check_fails`, `test_a_check_without_a_section_fails`, `test_a_check_without_a_row_fails`, `test_a_name_declared_twice_fails`, `test_a_section_missing_its_tippy_label_fails`: each builds a tree under `tmp_path` (`tests/test_a.py`, `.github/scripts/s.py`, a page) and asserts one message naming the check is in `disagreements`.
  - `test_a_computed_check_fails` (Review Focus 5): `CHECK = "a" + "b"` in the tree gives a disagreement naming the file.
  - `test_an_ill_formed_name_fails` (Review Focus 5): `CHECK = "Image_Marker"`.
- [ ] **Step 2: Run them to verify they fail.** `pixi run --frozen -e geovista pytest -p no:pretty tests/test_repository_checks.py -v`. Expected: `NameError` for the three functions.
- [ ] **Step 3: Implement the three functions.** `declared` walks `root / "tests"` (`rglob("*.py")`) and `root / ".github" / "scripts"` (`glob("*.py")`) with `ast`, taking a module-level `Assign`/`AnnAssign` to the name `CHECK`; a non-`str` constant value is recorded so `disagreements` can name it. `documented` reads labels with `^\.\. _(tippy-)?gv-developer-checks-([a-z0-9-]+):$`, and rows as the `<gv-developer-checks-…>` targets of `:ref:` roles before the first section label. Every message ends `… : see checks spec §3.4`.
- [ ] **Step 4: Run them to verify they pass**, with the Step 2 command.
- [ ] **Step 5: Prove it on the real tree.** In a scratch worktree: delete `CHECK` from `tests/test_python_support.py`, and the gate names `python-support`; separately, delete its section, and the gate names it. Remove the worktree.
- [ ] **Step 6: Commit** `tests: gate the repository checks page against the checks`.

### Task 6: Record it

**Files:**
- Modify: `tests/AGENTS.md`, `docs/src/developer/specs/2026-10-23-repository-checks-design.md`
- Create: `changelog/<PR>.contributor.rst`

- [ ] **Step 1: `tests/AGENTS.md`**: one rule, kept under 200 lines: a new repository check declares `CHECK`, gets a row and a section in `docs/src/developer/checks.rst`, and `tests/test_repository_checks.py` fails until it does.
- [ ] **Step 2: The changelog fragment**, `:user:`claude``, checked with `pixi run --frozen -e docs python .github/scripts/changelog.py <PR> "changelog/<PR>.contributor.rst"`.
- [ ] **Step 3: The full suite.** `CI=true GALLIUM_DRIVER=llvmpipe xvfb-run -a pixi run --frozen -e geovista pytest --numprocesses logical --dist worksteal`, and `pixi run --frozen -e test-py313 pytest -p no:pretty tests/test_repository_checks.py tests/test_changelog_script.py tests/test_status_references.py`. Expected: PASS, with no new skips.
- [ ] **Step 4: The landed row, as the last commit** after the review rounds: row 1 of checks spec §4 becomes `✅ landed (<date>, {pull}`<PR>`)`; run `pixi run --frozen -e test check-spec-status <PR>`.
