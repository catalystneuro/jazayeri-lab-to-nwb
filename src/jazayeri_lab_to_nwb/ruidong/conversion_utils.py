import numpy as np
from ndx_binned_spikes import BinnedAlignedSpikes
import mat73
from scipy.io import loadmat

def read_binned_data(
        path_neural: str,
        path_beh: str,
        ):
    
    print('loading neural data')
    # Read neural data
    neural_data = mat73.loadmat(
        path_neural, only_include=['smooth_session'])
    # Read behavior data
    print('loading behavioral data')
    data = mat73.loadmat(path_beh)
    # Extract the 'save_all_data' field from the loaded data
    save_all_data = data['save_all_data']

     # Extract 'nrns_all' and 'trial_indices_all'
    nrns_all = save_all_data['nrns']  # Neuron identifiers
    trial_indices_all = save_all_data['trial_indices_all']  # Trial identifiers

    # Reorganize neural data into 3D array
    reorganized_data = reorganize_neural_data(neural_data, nrns_all, trial_indices_all)

    # TODO: Specify event timestamps
    event_timestamps = np.linspace(1, int(np.shape(reorganized_data)[1]),int(np.shape(reorganized_data)[1])) # The timestamps to which we align the counts
    milliseconds_from_event_to_first_bin = 0.0  
    bin_width_in_milliseconds = 1.0
    binned_aligned_spikes = BinnedAlignedSpikes(
        data=reorganized_data,
        event_timestamps=event_timestamps,
        bin_width_in_milliseconds=bin_width_in_milliseconds,
        milliseconds_from_event_to_first_bin=milliseconds_from_event_to_first_bin
    )
    return binned_aligned_spikes

def reorganize_neural_data(neural_data, nrns_all, trial_indices_all):
    # Extract the dimensions of the data
    maximum_number_of_timepoints = np.shape(neural_data['smooth_session'])[1]  # Number of columns in the neural data (e.g., 16552)
    number_of_trials = len(np.unique(trial_indices_all))  # Number of unique trials
    number_of_neurons = len(np.unique(nrns_all))  # Number of unique neurons

    # Create a 3D array filled with NaN values
    reorganized_data = np.full((number_of_trials, maximum_number_of_timepoints, number_of_neurons), np.nan)

    # Create mappings for trial indices and neuron indices
    trial_id_to_index = {trial_id: idx for idx, trial_id in enumerate(np.unique(trial_indices_all))}
    neuron_id_to_index = {neuron_id: idx for idx, neuron_id in enumerate(np.unique(nrns_all))}

    # Loop through each row of the neural data and place the firing rates into the 3D array
    for i in range(np.shape(neural_data['smooth_session'])[0]):
        neuron_id = nrns_all[i]
        trial_id = trial_indices_all[i]

        # Get the corresponding indices in the 3D array
        trial_idx = trial_id_to_index[trial_id]
        neuron_idx = neuron_id_to_index[neuron_id]

        # Fill the array for this trial and neuron
        reorganized_data[trial_idx, :, neuron_idx] = neural_data['smooth_session'][i]

    return reorganized_data


def read_trials_data(
    path: str
):
    trials = {}
    # load behavior data
    data = mat73.loadmat(path)

    # Extract the 'save_all_data' field from the loaded data
    save_all_data = data['save_all_data']

    # List of fields you want to loop through and store in the trials dictionary
    fields_to_extract = ['h1', 'h2', 'h3', 'h4', 'h5', 'h6' , 'vel', 'LR',
                         'LR2', 'trial_answer1', 'trial_answer2', 'trial_answer3',
                         'trial_answer4', 'geo_present', 'fixation_cue_present',
                         'fix_start', 'flash_one', 'flash_two', 'flash_three',
                         'fixation_off', 'saccade_init', 'answer_time', 'trial_end',
                         'geo_type', 'path_type', 'rand_geo', 'trial_fade', 
                         'trial_indices_all']  # Add other fields as needed
    
    # initialize trials
    for field in fields_to_extract:
        trials[field] = []

    # nrns_all = save_all_data['nrns']
    # Extract 'nrns_all' and 'trial_indices_all' for neuron and trial identification
    trial_indices_all = save_all_data['trial_indices_all']

    # Get the unique trial identifiers
    unique_trials = np.unique(trial_indices_all)

    # Loop over each unique trial
    for trial_id in unique_trials:
        # Find indices where the trial matches the current trial_id
        trial_mask = (trial_indices_all == trial_id)

        # Loop through each field you want to extract
        for field in fields_to_extract:
            # Get the array corresponding to the field
            field_data = save_all_data[field]

            if field == 'nrns':
                # Special case: We will handle 'nrns' field later with binary matrix conversion
                continue
            else:
                # For other fields, store the unique value for the trial
                unique_values = np.unique(field_data[trial_mask])
                    
                if len(unique_values) > 1:
                    raise ValueError(f"Multiple unique values of '{field}' found for trial {trial_id}.")
                
                # Store the unique value of the field for this trial
                trials[field].append(unique_values[0])

    trials['start_time'] = trials['geo_present']

    return trials

# Need to update
def read_session_start_time(
        path: str):
    
    with open(path, 'r') as file:
        file_contents = file.readlines()

    # Initialize a variable to store fileCreateTime
    file_create_time = None

   # Loop through each line to find 'fileCreateTime'
    for line in file_contents:
        if "fileCreateTime" in line:
            # Split the line by '=' and extract the timestamp
            file_create_time = line.strip().split('=')[1]
            break
    return file_create_time