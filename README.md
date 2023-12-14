# jazayeri-lab-to-nwb
NWB conversion scripts for Jazayeri lab data to the [Neurodata Without Borders](https://nwb-overview.readthedocs.io/) data format.


## Installation
The package can be installed from this GitHub repo, which has the advantage that the source code can be modifed if you need to amend some of the code we originally provided to adapt to future experimental differences. To install the conversion from GitHub you will need to use `git` ([installation instructions](https://github.com/git-guides/install-git)). The package also requires Python 3.9 or 3.10. We also recommend the installation of `conda` ([installation instructions](https://docs.conda.io/en/latest/miniconda.html)) as it contains all the required machinery in a single and simple instal

From a terminal (note that conda should install one in your system) you can do the following:

```
git clone https://github.com/catalystneuro/jazayeri-lab-to-nwb
cd jazayeri-lab-to-nwb
conda env create --file make_env.yml
conda activate jazayeri-lab-to-nwb-env
```

This creates a [conda environment](https://docs.conda.io/projects/conda/en/latest/user-guide/concepts/environments.html) which isolates the conversion code from your system libraries.  We recommend that you run all your conversion related tasks and analysis from the created environment in order to minimize issues related to package dependencies.

Alternatively, if you have Python 3.9 or 3.10 on your machine and you want to avoid conda altogether (for example if you use another virtual environment tool) you can install the repository with the following commands using only pip:

```
git clone https://github.com/catalystneuro/jazayeri-lab-to-nwb
cd jazayeri-lab-to-nwb
pip install -e .
```

Note:
both of the methods above install the repository in [editable mode](https://pip.pypa.io/en/stable/cli/pip_install/#editable-installs).

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
        │       ├── behavior_interface.py
        │       ├── main_convert_session.py
        │       ├── metadata.yml
        │       ├── nwb_converter.py
        │       ├── requirements.txt
        │       └── __init__.py
        │   └── another_conversion
        └── __init__.py

 For example, for the conversion `watters` you can find a directory located in `src/jazayeri-lab-to-nwb/watters`. Inside each conversion directory you can find the following files:

* `main_convert_sesion.py`: this script defines the function to convert one full session of the conversion.
* `requirements.txt`: dependencies specific to this conversion.
* `metadata.yml`: metadata in yaml format for this specific conversion.
* `behavior_interface.py`: the behavior interface. Usually ad-hoc for each conversion.
* `nwb_converter.py`: the place where the `NWBConverter` class is defined.

The directory might contain other files that are necessary for the conversion but those are the central ones.


## Running a specific conversion
To run a specific conversion, you might need to install first some conversion specific dependencies that are located in each conversion directory:
```
pip install -r src/jazayeri_lab_to_nwb/watters/watters_requirements.txt
```

You can run a specific conversion with the following command:
```
python src/jazayeri_lab_to_nwb/watters/main_convert_session.py $SUBJECT $SESSION
```

### Watters working memory task data
The conversion function for this experiment, `session_to_nwb`, is found in `src/watters/main_convert_session.py`. The function takes arguments:
* `subject` subject name, either `'Perle'` or `'Elgar'`.
* `session` session date in format `'YYYY-MM-DD'`.
* `stub_test` indicates whether only a small portion of the data should be saved (mainly used by us for testing purposes).
* `overwrite` indicates whether to overwrite nwb output files.
* `dandiset_id` optional dandiset ID.

The function can be imported in a separate script with and run, or you can run the file directly and specify the arguments in the `if name == "__main__"` block at the bottom.

The function expects the raw data in `data_dir_path` to follow this structure:

    data_dir_path/
    ├── data_open_source
    │   ├── behavior
    │   │   └── eye.h.times.npy, etc.
    │   ├── task
    │       └── trials.start_times.json, etc.
    │   └── probes.metadata.json
    ├── raw_data
    │   ├── spikeglx
    │       └── */*/*.ap.bin, */*/*.lf.bin, etc.
    │   ├── v_probe_0
    │       └── raw_data.dat
    │   └── v_probe_{n}
    │       └── raw_data.dat
    ├── spike_sorting_raw
    │   ├── np
    │   ├── vp_0
    │   └── vp_{n}
    ├── sync_pulses
        ├── mworks
        ├── open_ephys
        └── spikeglx
    ...

The conversion will try to automatically fetch metadata from the provided data directory. However, some information, such as the subject's name and age, must be specified by the user in the file `src/jazayeri_lab_to_nwb/watters/metadata.yaml`. If any of the automatically fetched metadata is incorrect, it can also be overriden from this file.

The converted data will be saved in two files, one called `{session_id}_raw.nwb`, which contains the raw electrophysiology data from the Neuropixels and V-Probes, and one called `{session_id}_processed.nwb` with behavioral data, trial info, and sorted unit spiking.

If you run into memory issues when writing the `{session_id}_raw.nwb` files, you may want to set `buffer_gb` to a value smaller than 1 (its default) in the `conversion_options` dicts for the recording interfaces, i.e. [here](https://github.com/catalystneuro/jazayeri-lab-to-nwb/blob/vprobe_dev/src/jazayeri_lab_to_nwb/watters/main_convert_session.py#L189).
