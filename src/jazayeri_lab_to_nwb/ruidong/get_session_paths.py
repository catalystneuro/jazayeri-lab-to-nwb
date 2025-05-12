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
    # if path does not exist, use openmind path
    if not pathlib.Path(subject_names_path).exists():
        subject_names_path = "/om2/user/ruidong/data/data_srl/subject_names.csv"
    return pd.read_csv(subject_names_path)


SessionPaths = collections.namedtuple(
    "SessionPaths",
    [
        "behavior",
        "eye_path",
        "joystick_path",
        "ece_path",
        "phys",
        "output",
        "start_time",
        "ks_path",
    ],
)


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


def get_session_paths(subject, session):
    """Get paths to all components of the data on local machine."""
    probe_id = get_probe_id(subject, session)

    output_path = "/Volumes/Transfer/output"
    root = "/Volumes/Transfer/nwb_test/data/social_O_L/"
    if not pathlib.Path(output_path).exists():
        output_path = "/om2/user/ruidong/data/nwb"
        root = "/om2/user/ruidong/data/data_srl/social_O_L"
    # does this need to be a file? my behavior source data is a directory, each trial is a file in a subdirectory.
    behavior_path = f"{root}/{session}/results/moog_events/"

    # Read start time from settings.xml (OpenEphys start acquisition time)
    start_time_path = f"{root}/{session}/phys_raw/OpenEphys/settings.xml"

    binned_data_type = "cache_fdbk_-3_3"
    phys_path = (
        f"{root}/{session}/results/{probe_id}/spikes/{binned_data_type}.json"
    )

    # this is the raw data from open_ephys (converted to dat format)
    dat_path = f"{root}/{session}/results/{probe_id}/data.dat"

    # this is the sorted spikes from kilosort
    kilosort_path = f"{root}/{session}/results/{probe_id}/ks_output"

    # eye path
    if subject == "Offenbach":
        eye_path = f"{root}/{session}/results/mworks_events"
    elif subject == "Lalo":
        eye_path = f"{root}/{session}/results/mworks_events_2nd_eyelink"

    # joystick path
    joystick_path = f"{root}/{session}/results/mworks_events"

    session_paths = SessionPaths(
        output=pathlib.Path(output_path),
        behavior=pathlib.Path(behavior_path),
        eye_path=pathlib.Path(eye_path),
        joystick_path=pathlib.Path(joystick_path),
        ece_path=pathlib.Path(dat_path),
        phys=pathlib.Path(phys_path),
        start_time=pathlib.Path(start_time_path),
        ks_path=pathlib.Path(kilosort_path),
    )

    return session_paths
