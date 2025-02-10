"""Function for getting paths to data on openmind."""

import collections
import pathlib


SESSION_TO_ECEPHYS_DIR = {
   
#change folder here for vprobe vs NP probe
    'mahler': {
        "03122021_a": "03122021_mahler_g0/03122021_mahler_g0_imec0/",
        "03152021_a": "03152021_mahler_a_g0/03152021_mahler_a_g0_imec0/",
        "03172021_a": "031720221_mahler_a_g0/031720221_mahler_a_g0_imec0/",
        "03182021_a": "031820221_mahler_a_g0/031820221_mahler_a_g0_imec0/",
        "03192021_a": "031920221_mahler_a_g0/031920221_mahler_a_g0_imec0/"
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
        #f"/om4/group/jazlab/sujay_backup/mtt_data_mahler/{SESSION_TO_ECEPHYS_DIR[subject][session]}/" #vprobe
        f"/om4/group/jazlab/sujay_backup/np_data/{SESSION_TO_ECEPHYS_DIR[subject][session]}/" #neuropixel
    )

    # Path to task and behavior data.
    behavior_path = f'/om4/group/jazlab/sujay_backup/nwb/physiology_data_for_sharing/7a/{subject}{session}.mwk'

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
