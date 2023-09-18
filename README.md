<h1 align="center">
  <a href="https://github.com/bjlittle/geovista#--------">
    <img src="https://raw.githubusercontent.com/bjlittle/geovista-media/2023.09.1/media/branding/logo/primary/geovistalogo.svg"
         alt="GeoVista"
         width="200"></a>
</h1>

<h3 align="center">
  Cartographic rendering and mesh analytics powered by <a href="https://docs.pyvista.org/index.html">PyVista</a>
</h3>

<!---
fix docs pythreejs/panel
| 📚 Docs | [![documentation](https://readthedocs.org/projects/geovista/badge/?version=latest)](https://readthedocs.org/projects/geovista/)
-->

|              |                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           |
|--------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| ⚙️ CI        | [![ci-citation](https://github.com/bjlittle/geovista/actions/workflows/ci-citation.yml/badge.svg)](https://github.com/bjlittle/geovista/actions/workflows/ci-citation.yml) [![ci-locks](https://github.com/bjlittle/geovista/actions/workflows/ci-locks.yml/badge.svg)](https://github.com/bjlittle/geovista/actions/workflows/ci-locks.yml) [![ci-manifest](https://github.com/bjlittle/geovista/actions/workflows/ci-manifest.yml/badge.svg)](https://github.com/bjlittle/geovista/actions/workflows/ci-manifest.yml) [![ci-tests](https://github.com/bjlittle/geovista/actions/workflows/ci-tests.yml/badge.svg)](https://github.com/bjlittle/geovista/actions/workflows/ci-tests.yml) [![ci-wheels](https://github.com/bjlittle/geovista/actions/workflows/ci-wheels.yml/badge.svg)](https://github.com/bjlittle/geovista/actions/workflows/ci-wheels.yml) [![pre-commit](https://results.pre-commit.ci/badge/github/bjlittle/geovista/main.svg)](https://results.pre-commit.ci/latest/github/bjlittle/geovista/main) |
| 💬 Community | [![Contributor Covenant](https://img.shields.io/badge/contributor%20covenant-2.1-4baaaa.svg)](https://github.com/bjlittle/geovista/blob/main/CODE_OF_CONDUCT.md) [![GH Discussions](https://img.shields.io/badge/github-discussions%20%F0%9F%92%AC-yellow?logo=github&logoColor=lightgrey)](https://github.com/bjlittle/geovista/discussions)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             |
| 📈 Health    | [![codecov](https://codecov.io/gh/bjlittle/geovista/branch/main/graph/badge.svg?token=RVVXGP1SD3)](https://codecov.io/gh/bjlittle/geovista)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               |
| ✨ Meta       | [![geovista](https://img.shields.io/badge/%F0%9F%8C%8D-GeoVista-4051b5)](https://github.com/bjlittle/geovista) [![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/charliermarsh/ruff/main/assets/badge/v1.json)](https://github.com/charliermarsh/ruff) [![code style - black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black) [![NEP29](https://raster.shields.io/badge/follows-NEP29-orange.png)](https://numpy.org/neps/nep-0029-deprecation_policy.html) [![license - bds-3-clause](https://img.shields.io/github/license/bjlittle/geovista)](https://github.com/bjlittle/geovista/blob/main/LICENSE) [![conda platform](https://img.shields.io/conda/pn/conda-forge/geovista.svg)](https://anaconda.org/conda-forge/geovista)                                                                                                                                                                                                                 |
| 📦 Package   | [![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.7608302.svg)](https://doi.org/10.5281/zenodo.7608302) [![conda-forge](https://img.shields.io/conda/vn/conda-forge/geovista?color=orange&label=conda-forge&logo=conda-forge&logoColor=white)](https://anaconda.org/conda-forge/geovista) [![pypi](https://img.shields.io/pypi/v/geovista?color=orange&label=pypi&logo=python&logoColor=white)](https://pypi.org/project/geovista/) [![pypi - python version](https://img.shields.io/pypi/pyversions/geovista.svg?color=orange&logo=python&label=python&logoColor=white)](https://pypi.org/project/geovista/)                                                                                                                                                                                                                                                                                                                                                                                                           |
| 🧰 Repo      | [![commits-since](https://img.shields.io/github/commits-since/bjlittle/geovista/latest.svg)](https://github.com/bjlittle/geovista/commits/main) [![contributors](https://img.shields.io/github/contributors/bjlittle/geovista)](https://github.com/bjlittle/geovista/graphs/contributors) [![release](https://img.shields.io/github/v/release/bjlittle/geovista)](https://github.com/bjlittle/geovista/releases)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          |
| 🛡️ Status   | [![scitools](https://img.shields.io/badge/scitools-ownership%20pending-yellow)](https://github.com/bjlittle/geovista/issues/167)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          |
|              |                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           |


## Motivation

The goal of GeoVista is simple; to complement [PyVista](https://docs.pyvista.org/index.html) with a convenient
cartographic capability.

In this regard, from a design perspective we aim to keep GeoVista as **pure** to PyVista as possible i.e.,
**minimise specialisation** as far as practically possible in order to **maximise native compatibility** within the
PyVista and [VTK](https://vtk.org/) ecosystems.

We intend GeoVista to be a cartographic gateway into the powerful world of PyVista, and all that it offers.

GeoVista is intentionally agnostic to packages such as [geopandas](https://geopandas.org/en/stable/),
[iris](https://scitools-iris.readthedocs.io/en/latest/?badge=latest), [xarray](https://docs.xarray.dev/en/stable/)
et al, which specialise in preparing your spatial data for visualisation. Rather, we delegate that responsibility and
choice of tool to you the user, as we want GeoVista to remain as flexible and open-ended as possible to the entire
Scientific Python community.

Simply put, "*GeoVista is to PyVista*", as "*Cartopy is to Matplotlib*". Well, that's the aspiration.

## Installation

GeoVista is available on both [conda-forge](https://anaconda.org/conda-forge/geovista) and [PyPI](https://pypi.org/project/geovista/).

We recommend using [mamba](https://github.com/mamba-org/mamba) to install GeoVista 👍

### Mamba

GeoVista is available on [conda-forge](https://anaconda.org/conda-forge/geovista), and can be easily installed with
[mamba](https://github.com/mamba-org/mamba):
```shell
mamba install -c conda-forge geovista
```
or alternatively with [conda](https://docs.conda.io/projects/conda/en/latest/index.html):
```shell
conda install -c conda-forge geovista
```
For more information see our [conda-forge feedstock](https://github.com/conda-forge/geovista-feedstock) and
[prefix.dev dashboard](https://prefix.dev/channels/conda-forge/packages/geovista).

### Pip

GeoVista is also available on [PyPI](https://pypi.org/project/geovista/):

```shell
pip install geovista
```

Checkout out our [PyPI Download Stats](https://pypistats.org/packages/geovista), if you like that kinda thing.

### Developer

If you simply can't wait for the next release to play with the latest hot features, then you can easily
install the `main` development branch from GitHub:
```shell
pip install git+https://github.com/bjlittle/geovista@main
```

Alternatively, to configure a full developer environment, first clone the GeoVista GitHub repository:
```shell
git clone git@github.com:bjlittle/geovista.git
```
Change to the root directory:
```shell
cd geovista
```
Create the `geovista-dev` conda development environment:
```shell
mamba env create --file requirements/geovista.yml
```
Now activate the environment and install the `main` development branch of GeoVista:
```shell
conda activate geovista-dev
pip install --no-deps --editable .
```
Finally, you're good to roll 🥳

And for extra credit, install our developer `pre-commit` git-hooks:
```shell
pre-commit install
```

## Quick Start

GeoVista comes with various pre-canned resources to help get you started on your visualisation journey.

### Resources

GeoVista makes use of various resources, such as rasters, VTK meshes,
[Natural Earth](https://www.naturalearthdata.com/features/) features, and sample model data.

If you want to download and cache all registered GeoVista resources to make them available offline, simply:
```shell
geovista download --all
```
Alternatively, just leave GeoVista to download resources on-the-fly, as and when she needs them.

To view the list of registered resources, simply:
```shell
geovista download --list
```

Want to know more?
```shell
geovista download --help
```

### Plotting Examples

Let's explore a sample of various oceanographic and atmospheric model data using GeoVista.

#### WAVEWATCH III

First, let's render a [WAVEWATCH III](https://github.com/NOAA-EMC/WW3) (WW3) **unstructured** triangular mesh, with
[10m Natural Earth coastlines](https://www.naturalearthdata.com/downloads/10m-physical-vectors/10m-coastline/), a
[1:50m Natural Earth Cross-Blended Hypsometric Tints](https://www.naturalearthdata.com/downloads/50m-raster-data/50m-cross-blend-hypso/)
base layer, and the gorgeous perceptually uniform [cmocean balance](https://matplotlib.org/cmocean/#balance) diverging
colormap.

<details>
<summary>🗒 </summary>

```python
import geovista as gv
from geovista.pantry import ww3_global_tri
import geovista.theme

# Load the sample data.
sample = ww3_global_tri()

# Create the mesh from the sample data.
mesh = gv.Transform.from_unstructured(
    sample.lons, sample.lats, connectivity=sample.connectivity, data=sample.data
)

# Plot the mesh.
plotter = gv.GeoPlotter()
sargs = {"title": f"{sample.name} / {sample.units}"}
plotter.add_mesh(
    mesh, show_edges=True, scalar_bar_args=sargs
)
plotter.add_base_layer(texture=gv.natural_earth_hypsometric())
plotter.add_coastlines(resolution="10m")
plotter.add_graticule()
plotter.view_xy(negative=True)
plotter.add_axes()
plotter.show()
```
</details>

![ww3-tri](https://raw.githubusercontent.com/bjlittle/geovista-media/2023.09.1/media/readme/ww3-tri.png)

#### Finite Volume Community Ocean Model

Now, let's visualise the bathymetry of the
[Plymouth Sound and Tamar River](https://www.google.com/maps/place/Plymouth+Sound/@50.3337382,-4.2215988,12z/data=!4m5!3m4!1s0x486c93516bbce307:0xded7654eaf4f8f83!8m2!3d50.3638359!4d-4.1441365)
from an [FVCOM](http://fvcom.smast.umassd.edu/fvcom/) **unstructured** mesh, as kindly provided by the
[Plymouth Marine Laboratory](https://pml.ac.uk/) using the lush [cmocean deep](https://matplotlib.org/cmocean/#deep) colormap.

<details>
<summary>🗒 </summary>

```python
import geovista as gv
from geovista.pantry import fvcom_tamar
import geovista.theme

# Load the sample data.
sample = fvcom_tamar()

# Create the mesh from the sample data.
mesh = gv.Transform.from_unstructured(
    sample.lons,
    sample.lats,
    connectivity=sample.connectivity,
    data=sample.face,
    name="face",
)

# Warp the mesh nodes by the bathymetry.
mesh.point_data["node"] = sample.node
mesh.compute_normals(cell_normals=False, point_normals=True, inplace=True)
mesh.warp_by_scalar(scalars="node", inplace=True, factor=2e-5)

# Plot the mesh.
plotter = gv.GeoPlotter()
sargs = {"title": f"{sample.name} / {sample.units}"}
plotter.add_mesh(mesh, cmap="deep", scalar_bar_args=sargs)
plotter.add_axes()
plotter.show()
```
</details>

![tamar](https://raw.githubusercontent.com/bjlittle/geovista-media/2023.09.1/media/readme/tamar.png)

#### CF UGRID

##### Local Area Model

Initial projection support is available within GeoVista for **Cylindrical** and **Pseudo-Cylindrical** projections. As
GeoVista matures and stabilises, we'll aim to complement this capability with other classes of projections, such as
**Azimuthal** and **Conic**.

In the meantime, let's showcase our basic projection support with some high-resolution **unstructured** Local Area Model
(LAM) data reprojected to [Mollweide](https://proj.org/operations/projections/moll.html) using a
[PROJ](https://proj.org/index.html) string, with
[10m Natural Earth coastlines](https://www.naturalearthdata.com/downloads/10m-physical-vectors/10m-coastline/) and a
[1:50m Natural Earth Cross-Blended Hypsometric Tints](https://www.naturalearthdata.com/downloads/50m-raster-data/50m-cross-blend-hypso/)
base layer.

<details>
<summary>🗒 </summary>

```python
import geovista as gv
from geovista.pantry import lam_pacific
import geovista.theme

# Load the sample data.
sample = lam_pacific()

# Create the mesh from the sample data.
mesh = gv.Transform.from_unstructured(
    sample.lons,
    sample.lats,
    connectivity=sample.connectivity,
    data=sample.data,
)

# Plot the mesh on a mollweide projection using a Proj string.
plotter = gv.GeoPlotter(crs="+proj=moll")
sargs = {"title": f"{sample.name} / {sample.units}"}
plotter.add_mesh(mesh, scalar_bar_args=sargs)
plotter.add_coastlines()
plotter.add_base_layer(texture=gv.natural_earth_hypsometric())
plotter.add_graticule()
plotter.add_axes()
plotter.view_xy()
plotter.show()
```
</details>

![lam-mollweide](https://raw.githubusercontent.com/bjlittle/geovista-media/2023.09.1/media/readme/lam-moll.png)

Using the same **unstructured** LAM data, reproject to
[Equidistant Cylindrical](https://proj.org/operations/projections/eqc.html) but this time using a
[Cartopy Plate Carrée CRS](https://scitools.org.uk/cartopy/docs/latest/reference/projections.html#cartopy.crs.PlateCarree),
also with [10m Natural Earth coastlines](https://www.naturalearthdata.com/downloads/10m-physical-vectors/10m-coastline/)
and a
[1:50m Natural Earth Cross-Blended Hypsometric Tints](https://www.naturalearthdata.com/downloads/50m-raster-data/50m-cross-blend-hypso/)
base layer.

<details>
<summary>🗒 </summary>

```python
import cartopy.crs as ccrs

import geovista as gv
from geovista.pantry import lam_pacific
import geovista.theme

# Load the sample data.
sample = lam_pacific()

# Create the mesh from the sample data.
mesh = gv.Transform.from_unstructured(
    sample.lons,
    sample.lats,
    connectivity=sample.connectivity,
    data=sample.data,
)

# Plot the mesh on a Plate Carrée projection using a cartopy CRS.
plotter = gv.GeoPlotter(crs=ccrs.PlateCarree(central_longitude=180))
sargs = {"title": f"{sample.name} / {sample.units}"}
plotter.add_mesh(mesh, scalar_bar_args=sargs)
plotter.add_coastlines()
plotter.add_base_layer(texture=gv.natural_earth_hypsometric())
plotter.add_graticule()
plotter.add_axes()
plotter.view_xy()
plotter.show()
```
</details>

![lam-mollweide](https://raw.githubusercontent.com/bjlittle/geovista-media/2023.09.1/media/readme/lam-eqc.png)

#### LFRic Cube-Sphere

Now render a [Met Office LFRic](https://www.metoffice.gov.uk/research/approach/modelling-systems/lfric) C48 cube-sphere
**unstructured** mesh of Sea Surface Temperature data on a
[Robinson](https://proj.org/operations/projections/robin.html) projection using an ESRI SRID, with
[10m Natural Earth coastlines](https://www.naturalearthdata.com/downloads/10m-physical-vectors/10m-coastline/) and a
[cmocean thermal](https://matplotlib.org/cmocean/#thermal) colormap.

<details>
<summary>🗒 </summary>

```python
import geovista as gv
from geovista.pantry import lfric_sst
import geovista.theme

# Load the sample data.
sample = lfric_sst()

# Create the mesh from the sample data.
mesh = gv.Transform.from_unstructured(
    sample.lons,
    sample.lats,
    connectivity=sample.connectivity,
    data=sample.data,
)

# Plot the mesh on a Robinson projection using an ESRI spatial reference identifier.
plotter = gv.GeoPlotter(crs="ESRI:54030")
sargs = {"title": f"{sample.name} / {sample.units}"}
plotter.add_mesh(mesh, cmap="thermal", show_edges=True, scalar_bar_args=sargs)
plotter.add_coastlines()
plotter.view_xy()
plotter.add_axes()
plotter.show()
```
</details>

![lam-mollweide](https://raw.githubusercontent.com/bjlittle/geovista-media/2023.09.1/media/readme/lfric-robin.png)

#### UM ORCA2

So far we've demonstrated GeoVista's ability to cope with **unstructured** data. Now let's plot a **curvilinear** mesh
using Met Office Unified Model (UM) ORCA2 Sea Water Potential Temperature data, with
[10m Natural Earth coastlines](https://www.naturalearthdata.com/downloads/10m-physical-vectors/10m-coastline/) and a
[1:50m Natural Earth I](https://www.naturalearthdata.com/downloads/50m-raster-data/50m-natural-earth-1/) base layer.

<details>
<summary>🗒 </summary>

```python
import geovista as gv
from geovista.pantry import um_orca2
import geovista.theme

# Load sample data.
sample = um_orca2()

# Create the mesh from the sample data.
mesh = gv.Transform.from_2d(sample.lons, sample.lats, data=sample.data)

# Remove cells from the mesh with NaN values.
mesh = mesh.threshold()

# Plot the mesh.
plotter = gv.GeoPlotter()
sargs = {"title": f"{sample.name} / {sample.units}"}
plotter.add_mesh(
    mesh, show_edges=True, scalar_bar_args=sargs
)
plotter.add_base_layer(texture=gv.natural_earth_1())
plotter.add_coastlines(resolution="10m")
plotter.view_xy()
plotter.add_axes()
plotter.show()
```
</details>

![um-orca](https://raw.githubusercontent.com/bjlittle/geovista-media/2023.09.1/media/readme/um-orca.png)

#### OISST AVHRR

Now let's render a [NOAA/NCEI Optimum Interpolation SST](https://www.ncei.noaa.gov/products/optimum-interpolation-sst)
(OISST) Advanced Very High Resolution Radiometer (AVHRR) **rectilinear** mesh, with
[10m Natural Earth coastlines](https://www.naturalearthdata.com/downloads/10m-physical-vectors/10m-coastline/) and a
[NASA Blue Marble](https://visibleearth.nasa.gov/collection/1484/blue-marble) base layer.

<details>
<summary>🗒 </summary>

```python
import geovista as gv
from geovista.pantry import oisst_avhrr_sst
import geovista.theme

# Load sample data.
sample = oisst_avhrr_sst()

# Create the mesh from the sample data.
mesh = gv.Transform.from_1d(sample.lons, sample.lats, data=sample.data)

# Remove cells from the mesh with NaN values.
mesh = mesh.threshold()

# Plot the mesh.
plotter = gv.GeoPlotter()
sargs = {"title": f"{sample.name} / {sample.units}"}
plotter.add_mesh(mesh, scalar_bar_args=sargs)
plotter.add_base_layer(texture=gv.blue_marble())
plotter.add_coastlines()
plotter.view_xz()
plotter.add_axes()
plotter.show()
```
</details>

![oisst-avhrr](https://raw.githubusercontent.com/bjlittle/geovista-media/2023.09.1/media/readme/oisst-avhrr.png)

#### DYNAMICO Icosahedral

Finally, to demonstrate support for non-traditional cell geometries i.e., not triangles or quadrilaterals, we plot
the **unstructured** icosahedral mesh from the [DYNAMICO](https://gitlab.in2p3.fr/ipsl/projets/dynamico/dynamico)
project. This model uses hexagonal cells and is a new dynamical core for
[LMD-Z](https://www.lmd.ipsl.fr/en/modelisations/lmdz-en/), the atmospheric General Circulation Model (GCM) part of the
[IPSL-CM](https://cmc.ipsl.fr/ipsl-climate-models/) Earth System Model. The render also contains
[10m Natural Earth coastlines](https://www.naturalearthdata.com/downloads/10m-physical-vectors/10m-coastline/).

<details>
<summary>🗒 </summary>

```python
import geovista as gv
from geovista.pantry import icosahedral
import geovista.theme

# Load sample data.
sample = icosahedral()

# Create the mesh from the sample data.
mesh = gv.Transform.from_unstructured(sample.lons, sample.lats, data=sample.data)

# Plot the mesh.
plotter = gv.GeoPlotter()
sargs = {"title": f"{sample.name} / {sample.units}"}
plotter.add_mesh(mesh, scalar_bar_args=sargs)
plotter.add_coastlines()
plotter.add_axes()
plotter.show()
```
</details>

![dynamico-icosahedral](https://raw.githubusercontent.com/bjlittle/geovista-media/2023.09.1/media/readme/dynamico-icosahedral.png)

## Unreal Reels

GeoVista is built on the shoulders of giants, namely [PyVista](https://docs.pyvista.org/version/stable/) and
[VTK](https://vtk.org/documentation/), thus allowing it to easily leverage the power of the GPU.

As a result, it offers a paradigm shift in rendering performance and interactive user experience, as demonstrated by
this realtime, time-series animation of WAVEWATCH III® third-generation wave model (**WAVE**-height, **WAT**er depth
and **C**urrent **H**indcasting), developed at [NOAA](https://www.noaa.gov/)/[NCEP](https://www.weather.gov/ncep/),
quasi-unstructured Spherical Multi-Cell (SMC) grid data of Sea Surface Wave Significant Height located on cell faces.

[🎥 WW3 SMC time-series](https://github.com/bjlittle/geovista/assets/2051656/876d877e-a6fa-42ff-8153-08c41ff8a19e)

## Further Examples

<p align="center">
"<em>Please, sir, I want some more</em>", Charles Dickens, Oliver Twist, 1838.
</p>

Certainly, our pleasure! From the command line, simply:

```bash
geovista examples --run all --verbose
```

Want to know more?
```shell
geovista examples --help
```

<!---
## Documentation

The [documentation](https://geovista.readthedocs.io/en/latest/) is built by [Sphinx](https://www.sphinx-doc.org/en/master/) and hosted on [Read the Docs](https://docs.readthedocs.io/en/stable/).
-->

## Ecosystem

Whilst you're here, why not hop on over to the [pyvista-xarray](https://github.com/pyvista/pyvista-xarray) project and
check it out!

It's aiming to provide `xarray DataArray accessors for PyVista to visualize datasets in 3D` for the
[xarray](https://github.com/pydata/xarray) community, and will be building on top of GeoVista 🎉

## Support

Need help? 😢

Why not check out our [existing GitHub issues](https://github.com/bjlittle/geovista/issues). See something similar?
Well, give it a 👍 to raise its priority and feel free to chip in on the conversation. Otherwise, don't hesitate to
create a [new GitHub issue](https://github.com/bjlittle/geovista/issues/new/choose) instead.

However, if you'd rather have a natter, then head on over to our
[GitHub Discussions](https://github.com/bjlittle/geovista/discussions). That's definitely the place to wax lyrical all
things GeoVista!


## License

GeoVista is distributed under the terms of the [BSD-3-Clause](https://spdx.org/licenses/BSD-3-Clause.html) license.

## [#ShowYourStripes](https://showyourstripes.info/s/globe)

<h4 align="center">
  <a href="https://showyourstripes.info/s/globe">
    <img src="https://raw.githubusercontent.com/ed-hawkins/show-your-stripes/master/2022/GLOBE---1850-2022-MO.png"
         height="50" width="800"
         alt="#showyourstripes Global 1850-2022"></a>
</h4>

**Graphics and Lead Scientist**: [Ed Hawkins](http://www.met.reading.ac.uk/~ed/home/index.php), National Centre for Atmospheric Science, University of Reading.

**Data**: Berkeley Earth, NOAA, UK Met Office, MeteoSwiss, DWD, SMHI, UoR, Meteo France & ZAMG.

<p>
<a href="https://showyourstripes.info/s/globe">#ShowYourStripes</a> is distributed under a
<a href="https://creativecommons.org/licenses/by/4.0/">Creative Commons Attribution 4.0 International License</a>
<a href="https://creativecommons.org/licenses/by/4.0/">
  <img src="https://i.creativecommons.org/l/by/4.0/80x15.png" alt="creative-commons-by" style="border-width:0"></a>
</p>
