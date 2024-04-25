"""Function for getting paths to data on openmind."""

import collections
import pathlib


SESSION_TO_ECEPHYS_DIR = {
   

    'mahler': {
        "04122021_a": "mahler_2021-04-12_13-11-22__a/",
        "04132021_a": "mahler_2021-04-13_13-41-58__a/",
        "04142021_a": "mahler_2021-04-14_13-06-04__a/",
        "04212021_a": "mahler_2021-04-21_12-38-38__a/",
        "04222021_b": "mahler_2021-04-22_13-56-54__b/",
        "04252021_a": "mahler_2021-04-25_15-02-38__a/",
        "04272021_a": "mahler_2021-04-27_14-01-16__a/"
    }
}
SessionPaths = collections.namedtuple(
    "SessionPaths",
    [
        "output",
        "ecephys",
        "behavior",
        "spike_sorting",
        "sync_pulses",
    ],
)

def _get_session_paths_openmind(subject, session):
    """Get paths to all components of the data on openmind."""
    # TODO: Get write access to /om/ for both me and sujay

    # Path to write output nwb files to
    output_path = (
        # f"/om/user/sneupane/nwb_data/staging/sub-{subject}"
        f"/om/user/sneupane/sujay_nwb/staging/sub-{subject}"
    )
    session_id = f"{subject}{session}"
    # Path to the raw physiology data.
    ecephys_path = (
        f"/om4/group/jazlab/sujay_backup/mtt_data_mahler/{SESSION_TO_ECEPHYS_DIR[subject][session]}/"
    )

    # Path to task and behavior data.
    behavior_path = f'/om4/group/jazlab/sujay_backup/nwb/physiology_data_for_sharing/EC/{subject}{session}.mwk'

    # Path to spike sorting. This is used for reading spike sorted data.
    # TODO: Handle sessions with multiple MWorks sessions
    spike_sorting_path = (
        f"/om4/group/jazlab/sujay_backup/nwb/spike_sorted_data/{session_id}"
    )

    sync_pulses_path = (f"/om4/group/jazlab/sujay_backup/mtt_data/{session_id}.mwk")

    session_paths = SessionPaths(
        output=pathlib.Path(output_path),
        ecephys=pathlib.Path(ecephys_path),
        behavior=pathlib.Path(behavior_path),
        sync_pulses=pathlib.Path(sync_pulses_path),
        spike_sorting=pathlib.Path(spike_sorting_path),
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
