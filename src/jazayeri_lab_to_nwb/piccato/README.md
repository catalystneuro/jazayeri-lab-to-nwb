# Piccato data conversion pipeline
NWB conversion scripts for Piccato data to the [Neurodata Without Borders](https://nwb-overview.readthedocs.io/) data format.


## Usage
To run a specific conversion, you might need to install first some conversion specific dependencies that are located in each conversion directory:

```
pip install -r src/jazayeri_lab_to_nwb/piccato/requirements.txt
```

You can run a specific conversion with the following command:
```
python src/jazayeri_lab_to_nwb/piccato/main_convert_session.py $SUBJECT $SESSION
```

### Piccato working and long-term memory task data
The conversion function for this experiment, `session_to_nwb`, is found in `src/piccato/main_convert_session.py`. The function takes arguments:
* `subject` subject name (currently only `'elgar'`.)
* `session` session date in format `'YYYY-MM-DD'`.
* `stub_test` indicates whether only a small portion of the data should be saved (mainly used by us for testing purposes).
* `overwrite` indicates whether to overwrite nwb output files.

The function can be imported in a separate script with and run, or you can run the file directly and specify the arguments in the `if name == "__main__"` block at the bottom.

The function expects the raw data in `data_dir_path` to follow this structure:
```
   data_dir_path/
   ├── behavior_task
   │   ├── eye.h.json, eye.v.json, etc.
   │   ├── trials.json
   ├── raw_data
   │   ├── behavior
   │       └── mworks
   │       └── moog
   │   ├── spikeglx
   │       └── */*/*.ap.bin, */*/*.lf.bin, etc.
   ├── spike_sorting
   │   ├── spikeglx
   │       └── kilosort2_5_0
   ├── phys_metadata.json
   ├── sync_signals
       └── spikeglx
       	   └── transform
```
The conversion will try to automatically fetch metadata from the provided data directory. However, some information, such as the subject's name and age, must be specified by the user in the file `src/jazayeri_lab_to_nwb/piccato/metadata.yaml`. If any of the automatically fetched metadata is incorrect, it can also be overriden from this file.

The converted data will be saved in two files, one called `{session_id}_ecephys.nwb`, which contains the raw electrophysiology data from the Neuropixels and V-Probes, and one called `{session_id}_behavior+ecephys.nwb` with behavioral data, trial info, and sorted unit spiking.

If you run into memory issues when writing the `{session_id}_ecephys.nwb` files, you may want to set `buffer_gb` to a value smaller than 1 (its default) in the `conversion_options` dicts for the recording interfaces, i.e. [here](https://github.com/catalystneuro/jazayeri-lab-to-nwb/blob/vprobe_dev/src/jazayeri_lab_to_nwb/watters/main_convert_session.py#L189).
