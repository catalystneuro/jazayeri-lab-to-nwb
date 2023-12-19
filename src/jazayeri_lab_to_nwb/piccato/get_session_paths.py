"""Function for getting paths to data on openmind."""

import collections
import pathlib

SUBJECT_NAME_TO_ID = {
    "elgar": "elgar",
}

SessionPaths = collections.namedtuple(
    "SessionPaths",
    [
        "output",
        "raw_data",
        # "data_open_source",
        "task_behavior_data",
        "sync_pulses",
        "spike_sorting_raw",
    ],
)


def _get_session_paths_openmind(subject, session):
    """Get paths to all components of the data on openmind."""
    # subject_id = SUBJECT_NAME_TO_ID[subject]

    # Path to write output nwb files to
    output_path = f"/om2/user/apiccato/nwb_data/staging/sub-{subject}"

    # Path to the raw data. This is used for reading raw physiology data.
    raw_data_path = pathlib.Path(
        "/om4/group/jazlab/apiccato/",
        "phys_preprocessing_open_source/phys_data/",
        f"{session}/raw_data/{subject}/")

    # Path to task and behavior data.
    task_behavior_data_path = pathlib.Path(
        "/om4/group/jazlab/apiccato/phys_preprocessing_open_source/",
        f"{subject}/{session}"
    )

    # # Path to open-source data. This is used for reading behavior and task data.
    # data_open_source_path = (
    #     "/om4/group/jazlab/nwatters/multi_prediction/datasets/data_open_source/" f"Subjects/{subject_id}/{session}/001"
    # )

    # Path to sync pulses. This is used for reading timescale transformations
    # between physiology and mworks data streams.
    sync_pulses_path = pathlib.Path(
        "/om4/group/jazlab/phys_preprocessing_open_source",
        f"{subject}/{session}/sync_signals"
    )

    # Path to spike sorting. This is used for reading spike sorted data.
    spike_sorting_raw_path = pathlib.Path(
        "/om4/group/jazlab/apiccato/phys_preprocessing_open_source/"
        f"{subject}/{session}/spike_sorting"
    )

    session_paths = SessionPaths(
        output=output_path,
        raw_data=raw_data_path,
        # data_open_source=pathlib.Path(data_open_source_path),
        task_behavior_data=task_behavior_data_path,
        sync_pulses=sync_pulses_path,
        spike_sorting_raw=spike_sorting_raw_path,
    )

    return session_paths

# TODO: Update Globus paths when these are available

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
    if repo == "openmind":
        return _get_session_paths_openmind(subject=subject, session=session)
    elif repo == "globus":
        return _get_session_paths_globus(subject=subject, session=session)
    else:
        raise ValueError(f"Invalid repo {repo}")
