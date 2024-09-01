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
* `documentation`: Notable changes to the documentation structure, content, render or build
* `internal`: Miscellaneous internal and maintenance changes
* `community`: Celebrate our awesome community members and contributions
* `contributor`: Changes that affect contributors such as standards, conventions, running tests, building docs, environments etc
* `misc`: Catch all for items that don't fit elsewhere

For example, ``123.feature.rst`` or ``456.bugfix.rst``.

If you are unsure what `<TYPE>` to use, then don't hesitate to ask in your
pull-request.

````{tip}
If a change is associated with **more than one** pull-request, then create a
news fragment file for each pull-request with **identical content** e.g.,
a change associated with 3 pull-requests has the following 3 news fragment
files `101.feature.rst`, `102.feature.rst` and `103.feature.rst`, all of
which contain exactly the same content.
````

[towncrier](https://github.com/twisted/towncrier) preserves multiple
paragraphs in a news fragment file, however concise single paragraph
entries are encouraged.

```{tip}
Run `towncrier --draft` to render a preview of the news fragments.
```
