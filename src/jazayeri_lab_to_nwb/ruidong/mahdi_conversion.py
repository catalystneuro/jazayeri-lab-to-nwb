import numpy as np
import pandas as pd
import json
from get_session_paths import get_probe_id
from ndx_binned_spikes import BinnedAlignedSpikes


def from_json(d):
    if isinstance(d, dict) and d.get("type") == "ndarray":
        return np.array(d["value"])
    return d


def read_binned_data(
    subject_id: str,
    session_id: int,
    event: str,
):
    # Read data from file
    probe_id = get_probe_id(subject_id, session_id)
    path_neural = f"/Volumes/Transfer/nwb_test/data/social_O_L/{session_id}/results/{probe_id}/spikes/cache_{event}_-3_3.json"
    print("loading neural data")
    with open(path_neural, "r") as f:
        dataT = json.load(f, object_hook=from_json)
    print("loading behavioral data")
    path_behav = f"/Volumes/Transfer/nwb_test/data/social_O_L/{session_id}/results/moog_events/trial_info.csv"
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

def read_trials_data(session_id: int):
    trials = {}

    path_behav = f"/Volumes/Transfer/nwb_test/data/social_O_L/{session_id}/results/moog_events/trial_info.csv"
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

    return trials


if __name__ == "__main__":

    subject_id = "Offenbach"
    session_id = 20230209
    read_trials_data(session_id=session_id)
    read_binned_data(
        subject_id=subject_id,
        session_id=session_id,
        event="fdbk",
    )
