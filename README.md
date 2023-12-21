# jazayeri-lab-to-nwb
NWB conversion scripts for Jazayeri lab data to the
[Neurodata Without Borders](https://nwb-overview.readthedocs.io/) data format.


## Installation
The package can be installed from this GitHub repo, which has the advantage that
the source code can be modifed if you need to amend some of the code we
originally provided to adapt to future experimental differences. To install the
conversion from GitHub you will need to use `git`
([installation instructions](https://github.com/git-guides/install-git)). The
package also requires Python 3.9 or 3.10. We also recommend the installation of
`conda`
([installation instructions](https://docs.conda.io/en/latest/miniconda.html)) as
it contains all the required machinery in a single and simple instal

From a terminal (note that conda should install one in your system) you can do
the following:

```
git clone https://github.com/catalystneuro/jazayeri-lab-to-nwb
cd jazayeri-lab-to-nwb
conda env create --file make_env.yml
conda activate jazayeri-lab-to-nwb-env
```

This creates a
[conda environment](https://docs.conda.io/projects/conda/en/latest/user-guide/concepts/environments.html)
which isolates the conversion code from your system libraries.  We recommend
that you run all your conversion related tasks and analysis from the created
environment in order to minimize issues related to package dependencies.

Alternatively, if you have Python 3.9 or 3.10 on your machine and you want to
avoid conda altogether (for example if you use another virtual environment tool)
you can install the repository with the following commands using only pip:

```
git clone https://github.com/catalystneuro/jazayeri-lab-to-nwb
cd jazayeri-lab-to-nwb
pip install -e .
```

Note:
both of the methods above install the repository in
[editable mode](https://pip.pypa.io/en/stable/cli/pip_install/#editable-installs)
.

## Repository structure
Each conversion is organized in a directory of its own in the `src` directory:

    jazayeri-lab-to-nwb/
    ├── LICENSE
    ├── make_env.yml
    ├── pyproject.toml
    ├── README.md
    ├── requirements.txt
    ├── setup.py
    └── src
        ├── jazayeri_lab_to_nwb
        │   ├── watters
        │       ├── README.md
        │       ├── __init__.py
        │       ├── main_convert_session.py
        │       ├── requirements.txt
        │       ├── metadata.yml
        │       └── ...
        │   └── another_conversion
        └── __init__.py

 For example, for the conversion `watters` you can find a directory located in
 `src/jazayeri-lab-to-nwb/watters`. Inside each conversion directory you can
 find the following files:

* `main_convert_sesion.py`: this script defines the function to convert one full
session of the conversion.
* `requirements.txt`: dependencies specific to this conversion.
* `metadata.yml`: metadata in yaml format for this specific conversion.

Please read `README.md` in the conversion directory for usage and instructions
for running a conversion.
