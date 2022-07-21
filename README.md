<h1 align="center">
  <a href="https://github.com/bjlittle/geovista#--------">
    <img src="https://raw.githubusercontent.com/bjlittle/geovista/main/branding/logo/primary/geovistalogo.svg"
         alt="GeoVista"
         width="200"></a>
</h1>

<h5 align="center">
  Cartographic rendering and mesh analytics powered by <a href="https://docs.pyvista.org/index.html">PyVista</a>
</h5>

| | |
| --- | --- |
| CI | [![ci-locks](https://github.com/bjlittle/geovista/actions/workflows/ci-locks.yml/badge.svg)](https://github.com/bjlittle/geovista/actions/workflows/ci-locks.yml) [![ci-manifest](https://github.com/bjlittle/geovista/actions/workflows/ci-manifest.yml/badge.svg)](https://github.com/bjlittle/geovista/actions/workflows/ci-manifest.yml) [![ci-tests](https://github.com/bjlittle/geovista/actions/workflows/ci-tests.yml/badge.svg)](https://github.com/bjlittle/geovista/actions/workflows/ci-tests.yml) [![ci-wheels](https://github.com/bjlittle/geovista/actions/workflows/ci-wheels.yml/badge.svg)](https://github.com/bjlittle/geovista/actions/workflows/ci-wheels.yml) [![pre-commit](https://results.pre-commit.ci/badge/github/bjlittle/geovista/main.svg)](https://results.pre-commit.ci/latest/github/bjlittle/geovista/main) |
| Docs | [![documentation](https://readthedocs.org/projects/geovista/badge/?version=latest)](https://readthedocs.org/projects/geovista/) |
| Package | [![conda-forge](https://img.shields.io/conda/vn/conda-forge/geovista?color=orange&label=conda-forge&logo=conda-forge&logoColor=white)](https://anaconda.org/conda-forge/geovista) [![pypi](https://img.shields.io/pypi/v/geovista?color=orange&label=pypi&logo=python&logoColor=white)](https://pypi.org/project/geovista/) [![pypi - python version](https://img.shields.io/pypi/pyversions/geovista.svg?color=orange&logo=python&label=Python&logoColor=white)](https://pypi.org/project/geovista/) |
| Repository | [![contributors](https://img.shields.io/github/contributors/bjlittle/geovista)](https://github.com/bjlittle/geovista/graphs/contributors) |
| Health | [![codacy](https://app.codacy.com/project/badge/Grade/a13c37670f854814ae58f571fab06bc2)](https://www.codacy.com/gh/bjlittle/geovista/dashboard?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=bjlittle/geovista&amp;utm_campaign=Badge_Grade) [![codecov](https://codecov.io/gh/bjlittle/geovista/branch/main/graph/badge.svg?token=RVVXGP1SD3)](https://codecov.io/gh/bjlittle/geovista) |
| Meta | [![code style - black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black) [![license - bds-3-clause](https://img.shields.io/github/license/bjlittle/geovista)](https://github.com/bjlittle/geovista/blob/main/LICENSE) [![conda platform](https://img.shields.io/conda/pn/conda-forge/geovista.svg)](https://anaconda.org/conda-forge/geovista) |
| | |


<p align="center">
  <img src="https://img.shields.io/badge/wip-%20%F0%9F%9A%A7%20under%20construction%20%F0%9F%9A%A7-yellow"
       alt="wip">
</p>


## Installation

Almost, but not quite... 😉

Apologies. We've not yet tagged our first minor release of GeoVista.

We have secured the package namespace on both [conda-forge](https://anaconda.org/conda-forge/geovista) and [PyPI](https://pypi.org/project/geovista/), but that's just a placeholder for now.

In the meantime, life is just a smidge more complicated than necessary if you desire to play with GeoVista.


### Development

First, clone the GeoVista GitHub repository:
```shell
git clone git@github.com:bjlittle/geovista.git
```
Change to the root directory:
```shell
cd geovista
```
Create the `geovista-dev` conda environment for your preferred platform and Python version e.g.,
```shell
conda create -n geovista-dev --file requirements/locks/py310-lock-linux-64.txt
```
Note that, the `requirements/locks` directory contains fully resolved conda package environments, which are automatically updated on a weekly basis. Alternatively, simply:
```shell
conda env create --file requirements/geovista.yml
```
Now activate the environment and install the `main` development branch of GeoVista:
```shell
conda activate geovista-dev
pip install --no-deps --editable .
```
Finally, we're good to roll 👍

### ~~conda~~

GeoVista is available on [conda-forge](https://anaconda.org/conda-forge/geovista), and can be easily installed with [conda](https://docs.conda.io/projects/conda/en/latest/index.html):
```shell
conda install -c conda-forge geovista
```
or alternatively with [mamba](https://github.com/mamba-org/mamba):
```shell
mamba install geovista
```
For more information see the [feedstock](https://github.com/conda-forge/geovista-feedstock).

### ~~pip~~

GeoVista is available on [PyPI](https://pypi.org/project/geovista/):

```shell
pip install geovista
```

## Quick Start

GeoVista comes with various pre-canned resources to help get you started on your visualisation journey.

### Resources

GeoVista makes use of various resources, such as rasters, VTK meshes, [Natural Earth](https://www.naturalearthdata.com/features/) features, and sample model data.

If you want to download and cache all the available GeoVista assets to make them available offline, simply:
```shell
geovista download --all
```
Alternatively, just leave GeoVista to download assets on-the-fly as and when it needs them.

To view the list of registered resources available, simply:
```shell
geovista download --list
```

### Plotting Examples

Let's explore a sample of various oceanographic and atmospheric model data using GeoVista.

#### WAVEWATCH III

First, let's render a [WAVEWATCH III](https://github.com/NOAA-EMC/WW3) (WW3) unstructured triangular mesh.
<details>
<summary> <img src="https://raw.githubusercontent.com/bjlittle/geovista-data/main/icons/browser.png" alt="code"> </summary>

```python
import geovista as gv
from geovista.pantry import ww3_global_tri
import geovista.theme

# load the sample data
sample = ww3_global_tri()

# create the mesh from the sample data
mesh = gv.Transform.from_unstructured(
    sample.lons, sample.lats, sample.connectivity, data=sample.data
)

# plot the mesh
plotter = gv.GeoPlotter()
sargs = dict(title=f"{sample.name} / {sample.units}")
plotter.add_mesh(
    mesh, cmap="balance", show_edges=True, edge_color="grey", scalar_bar_args=sargs
)
plotter.add_base_layer(texture=gv.natural_earth_hypsometric())
plotter.add_coastlines(resolution="10m", color="white")
plotter.add_axes()
plotter.show()
```
</details>

![ww3-tri](https://raw.githubusercontent.com/bjlittle/geovista-data/main/media/ww3-tri.png)

#### Finite Volume Community Ocean Model

Now, let's visualise the bathymetry of the [Plymouth Sound and Tamar River](https://www.google.com/maps/place/Plymouth+Sound/@50.2923012,-4.192073,12z/data=!4m5!3m4!1s0x486c93516bbce307:0xded7654eaf4f8f83!8m2!3d50.3638359!4d-4.1441365) from an [FVCOM](http://fvcom.smast.umassd.edu/fvcom/) unstructured mesh, as kindly provided by the [Plymouth Marine Laboratory](https://pml.ac.uk/).

<details>
<summary> <img src="https://raw.githubusercontent.com/bjlittle/geovista-data/main/icons/browser.png" alt="code"> </summary>

```python
import geovista as gv
from geovista.pantry import fvcom_tamar
import geovista.theme

# load the sample data
sample = fvcom_tamar()

# create the mesh from the sample data
mesh = gv.Transform.from_unstructured(
    sample.lons, sample.lats, sample.connectivity, sample.face, name="face"
)

# warp the mesh nodes by the bathymetry
mesh.point_data["node"] = sample.node
mesh.compute_normals(cell_normals=False, point_normals=True, inplace=True)
mesh.warp_by_scalar(scalars="node", inplace=True, factor=2e-5)

# plot the mesh
plotter = gv.GeoPlotter()
sargs = dict(title=f"{sample.name} / {sample.units}")
plotter.add_mesh(mesh, cmap="balance", scalar_bar_args=sargs)
plotter.add_axes()
plotter.show()
```
</details>

![tamar](https://raw.githubusercontent.com/bjlittle/geovista-data/main/media/tamar_zoom.png)

## License

GeoVista is distributed under the terms of the [BSD-3-Clause](https://spdx.org/licenses/BSD-3-Clause.html) license.
