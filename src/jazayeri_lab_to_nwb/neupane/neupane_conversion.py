import mat73

def read_trials_data(session_paths):
    """Read in behavioral data from Matlab files."""
    behavior_path = session_paths.behavior

    # Any tensor file will work here
    cond_matrix_path = behavior_path / 'amadeus08292019_a_neur_tensor_gocueon.mat'
    
    cond_mat = mat73.loadmat(
        cond_matrix_path, only_include=['cond_label', 'cond_matrix'])

    # Create dictionary of lists 
    trials = {}
    for label_ix, label in enumerate(cond_mat['cond_label']):
        trials[label] = cond_mat['cond_matrix'][:, label_ix]

    ttl_data = _read_ttl_data(session_paths)
    trials.update(ttl_data)
    return trials
    
def _read_ttl_data(session_paths):
    # TODO: Read in TTL data and return dictionary of lists
    """Read in TTL data from Matlab files."""
    behavior_path = session_paths.behavior
    cond_matrix_path = behavior_path / 'amadeus08292019_a_neur_tensor_gocueon.mat'

    import pdb; pdb.set_trace()

def read_behavior_data(session_paths):
    """Read in non-trial-structured behavioral data from Matlab files."""
    # TODO: Read in non-trial-structured behavioral data (e.g. eye position,
    # reward line, eye position) from matlab files

