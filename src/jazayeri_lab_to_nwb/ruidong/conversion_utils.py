import numpy as np
import pandas as pd
import json
import pathlib
from get_session_paths import get_probe_id
from ndx_binned_spikes import BinnedAlignedSpikes
import re
from datetime import datetime, timezone, timedelta


def from_json(d):
    if isinstance(d, dict) and d.get("type") == "ndarray":
        return np.array(d["value"])
    return d


def read_binned_data(
    subject_id: str,
    session_id: str,
    name: str,
):
    # Read data from file
    event = name
    probe_id = get_probe_id(subject_id, session_id)
    root = "/Volumes/Transfer/nwb_test/data/social_O_L/"
    if not pathlib.Path(output_path).exists():
        output_path = "/om2/user/ruidong/data/nwb"
        root = "/om2/user/ruidong/data/data_srl/social_O_L"
    path_neural = (
        f"{root}/{session_id}/results/{probe_id}/spikes/cache_{event}_-3_3.json"
    )
    print("loading neural data")
    with open(path_neural, "r") as f:
        dataT = json.load(f, object_hook=from_json)
    print("loading behavioral data")
    path_behav = f"{root}/{session_id}/results/moog_events/trial_info.csv"
    df_bhv = pd.read_csv(path_behav)

    # Reorganize neural data into 3D array # Nun x Ntrial x Ntime
    reorganized_data = reorganize_neural_data(dataT, df_bhv)

    # Specify event timestamps
    event_timestamps = dataT["timepoints"]
    bin_width_in_milliseconds = 100.0
    binned_aligned_spikes = BinnedAlignedSpikes(
        data=reorganized_data,
        event_timestamps=event_timestamps,
        bin_width_in_milliseconds=bin_width_in_milliseconds,
        milliseconds_from_event_to_first_bin=-3000.0,
        name=name,
    )
    return binned_aligned_spikes


def reorganize_neural_data(dataT, df_bhv):
    # Extract the dimensions of the data
    maximum_number_of_timepoints = np.shape(dataT["unit"][0]["response"])[
        1
    ]  # Number of columns in the neural data (e.g., 16552)
    number_of_trials = len(df_bhv)  # Number of unique trials
    number_of_neurons = len(dataT["unit"])  # Number of unique neurons

    # Create a 3D array filled with NaN values
    reorganized_data = np.full(
        (number_of_trials, maximum_number_of_timepoints, number_of_neurons),
        np.nan,
    )

    # Loop through each unit and place the firing rates into the 3D array
    for i in range(number_of_neurons):
        unit = dataT["unit"][i]
        # Extract the trial indices for this unit
        trial_ids = unit["task_variable"]["trial_num"]
        responses = unit["response"]

        # Fill the array for this trial and neuron
        for i_resp, trial in enumerate(trial_ids):
            i_trial = df_bhv[df_bhv["trial_num"] == trial].index[0]
            reorganized_data[i_trial, :, i] = responses[i_resp, :]

    return reorganized_data


def read_trials_data(session_id: str):
    trials = {}
    root = "/Volumes/Transfer/nwb_test/data/social_O_L/"
    if not pathlib.Path(output_path).exists():
        output_path = "/om2/user/ruidong/data/nwb"
        root = "/om2/user/ruidong/data/data_srl/social_O_L"
    path_behav = f"{root}/{session_id}/results/moog_events/trial_info.csv"
    # load behavior data
    df_bhv = pd.read_csv(path_behav)

    # List of fields you want to loop through and store in the trials dictionary
    fields_to_extract = [
        "trial_num",
        "choice_a0",
        "choice_a1",
        "player",
        "reward",
        "touched_polls",
        "difficulty",
        "better_choice",
        "history",
        "pos_in_block",
        "pos_in_block_obj",
        "attention_full",
        "attention_full_L",
        "n_pre_switch_actor",
    ]  # Add other fields as needed

    # initialize trials
    for field in fields_to_extract:
        trials[field] = df_bhv[field].tolist()

    # Add the trial start times
    trials["start_time"] = df_bhv["trial_start_time"].tolist()

    return trials


def convert_timestamp(raw_timestamp, tz_offset="-05:00"):
    """
    Converts a raw timestamp string in the format YYYY-MM-DD_HH-MM-SS into an ISO8601 extended format,
    assuming the provided timezone offset. By default, tz_offset is set to "-05:00" (EST).

    Args:
        raw_timestamp (str): The timestamp string, e.g. "2023-02-09_13-41-15".
        tz_offset (str): The timezone offset as a string. Default is "-05:00" for EST.

    Returns:
        str: The ISO8601 formatted timestamp with millisecond precision.
    """
    # Parse the raw timestamp
    dt = datetime.strptime(raw_timestamp, "%Y-%m-%d_%H-%M-%S")
    dt = dt.replace(microsecond=0)

    if tz_offset is None:
        # If no offset is provided, assume UTC.
        dt = dt.replace(tzinfo=timezone.utc)
        iso_str = dt.isoformat(timespec="milliseconds").replace("+00:00", "Z")
    else:
        # Parse the timezone offset (e.g., "-05:00" for EST)
        sign = 1 if tz_offset[0] == "+" else -1
        hours = int(tz_offset[1:3])
        minutes = int(tz_offset[4:6])
        offset = timezone(timedelta(hours=sign * hours, minutes=sign * minutes))
        dt = dt.replace(tzinfo=offset)
        iso_str = dt.isoformat(timespec="milliseconds")

    return iso_str


# Need to update
def read_session_start_time(path: str):

    with open(path, "r") as file:
        file_contents = file.readlines()

    # Initialize a variable to store acquisition start time
    raw_timestamp = None

    # Loop through each line to find 'MAIN state'
    # The line will look like     <MAIN state="1" value="2023-02-09_13-41-15"/>
    # We want to extract 2023-02-09_13-41-15 as a time stamp
    # Date and time of the experiment/session start. The date is stored in UTC with local timezone offset as ISO 8601 extended formatted string: 2018-09-28T14:43:54.123+02:00. Dates stored in UTC end in “Z” with no timezone offset. Date accuracy is up to milliseconds.
    for line in file_contents:
        if "MAIN state" in line:
            # Expected line example:
            # <MAIN state="1" value="2023-02-09_13-41-15"/>
            match = re.search(r'value="([^"]+)"', line)
            if match:
                raw_timestamp = match.group(1)
            break
    if raw_timestamp:
        # Convert the raw timestamp, assuming EST (UTC-5)
        iso_timestamp = convert_timestamp(raw_timestamp, tz_offset="-05:00")
        print(f"Session start time: {iso_timestamp}")
        return iso_timestamp
    else:
        raise ValueError("Session start time not found in the provided file.")
