"""Class for converting trial-structured data."""

import json
import warnings
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd
from neuroconv.datainterfaces.text.timeintervalsinterface import TimeIntervalsInterface
from neuroconv.utils import DeepDict, FilePathType, FolderPathType
from pynwb import NWBFile


class TrialsInterface(TimeIntervalsInterface):
    """Class for converting trial-structured data.
    
    All events that occur exactly once per trial are contained in this
    interface.
    """
    
    KEY_MAP = {
        'background_indices': 'background_indices',
        'broke_fixation': 'broke_fixation',
        'stimulus_object_identities': 'stimulus_object_identities',
        'stimulus_object_positions': 'stimulus_object_positions',
        'stimulus_object_velocities': 'stimulus_object_velocities',
        'stimulus_object_target': 'stimulus_object_target',
        'delay_object_blanks': 'delay_object_blanks',
        'closed_loop_response_position': 'closed_loop_response_position',
        'closed_loop_response_time': 'closed_loop_response_time',
        'time_start': 'start_time',
        'time_phase_fixation': 'phase_fixation_time',
        'time_phase_stimulus': 'phase_stimulus_time',
        'time_phase_delay': 'phase_delay_time',
        'time_phase_cue': 'phase_cue_time',
        'time_phase_response': 'phase_response_time',
        'time_phase_reveal': 'phase_reveal_time',
        'time_phase_iti': 'phase_iti_time',
        'reward_time': 'reward_time',
        'reward_duration': 'reward_duration',
        'response_position': 'response_position',
        'response_time': 'response_time',
    }

    def __init__(self, folder_path: FolderPathType, verbose: bool = True):
        super().__init__(file_path=folder_path, verbose=verbose)

    def get_metadata(self) -> dict:
        metadata = super().get_metadata()
        metadata['TimeIntervals'] = dict(
            trials=dict(
                table_name='trials',
                table_description='data about each trial',
            )
        )
        return metadata
    
    def get_timestamps(self) -> np.ndarray:
        return super(TrialsInterface, self).get_timestamps(column='start_time')
    
    def set_aligned_starting_time(self, aligned_starting_time: float) -> None:
        self.dataframe.closed_loop_response_time += aligned_starting_time
        self.dataframe.start_time += aligned_starting_time
        self.dataframe.phase_fixation_time += aligned_starting_time
        self.dataframe.phase_stimulus_time += aligned_starting_time
        self.dataframe.phase_delay_time += aligned_starting_time
        self.dataframe.phase_cue_time += aligned_starting_time
        self.dataframe.phase_response_time += aligned_starting_time
        self.dataframe.phase_reveal_time += aligned_starting_time
        self.dataframe.phase_iti_time += aligned_starting_time
        self.dataframe.reward_time += aligned_starting_time
        self.dataframe.response_time += aligned_starting_time
        
    def _read_file(self, file_path: FolderPathType):
        # Create dataframe with data for each trial
        trials = json.load(open(Path(file_path) / 'trials.json', 'r'))
        trials = {
            k_mapped: [d[k] for d in trials]
            for k, k_mapped in TrialsInterface.KEY_MAP.items()
        }
        
        # Field closed_loop_response_position may have None values, so replace
        # those with NaN to make hdf5 conversion work
        trials['closed_loop_response_position'] = [
            [np.nan, np.nan] if x is None else x
            for x in trials['closed_loop_response_position']
        ]
        
        # Serialize fields with variable-length lists for hdf5 conversion
        for k in [
                'stimulus_object_identities',
                'stimulus_object_positions',
                'stimulus_object_velocities',
                'stimulus_object_target',
            ]:
            trials[k] = [json.dumps(x) for x in trials[k]]
        
        return pd.DataFrame(trials)

    def add_to_nwbfile(self,
                       nwbfile: NWBFile,
                       metadata: Optional[dict] = None,
                       tag: str = 'trials'):
        return super(TrialsInterface, self).add_to_nwbfile(
            nwbfile=nwbfile,
            metadata=metadata,
            tag=tag,
            column_descriptions=self.column_descriptions,
        )
    
    @property
    def column_descriptions(self):
        column_descriptions = {
            'background_indices': (
                'For each trial, the indices of the background noise pattern '
                'patch.'
            ),
            'broke_fixation': (
                'For each trial, whether the subject broke fixation and the '
                'trial was aborted'
            ),
            'stimulus_object_identities': (
                'For each trial, a serialized list with one element for each '
                'object. Each element is the identity symbol (e.g. "a", "b", '
                '"c", ...) of the corresponding object.'
            ),
            'stimulus_object_positions': (
                'For each trial, a serialized list with one element for each '
                'object. Each element is the initial (x, y) position of the '
                'corresponding object, in coordinates of arena width.'
            ),
            'stimulus_object_velocities': (
                'For each trial, a serialized list with one element for each '
                'object. Each element is the initial (dx/dt, dy/dt) velocity '
                'of the corresponding object, in units of arena width per '
                'display update.'
            ),
            'stimulus_object_target': (
                'For each trial, a serialized list with one element for each '
                'object. Each element is a boolean indicating whether the '
                'corresponding object is ultimately the cued target.'
            ),
            'delay_object_blanks': (
                'For each trial, a boolean indicating whether the objects were '
                'rendered as blank discs during the delay phase.'
            ),
            'closed_loop_response_position': (
                'For each trial, the position of the response saccade used by '
                'the closed-loop game engine. This is used for determining '
                'reward.'
            ),
            'closed_loop_response_time': (
                'For each trial, the time of the response saccade used by '
                'the closed-loop game engine. This is used for the timing of '
                'reward delivery.'
            ),
            'start_time': 'Start time of each trial.',
            'phase_fixation_time': (
                'Time of fixation phase onset for each trial.'
            ),
            'phase_stimulus_time': (
                'Time of stimulus phase onset for each trial.'
            ),
            'phase_delay_time': 'Time of delay phase onset for each trial.',
            'phase_cue_time': 'Time of cue phase onset for each trial.',
            'phase_response_time': (
                'Time of response phase onset for each trial.'
            ),
            'phase_reveal_time': 'Time of reveal phase onset for each trial.',
            'phase_iti_time': (
                'Time of inter-trial interval onset for each trial.'
            ),
            'reward_time': 'Time of reward delivery onset for each trial.',
            'reward_duration': 'Reward duration for each trial',
            'response_position': (
                'Response position for each trial. This differs from '
                'closed_loop_response_position in that this is calculated '
                'post-hoc from high-resolution eye tracking data, hence is '
                'more accurate.'
            ),
            'response_time': (
                'Response time for each trial. This differs from '
                'closed_loop_response_time in that this is calculated post-hoc '
                'from high-resolution eye tracking data, hence is more '
                'accurate.'
            ),
        }
        
        return column_descriptions
