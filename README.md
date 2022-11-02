# hamsci_psws

[![Documentation Status](https://readthedocs.org/projects/hamsci-psws/badge/?version=latest)](https://hamsci-psws.readthedocs.io/en/latest/?badge=latest)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.7023781.svg)](https://doi.org/10.5281/zenodo.7023781)


Plotting data from Grape V1 receivers.

In terminal, clone repository and install with `pip install .`.

To begin, download the most recent dataset from [![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.6622112.svg)](https://doi.org/10.5281/zenodo.6622111) and unzip it into the `scripts/data/` directory. You can then run the Jupyter notebooks in the `scripts` directory to produce plots. 


## Installation

hamsci_psws includes both a reusuable Python package (intended to be imported and reused by other projects) and a set of scripts and interactive notebooks using that package. How you should install hamsci_psws depends on how you intend to use it.

**If you want to run the interactive notebooks**, you should download this repository and install from it. **If you want to use the library in other projects**, you can either do that or just install the library from a package index.

### If you want to run the interactive notebooks

Make sure you have a recent Python version and Jupyter installed.

Clone this repository into a suitable location on your computer:

`git clone https://github.com/HamSCI/hamsci_psws`

`cd hamsci_psws`

`pip install .`

You should now be able to open and run the notebooks within `scripts/` using Jupyter.

### If you want to use the library in other projects

#### From the Python Package Index:

The hamsci_psws package is distributed on the Python Package Index: https://pypi.org/project/hamsci_psws/

`pip install hamsci_psws`

#### From the git repository:

Follow the same instructions as installing the interactive notebooks.


## Getting Started


## Folder Structure

- `hamsci_psws` -  the python package
- `scripts` - example analysis scripts and Jupyter notebooks
- `deprecate`, `scripts/deprecate`, etc. - files that will be removed in future versions


## Contributing

Contributions to HamSCI projects are welcome. See https://hamsci.org/get-involved for general information about getting involved in the HamSCI community.

### Development Environment

Clone this repository into a suitable location on your computer:

`git clone https://github.com/HamSCI/hamsci_psws`

`cd hamsci_psws`

Install the repository in 'editable' mode:

`pip install -e .`

### Building the Documentation

`cd docs`

`make html`

Open `build/html/index.html` in a web browser.

Within `docs/`, `make clean` can be used to ensure a clean slate for rebuilding the documentation.


Documentation for hamsci_psws is hosted on Read the Docs: https://hamsci-psws.readthedocs.io/en/latest/



### Releasing the Package

To upload a release, you will need an account at https://pypi.org/, and an API token for that account.

1. Make sure you have the latest version of [pip](https://pip.pypa.io/en/stable/):

`pip install --upgrade pip`

2. Make sure you have the latest version of [build](https://pypa-build.readthedocs.io/en/stable/index.html) and [twine](https://twine.readthedocs.io/en/latest/):

`pip install --upgrade build twine`

3. Each new release will need an incremented version number in `pyproject.toml`.

4. Build the package (from the root directory of the project).

`python -m build`

5. Upload to [PyPI](https://pypi.org/):

`python -m twine upload dist/*`

Enter `__token__` as the user name, and your token as the token, including the `pypi-` prefix.

6. Test package installation, preferrably in a separate environment from where you are developing.

`pip install hamsci_psws`

More info: https://packaging.python.org/en/latest/tutorials/packaging-projects/


## Citing this Project

You can use `CITATION.cff`.
