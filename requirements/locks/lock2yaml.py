#!/usr/bin/env python
# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Convert a lock file to a YAML file."""
from __future__ import annotations

import sys

from jinja2 import Environment, FileSystemLoader, select_autoescape

if (nargv := (len(sys.argv) - 1)) != 1:
    emsg = f"Expect 'environment-name' as a single argument to '{sys.argv[0]}' script."
    raise ValueError(emsg)

environment = Environment(
    autoescape=select_autoescape(), loader=FileSystemLoader("templates/")
)
template = environment.get_template("lock2yaml.txt")

# default to linux-64 only
env = sys.argv[1]
lock = f"{env}-linux-64.txt"
name = f"geovista-{env}"
yaml = f"{env}-linux-64.yml"

# TODO @bjlittle: use Path.open when >=py311 and remove .ruff.toml ignore
with open(lock) as fin:
    content = template.render(file=fin, name=name)

with open(yaml, mode="w", encoding="utf-8") as fout:
    fout.write(content)
