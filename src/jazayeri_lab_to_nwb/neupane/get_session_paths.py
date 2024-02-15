"""Function for getting paths to data on openmind."""

import collections
import pathlib


SESSION_TO_ECEPHYS_DIR = {
    'amadeus': {
        '08292019': "amadeus_2019-08-29_12-29-52__a/"
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
        f"/om/user/apiccato/sujay_nwb/staging/sub-{subject}"
    )
    session_id = f"{subject}{session}"
    # Path to the raw physiology data.
    ecephys_path = (
        f"/om4/group/jazlab/sujay_backup/mtt_data/{SESSION_TO_ECEPHYS_DIR[subject][session]}/"
    )

    # Path to task and behavior data.
    behavior_path = f'/om4/group/jazlab/sujay_backup/nwb/physiology_data_for_sharing/EC/{subject}{session}_a.mwk'

    # Path to spike sorting. This is used for reading spike sorted data.
    # TODO: Handle sessions with multiple MWorks sessions
    spike_sorting_path = (
        f"/om4/group/jazlab/sujay_backup/nwb/spike_sorted_data/{session_id}_a"
    )

    sync_pulses_path = (f"/om4/group/jazlab/sujay_backup/mtt_data/{session_id}_a.mwk")

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
