"""Function for getting paths to data on openmind."""

import collections
import pathlib
import pandas as pd

# TODO: If you want subject names to be different, change this.
SUBJECT_NAME_TO_ID = {
    "Offenbach": "monkey0",
    "Lalo": "monkey1",
}


def load_subject_names():
    subject_names_path = "/Volumes/Transfer/nwb_test/data/subject_names.csv"
    return pd.read_csv(subject_names_path)


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


def get_probe_id(subject, session):
    if subject == "Offenbach":
        subject = "O"
    elif subject == "Lalo":
        subject = "L"
    subject_names = load_subject_names()
    # make sure session is a number
    session = int(session)
    # find the v_probe for this subject on this session
    session_df = subject_names[subject_names["date"] == session]
    # check if subject is in column 'subject1' or 'subject2'
    if subject in session_df["subject1"].values:
        probe_id = "v_probe_1"
    elif subject in session_df["subject2"].values:
        probe_id = "v_probe_2"
    else:
        raise ValueError(f"Subject {subject} not found in session {session}")
    return probe_id


def _get_session_paths_local(subject, session):
    """Get paths to all components of the data on local machine."""
    probe_id = get_probe_id(subject, session)

    output_path = "/Volumes/Transfer/output"
    root = "/Volumes/Transfer/nwb_test/data/social_O_L/"
    # does this need to be a file? my behavior source data is a directory, each trial is a file in a subdirectory.
    behavior_path = f"{root}/{session}/results/moog_events/"

    # Read start time from settings.xml (OpenEphys start acquisition time)
    start_time_path = f"{root}/{session}/phys_raw/OpenEphys/settings.xml"

    binned_data_type = "cache_fdbk_-3_3"
    phys_path = f"{root}/{session}/results/{probe_id}/{binned_data_type}.json"

    # this is the raw data from open_ephys (converted to dat format)
    dat_path = f"{root}/{session}/results/{probe_id}/data.dat"

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
