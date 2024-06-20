"""Function for getting paths to data on openmind."""

import collections
import pathlib

SUBJECT_NAME_TO_ID = {
    "elgar": "elgar",
}

OM_PATH = "/om2/user/apiccato/phys_preprocessing_open_source/phys_data"
DANDISET_ID = "000767"
SessionPaths = collections.namedtuple(
    "SessionPaths",
    [
        "output",
        "ecephys_data",
        "behavior_task_data",
        "session_data",
        "sync_pulses",
        "spike_sorting_raw",
        "postprocessed_data",
    ],
)


def _get_session_paths_openmind(subject, session):
    """Get paths to all components of the data on openmind."""
    # subject_id = SUBJECT_NAME_TO_ID[subject]

    # Path to write output nwb files to
    output_path = pathlib.Path(
        f"/om2/user/apiccato/nwb_data/staging/{DANDISET_ID}/sub-{subject}"
    )

    # Path to the raw data. This is used for reading raw physiology data.
    ecephys_data_path = pathlib.Path(
        f"{OM_PATH}/{subject}/{session}/raw_data/"
    )

    # Path to task and behavior data.
    behavior_task_data_path = pathlib.Path(
        f"{OM_PATH}/{subject}/{session}/behavior_task"
    )

    # Path to sync pulses. This is used for reading timescale transformations
    # between physiology and mworks data streams.
    sync_pulses_path = pathlib.Path(
        f"{OM_PATH}/{subject}/{session}/sync_signals"
    )

    # Path to spike sorting. This is used for reading spike sorted data.
    spike_sorting_raw_path = pathlib.Path(
        f"{OM_PATH}/{subject}/{session}/spike_sorting"
    )

    session_path = pathlib.Path(f"{OM_PATH}/{subject}/{session}/")

    postprocessed_data_path = pathlib.Path(
        f"{OM_PATH}/{subject}/{session}/kilosort2_5_0"
    )

    session_paths = SessionPaths(
        output=output_path,
        ecephys_data=ecephys_data_path,
        session_data=session_path,
        behavior_task_data=pathlib.Path(behavior_task_data_path),
        sync_pulses=sync_pulses_path,
        spike_sorting_raw=spike_sorting_raw_path,
        postprocessed_data=postprocessed_data_path,
    )

    return session_paths


def get_session_paths(subject, session, repo="openmind"):
    """Get paths to all components of the data.

    Returns:
        SessionPaths namedtuple.
    """
    if repo == "openmind":
        return _get_session_paths_openmind(subject=subject, session=session)
    else:
        raise ValueError(f"Invalid repo {repo}")
