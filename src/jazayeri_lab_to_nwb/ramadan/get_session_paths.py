"""Function for getting paths to data on openmind."""

import collections
import pathlib

# TODO: If you want subject names to be different, change this.
SUBJECT_NAME_TO_ID = {
    "Faure": "monkey0",
    "Nielsen": "monkey1",
}

SessionPaths = collections.namedtuple(
    "SessionPaths",
    [
        "behavior", 
        "phys",
        "output",
        "start_time",
    ],
)

def _get_session_paths_openmind(subject, session):
    """Get paths to all components of the data on openmind."""

    output_path = ('./output')
    behavior_path = f"/om2/user/mramadan/Neurophys/Sorting/Analysis/NP/{subject}/Good_Trials/{session}_good_trials_concat.mat"

    start_time_data_type='_t0.imec0.lf.meta'
    start_time_path = f"/om4/group/jazlab/Mahdi/Neurophys/Sorting/Data_KS/Faure/NP/{session}/{session}_imec0/{session}{start_time_data_type}"

    binned_data_type='_whole_trial_FR'
    phys_path = f"/om2/user/mramadan/Neurophys/Sorting/Analysis/NP/{subject}/Firing_Rates/{session}{binned_data_type}.mat"

    # output_path = ('./output')
    # behavior_path = f"/Volumes/Portable/Kilosort/{session}/{session}_good_trials_concat.mat"

    # start_time_data_type='_t0.imec0.lf.meta'
    # start_time_path = f"/Volumes/Portable/Kilosort/{session}/{session}{start_time_data_type}"

    # binned_data_type='_whole_trial_FR'
    # phys_path = f"/Volumes/Portable/Kilosort/{session}/{session}{binned_data_type}.mat"

    session_paths = SessionPaths(
        output=pathlib.Path(output_path),
        behavior=pathlib.Path(behavior_path),
        phys=pathlib.Path(phys_path),
        start_time = pathlib.Path(start_time_path),
    )

    return session_paths


def _get_session_paths_globus(subject, session):
    """Get paths to all components of the data in the globus repo."""
    subject_id = SUBJECT_NAME_TO_ID[subject]
    base_data_dir = f"/shared/catalystneuro/JazLab/{subject_id}/{session}/"

    # Path to write output nwb files to
    output_path = f"~/conversion_nwb/jazayeri-lab-to-nwb"

    # Path to the raw data. This is used for reading raw physiology data.
    raw_data_path = f"{base_data_dir}/raw_data"

    # Path to task and behavior data.
    task_behavior_data_path = f"{base_data_dir}/processed_task_data"

    # Path to open-source data. This is used for reading behavior and task data.
    data_open_source_path = f"{base_data_dir}/data_open_source"

    # Path to sync pulses. This is used for reading timescale transformations
    # between physiology and mworks data streams.
    sync_pulses_path = f"{base_data_dir}/sync_pulses"

    # Path to spike sorting. This is used for reading spike sorted data.
    spike_sorting_raw_path = f"{base_data_dir}/spike_sorting"

    session_paths = SessionPaths(
        output=pathlib.Path(output_path),
        raw_data=pathlib.Path(raw_data_path),
        data_open_source=pathlib.Path(data_open_source_path),
        task_behavior_data=pathlib.Path(task_behavior_data_path),
        sync_pulses=pathlib.Path(sync_pulses_path),
        spike_sorting_raw=pathlib.Path(spike_sorting_raw_path),
    )

    return session_paths


def get_session_paths(subject, session, repo="openmind"):
    """Get paths to all components of the data.

    Returns:
        SessionPaths namedtuple.
    """

    return _get_session_paths_openmind(subject=subject, session=session)