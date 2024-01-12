# Watters data conversion pipeline
NWB conversion scripts for Nick Watters working memory data to the
[Neurodata Without Borders](https://nwb-overview.readthedocs.io/) data format.

## Usage
To run a specific conversion, you might need to install first some conversion
specific dependencies that are located in each conversion directory:
```
pip install -r src/jazayeri_lab_to_nwb/watters/watters_requirements.txt
```

You can run a specific conversion with the following command:
```
python src/jazayeri_lab_to_nwb/watters/main_convert_session.py $SUBJECT $SESSION
```

where `$SUBJECT` is in `['Perle', 'Elgar']` and `$SESSION` is a session date in
format `'YYYY-MM-DD'`. For example:
```
python src/jazayeri_lab_to_nwb/watters/main_convert_session.py Perle 2022-06-01
```

The conversion function for this experiment, `session_to_nwb`, is found in
`src/watters/main_convert_session.py`. The function takes arguments:
* `subject` subject name, either `'Perle'` or `'Elgar'`.
* `session` session date in format `'YYYY-MM-DD'`.
* `stub_test` indicates whether only a small portion of the data should be
saved (used for testing purposes).
* `overwrite` indicates whether to overwrite nwb output files.

The function can be imported in a separate script with and run, or you can run
the file directly and specify the arguments in the `if name == "__main__"`
block at the bottom.

## Data format

The function expects there to exist data paths with this structure:
```
    trials
        ├── eye_h_calibrated.json
        ├── eye_v_calibrated.json
        ├── pupil_size_r.json
        ├── reward_line.json
        ├── sound.json
        └── trials.json
    data_open_source
        └── probes.metadata.json
    raw_data
        ├── spikeglx
            └── */*/*.ap.bin, */*/*.lf.bin, etc.
        ├── v_probe_0
            └── raw_data.dat
        └── v_probe_{n}
            └── raw_data.dat
    spike_sorting
        ├── np
        ├── v_probe_0
        └── v_probe_{n}
    sync_pulses
        ├── mworks
        ├── open_ephys
        └── spikeglx
```
Each of the top-level directories may lie in different filesystems. The script
`get_session_paths.py` contains a function to fetch them given subject and session.

The converted data will be saved in two files in
`/om/user/nwatters/nwb_data_multi_prediction/staging/sub-$SUBJECT/`:
    sub-$SUBJECT_ses-$SESSION_ecephys.nwb --- Raw physiology
    sub-$SUBJECT_ses-$SESSION_behavior+ecephys.nwb --- Task, behavior, and
        sorted physiology

If you run into memory issues when writing the `{session_id}_raw.nwb` files,
you may want to set `buffer_gb` to a value smaller than 1 (its default) in the
`conversion_options` dicts for the recording interfaces, i.e.
[here](https://github.com/catalystneuro/jazayeri-lab-to-nwb/blob/vprobe_dev/src/jazayeri_lab_to_nwb/watters/main_convert_session.py#L189).

## Uploading to DANDI

To upload from openmind to DANDI, first log into the openmind data transfer
node, e.g. `ssh nwatters@openmind-dtn.mit.edu`. Then navigate to the directory
with the NWB files, e.g.
`/om/user/nwatters/nwb_data_multi_prediction/staging/`. Finally, run the steps
in the
[DANDI uploading pipeline](https://www.dandiarchive.org/handbook/13_upload/#data-uploadmanagement-workflow).

Note that you must pip install dandi to run the uploading steps, and in order
to activate a conda environment in openmind-dtn you may have to run
`$ source ~/.bashrc` in the openmind-dtn terminal. Also not that DANDI
uploading entire sessions of raw data can take a while, so it is convenient to
run it in a tmux terminal on openmind-dtn.
