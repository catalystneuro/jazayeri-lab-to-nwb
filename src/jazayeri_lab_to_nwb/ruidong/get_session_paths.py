"""Function for getting paths to data on openmind."""

import collections
import pathlib

# TODO: If you want subject names to be different, change this.
SUBJECT_NAME_TO_ID = {
    "Offenbach": "monkey0",
    "Lalo": "monkey1",
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

    output_path = "./output"
    # does this need to be a file? my behavior source data is a directory, each trial is a file in a subdirectory.
    behavior_path = f"/om2/user/ruidong/data/social_O_L/{session}/behavior/"

    start_time_data_type = "_t0.imec0.lf.meta"
    start_time_path = f"/om4/group/jazlab/Mahdi/Neurophys/Sorting/Data_KS/Offenbach/NP/{session}/{session}_imec0/{session}{start_time_data_type}"

    binned_data_type = "_whole_trial_FR"
    phys_path = f"/om2/user/ruidong/Neurophys/Sorting/Analysis/NP/{subject}/Firing_Rates/{session}{binned_data_type}.mat"

    session_paths = SessionPaths(
        output=pathlib.Path(output_path),
        behavior=pathlib.Path(behavior_path),
        phys=pathlib.Path(phys_path),
        start_time=pathlib.Path(start_time_path),
    )

    return session_paths


def _get_session_paths_local(subject, session):
    """Get paths to all components of the data on local machine."""

    output_path = "./output"
    root = "/Volumes/Transfer/nwb/data/social_O_L/"
    # does this need to be a file? my behavior source data is a directory, each trial is a file in a subdirectory.
    behavior_path = f"{root}/{session}/results/moog_events/"

    # I don't have this file, what is it?
    start_time_path = f"{root}/{session}/results/{session}"

    binned_data_type = "_whole_trial_FR"
    phys_path = f"{root}/{session}/results/{session}{binned_data_type}.mat"

    session_paths = SessionPaths(
        output=pathlib.Path(output_path),
        behavior=pathlib.Path(behavior_path),
        phys=pathlib.Path(phys_path),
        start_time=pathlib.Path(start_time_path),
    )

    return session_paths


def get_session_paths(subject, session, repo="openmind"):
    """Get paths to all components of the data.

    Returns:
        SessionPaths namedtuple.
    """
    if repo == "openmind":
        return _get_session_paths_openmind(subject=subject, session=session)
    elif repo == "local":
        return _get_session_paths_local(subject=subject, session=session)
