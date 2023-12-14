"""Function for getting paths to data on openmind."""

import collections
import pathlib

SUBJECT_NAME_TO_ID = {
    'Perle': 'monkey0',
    'Elgar': 'monkey1',
}

SessionPaths = collections.namedtuple(
    'SessionPaths',
    [
        'output',
        'raw_data',
        'data_open_source',
        'sync_pulses',
        'spike_sorting_raw',
    ],
)


def get_session_paths(subject, session, stub_test=False):
    """Get paths to all components of the data.
    
    Returns:
        SessionPaths namedtuple.
    """
    subject_id = SUBJECT_NAME_TO_ID[subject]
    
    # Path to write output nwb files to
    output_path = (
        f'/om/user/nwatters/nwb_data_multi_prediction/{subject}/{session}'
    )
    if stub_test:
        output_path = f'{output_path}/stub'
    
    # Path to the raw data. This is used for reading raw physiology data.
    raw_data_path = (
        f'/om4/group/jazlab/nwatters/multi_prediction/phys_data/{subject}/'
        f'{session}/raw_data'
    )
    
    # Path to open-source data. This is used for reading behavior and task data.
    data_open_source_path = (
        '/om4/group/jazlab/nwatters/multi_prediction/datasets/data_open_source/'
        f'Subjects/{subject_id}/{session}/001'
    )
    
    # Path to sync pulses. This is used for reading timescale transformations
    # between physiology and mworks data streams.
    sync_pulses_path = (
        '/om4/group/jazlab/nwatters/multi_prediction/data_processed/'
        f'{subject}/{session}/sync_pulses'
    )
    
    # Path to spike sorting. This is used for reading spike sorted data.
    spike_sorting_raw_path = (
        f'/om4/group/jazlab/nwatters/multi_prediction/phys_data/{subject}/'
        f'{session}/spike_sorting'
    )
    
    session_paths = SessionPaths(
        output=pathlib.Path(output_path),
        raw_data=pathlib.Path(raw_data_path),
        data_open_source=pathlib.Path(data_open_source_path),
        sync_pulses=pathlib.Path(sync_pulses_path),
        spike_sorting_raw=pathlib.Path(spike_sorting_raw_path),
    )
    
    return session_paths
