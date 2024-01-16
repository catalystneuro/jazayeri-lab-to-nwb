import mat73
from scipy.io import loadmat

def read_trials_data(session_paths):
    """"""
    """Read in behavioral data from Matlab files."""
    ttl_data = _read_ttl_data(session_paths)

    behavior_path = session_paths.behavior


    # Any tensor file will work here
    # TODO: Make this a function that finds file
    cond_matrix_path = behavior_path / 'amadeus08292019_a_neur_tensor_gocueon.mat'
    
    cond_mat = mat73.loadmat(
        cond_matrix_path, only_include=['cond_label', 'cond_matrix'])
    
    # Create dictionary of lists 
    trials = {}

    for label_ix, label in enumerate(cond_mat['cond_label']):
        trials[label] = cond_mat['cond_matrix'][:, label_ix]

    # trials.update(ttl_data)
    return trials
    
def _read_ttl_data(session_paths):
    # TODO: Read in TTL data and return dictionary of lists
    """Read in TTL data from Matlab files."""
    behavior_path = session_paths.behavior
    ttl_path = behavior_path / 'amadeus08292019_a.mat'
    ttl_mat = loadmat(ttl_path)
    ttl_dict = {}
    variable_names = ['ta', 'tp']
    for var in variable_names:
        ttl_dict[var] = ttl_mat[var].squeeze()
    return ttl_dict

def read_behavior_data(session_paths):
    """Read in non-trial-structured behavioral data from Matlab files."""
    # TODO: Read in non-trial-structured behavioral data (e.g. eye position,
    # reward line, eye position) from matlab files

