"""Function for getting paths to data on openmind."""

import collections
import pathlib



SessionPaths = collections.namedtuple(
    "SessionPaths",
    [
        "output",
        "ecephys",
        "behavior",
        "spike_sorting",
        "sync_pulses",
        "session_start_time"
    ],
)

def _get_session_paths_openmind(subject, session):
    """Get paths to all components of the data on openmind."""
    # TODO: Get write access to /om/ for both me and sujay

    # Path to write output nwb files to
    output_path = (
        f"/om2/user/apiccato/sujay_nwb/staging/sub-{subject}"
    )

    # Path to the raw physiology data.
    # TODO: Find session open ephys directory
    # ecephys_path = (
    #     f"/om4/group/jazlab/sujay_backup/mtt_data/{subject}_{session}"
    # )
    ecephys_path = "/om4/group/jazlab/sujay_backup/mtt_data/amadeus_2019-08-29_12-29-52__a/"

    # Path to task and behavior data.
    # behavior_path = (
    #     "/om4/group/jazlab/sujay_backup/multi_prediction/datasets/data_nwb_trials/"
    #     f"{subject}/{session}"
    # )
    behavior_path = '/om4/group/jazlab/sujay_backup/nwb/physiology_data_for_sharing/EC/amadeus08292019_a.mwk'

    # Path to spike sorting. This is used for reading spike sorted data.
    # TODO: Handle sessions with multiple sessions
    spike_sorting_path = (
        f"/om4/group/jazlab/sujay_backup/nwb/spike_sorted_data/{subject}_{session}"
    )

    # TODO: Handle naming of sync pulses directory
    sync_pulses_path = (f"/om4/group/jazlab/sujay_backup/mtt_data/amadeus08292019_a.mwk")

    # TODO: Find session start time
    session_start_time_path = (f"/om4/group/jazlab/sujay_backup/mtt_data/amadeus08292019_a.mwk/amadeus08292019_a.mat")

    session_paths = SessionPaths(
        output=pathlib.Path(output_path),
        ecephys=pathlib.Path(ecephys_path),
        behavior=pathlib.Path(behavior_path),
        sync_pulses=pathlib.Path(sync_pulses_path),
        spike_sorting=pathlib.Path(spike_sorting_path),
        session_start_time=pathlib.Path(session_start_time_path),
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
