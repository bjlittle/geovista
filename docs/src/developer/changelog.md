# {fa}`road` Changelog

The {ref}`changelog <gv-changelog>` is managed and orchestrated with
[towncrier](https://github.com/twisted/towncrier).

The root level `changelog` directory contains [ReStructuredText](https://www.sphinx-doc.org/en/master/usage/restructuredtext/basics.html)
(`.rst`) **news fragment files** that each describe a change made to
`geovista`. These news fragment files will be removed, combined and
then added as the final release notes by
[towncrier](https://github.com/twisted/towncrier) to the root level
`CHANGELOG.rst` file when performing a release of `geovista`.

The **intended audience** of the `CHANGELOG.rst` are **users**. Therefore,
avoid describing low-level internal details only suitable for contributors,
if possible.

When describing a change in its news fragment file make sure to use full
sentences in the *past* or *present* tense with appropriate punctuation,
for example:

```none
Skip tests if their optional package dependencies are not installed.
```

or

```none
Cross-referenced module headings to improve primary sidebar readability.
```

The following [extlinks](https://www.sphinx-doc.org/en/master/usage/extensions/extlinks.html)
conveniences may be used within a news fragment file:

* `:issue:` - Link to a `geovista` {fab}`github` issue e.g., **:issue:\`123\`**
* `:pull:` - Link to a `geovista` {fab}`github` pull-request e.g., **:pull:\`456\`**
* `:user:` - Link to a {fab}`github` user e.g., **:user:\`bjlittle\`**

````{note}
Remember to acknowledge the author/s of a pull-request e.g.,

```none
Added an awesome new feature. (:user:`bjlittle`)
```
````

Each news fragment file **must** be named as `<PULL-REQUEST>.<TYPE>.rst`,
where `<PULL-REQUEST>` is the {fab}`github` pull-request number,
and `<TYPE>` is one of:

* `breaking`: Removals and backward incompatible breaking changes that may affect user code
* `deprecation`: Declaration of removals and backward incompatible changes
* `feature`: New user facing behaviours or capability
* `enhancement`: Updates to existing behaviours or capability, including performance
* `bugfix`: Correction to undesired behaviours or reported bugs
* `dependency`: Package dependency removals, additions, pins etc
* `asset`: Data, media and asset updates etc
* `documentation`: Notable changes to the documentation structure, content, render or build
* `internal`: Miscellaneous internal and maintenance changes
* `community`: Celebrate our awesome community members and their contributions, including social changes
* `contributor`: Changes that affect contributors such as standards, conventions, running tests, building docs, environments etc
* `misc`: Catch all for items that don't fit elsewhere

e.g., ``123.feature.rst`` or ``456.bugfix.rst``.

[towncrier](https://github.com/twisted/towncrier) is configured in the
`pyproject.toml`. For further details see the `[tool.towncrier]` section.
Note that the order of the `[[tool.towncrier.type]]` entries is significant,
as it is mirrored in the final rendered {ref}`changelog <gv-changelog>`.

If you're unsure what news fragment `<TYPE>` to use, then don't hesitate to
ask in your pull-request.

````{tip}
If a change is associated with **more than one** pull-request, then create a
news fragment file for each pull-request with **identical content** e.g.,
a change associated with 3 pull-requests has the following 3 news fragment
files `101.feature.rst`, `102.feature.rst` and `103.feature.rst`, all of
which contain exactly the same content.
````

[towncrier](https://github.com/twisted/towncrier) preserves multiple
paragraphs and the formatting within a news fragment file, however concise
single paragraph entries are encouraged.

```{tip}
Run `towncrier --draft` to render a preview of the news fragment files in the
`changelog` directory.
```

## {fa}`road` Changelog Quality Assurance

Quality assurance of `changelog` contributions is performed by the
[ci-changelog](https://github.com/bjlittle/geovista/blob/main/.github/workflows/ci-changelog.yml)
{fab}`github` Action.

It performs the following automated checks on each pull-request:

* Ensures that the pull-request includes a `changelog` news fragment
* The news fragment file conforms with the expected `<PULL-REQUEST>.<TYPE>.rst` naming format i.e.,
  * The `<PULL-REQUEST>` component is a valid integer and matches the pull-request number
  * The `<TYPE>` matches a configured `[[tool.towncrier.type]]` entry in the `pyproject.toml`
  * The `rst` extension is provided

These quality assurance checks can be **skipped** by adding the
`skip changelog` label to the pull-request. Note that a pull-request generated
by the following bots or services will have the `skip changelog` label
automatically applied:

* [dependabot](https://docs.github.com/en/code-security/dependabot/dependabot-version-updates/configuring-dependabot-version-updates) version updates
* [pre-commit.ci](https://pre-commit.ci/) hook updates
* [ci-locks](https://github.com/bjlittle/geovista/blob/main/.github/workflows/ci-locks.yml) {fab}`github` Action

Also, see the [ci-label](https://github.com/bjlittle/geovista/blob/main/.github/workflows/ci-label.yml)
{fab}`github` Action for automated pull-request labelling.

Removing the `skip changelog` label from a pull-request will trigger the
[ci-changelog](https://github.com/bjlittle/geovista/blob/main/.github/workflows/ci-changelog.yml)
{fab}`github` Action workflow.
