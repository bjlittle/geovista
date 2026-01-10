#!/usr/bin/env python
# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Convert a lock file to a YAML file."""

from __future__ import annotations

from pathlib import Path
import sys

from jinja2 import Environment, FileSystemLoader, select_autoescape

if (nargv := (len(sys.argv) - 1)) != 1:
    emsg = f"Expect 'version' as a single argument to '{sys.argv[0]}' script."
    raise ValueError(emsg)

environment = Environment(
    autoescape=select_autoescape(), loader=FileSystemLoader("templates/")
)
template = environment.get_template("lock2yaml.txt")

# default to linux-64 only
env = f"geovista-{sys.argv[1]}"
lock = f"{env}_linux-64_conda_spec.txt"
yaml = f"{env}_linux-64_conda_spec.yml"

with Path(lock).open(mode="r") as fin:
    content = template.render(file=fin, name=env)

with Path(yaml).open(mode="w", encoding="utf-8") as fout:
    fout.write(content)
    fout.write("\n")
