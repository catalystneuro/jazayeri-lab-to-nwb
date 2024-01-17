import mat73
import numpy as np
from scipy.io import loadmat

from get_session_paths import SessionPaths

def read_trials_data(session_paths: SessionPaths, 
                     subject: str, 
                     session: str):
    """Read in behavioral data from Matlab files."""

    behavior_path = session_paths.behavior

    # Any tensor file will work here
    # TODO: Make this a function that finds file
    cond_matrix_path = behavior_path / f'{subject}{session}_a_neur_tensor_gocueon.mat'
    
    cond_mat = mat73.loadmat(
        cond_matrix_path, only_include=['cond_label', 'cond_matrix'])
    
    # Create dictionary of lists 
    trials = {}

    for label_ix, label in enumerate(cond_mat['cond_label']):
        trials[label] = cond_mat['cond_matrix'][:, label_ix]

    ttl_data = _read_ttl_data(session_paths, subject=subject, session=session)
    trials.update(ttl_data)
    return trials
    
def _read_ttl_data(session_paths: SessionPaths, 
                   subject: str, 
                   session: str):
    # TODO: Read in TTL data and return dictionary of lists
    """Read in TTL data from Matlab files."""
    behavior_path = session_paths.behavior
    # TODO: replace hard-coded name with subject/session
    ttl_path = behavior_path / f'{subject}{session}_a.mat'
    ttl_mat = loadmat(ttl_path)
    ttl_dict = {}
    variable_names = ['gocuettl', 'joy1offttl', 'joy1onttl', 'stim1onttl',]
    for var in variable_names:
        ttl_dict[var] = ttl_mat[var].squeeze()
    return ttl_dict

def read_behavior_data(session_paths: SessionPaths, 
                       subject: str, 
                       session: str):
    """Read in non-trial-structured behavioral data from Matlab files."""

    behavior_path = session_paths.behavior
    behavior_dict = {}
    # TODO: replace hard-coded name with subject/session
    ttl_path = behavior_path / f'{subject}{session}_a.mat'
    ttl_mat = loadmat(ttl_path)
    
    eyet = ttl_mat['eyex_time']
    eyex = ttl_mat['eyex']
    eyey = ttl_mat['eyey']
    offset = ttl_mat['mworks_lead']
    mworks_start_time = ttl_mat['t0_mworks']
    eyet_aligned = eyet - mworks_start_time + offset
    behavior_dict['EyePosition'] = {}
    behavior_dict['EyePosition']['times'] = eyet_aligned
    behavior_dict['EyePosition']['values'] = np.stack([eyex, eyey], axis=1).reshape(2, -1)
    # TODO: Assert that length of times and values matches    


    joyt = ttl_mat['joy_time']
    joy = ttl_mat['joy']
    joyt_aligned = joyt - mworks_start_time + offset
    behavior_dict['HandPosition'] = {}
    behavior_dict['HandPosition']['times'] = np.array(joyt_aligned)
    behavior_dict['HandPosition']['values'] = np.array(joy)
    # TODO: Assert that length of times and values matches    
    return behavior_dict
    

def read_session_start_time(
        session_paths: SessionPaths,
        subject: str, 
        session: str):   
    behavior_path = session_paths.behavior
    # TODO: replace hard-coded name with subject/session
    ttl_path = behavior_path / 'amadeus08292019_a.mat'
    ttl_mat = loadmat(ttl_path)
    import pdb; pdb.set_trace()


