"""Primary classes for timeseries variables.

The classes here handle variables like eye position, reward line, and audio
stimuli that are not necessarily tied to the trial structure of display updates.
For trial structured variables, see ../trials_interface.py. For variables
pertaining to display updates, see ../frames_interface.py.
"""

import abc
import json
import numpy as np
from pathlib import Path
from pynwb import NWBFile, TimeSeries
from pynwb.behavior import SpatialSeries
from hdmf.backends.hdf5 import H5DataIO

from neuroconv.basetemporalalignmentinterface import BaseTemporalAlignmentInterface
from neuroconv.utils import DeepDict, FolderPathType, FilePathType
from neuroconv.tools.nwb_helpers import get_module


class TemporalAlignmentMixin(BaseTemporalAlignmentInterface):
    """Mixin implementing temporal alignment functions with timestamps."""
    
    def __init__(self, folder_path: FolderPathType):
        super().__init__(folder_path=folder_path)

    def set_original_timestamps(self, original_timestamps: np.ndarray) -> None:
        self._original_timestamps = original_timestamps
        self._timestamps = np.copy(original_timestamps)
    
    def get_original_timestamps(self) -> np.ndarray:
        return self._original_timestamps

    def set_aligned_timestamps(self, aligned_timestamps: np.ndarray) -> None:
        self._timestamps = aligned_timestamps
        
    def get_timestamps(self):
        return self._timestamps


class EyePositionInterface(TemporalAlignmentMixin):
    """Eye position interface."""

    def __init__(self, folder_path: FolderPathType):
        folder_path = Path(folder_path)
        super().__init__(folder_path=folder_path)
        
        # Find eye position files and check they all exist
        eye_h_file = folder_path / 'eye_h_calibrated.json'
        eye_v_file = folder_path / 'eye_v_calibrated.json'
        assert eye_h_file.exists(), f'Could not find {eye_h_file}'
        assert eye_v_file.exists(), f'Could not find {eye_v_file}'
        
        # Load eye data
        eye_h_data = json.load(open(eye_h_file, 'r'))
        eye_v_data = json.load(open(eye_v_file, 'r'))
        eye_h_times = np.array(eye_h_data['times'])
        eye_h_values = 0.5 + (np.array(eye_h_data['values']) / 20)
        eye_v_times = np.array(eye_v_data['times'])
        eye_v_values = 0.5 + (np.array(eye_v_data['values']) / 20)
        
        # Check eye_h and eye_v have the same number of samples
        if len(eye_h_times) != len(eye_v_times):
            raise ValueError(
                f'len(eye_h_times) = {len(eye_h_times)}, but len(eye_v_times) '
                f'= {len(eye_v_times)}'
            )
        # Check that eye_h_times and eye_v_times are similar to within 0.5ms
        if not np.allclose(eye_h_times, eye_v_times, atol=0.0005):
            raise ValueError(
                'eye_h_times and eye_v_times are not sufficiently similar'
            )
        
        # Set data attributes
        self.set_original_timestamps(eye_h_times)
        self._eye_pos = np.stack([eye_h_values, eye_v_values], axis=1)

    def add_to_nwbfile(self, nwbfile: NWBFile, metadata: dict):
        # Make SpatialSeries
        eye_position = SpatialSeries(
            name='eye_position',
            data=H5DataIO(self._eye_pos, compression='gzip'),
            reference_frame='(0,0) is bottom left corner of screen',
            unit='meters',
            conversion=0.257,
            timestamps=H5DataIO(self._timestamps, compression='gzip'),
            description='Eye position data recorded by EyeLink camera',
        )

        # Get processing module
        module_description = 'Contains behavioral data from experiment.'
        processing_module = get_module(
            nwbfile=nwbfile, name='behavior', description=module_description)

        # Add data to module
        processing_module.add_data_interface(eye_position)

        return nwbfile


class PupilSizeInterface(TemporalAlignmentMixin):
    """Pupil size interface."""

    def __init__(self, folder_path: FolderPathType):
        # Find pupil size file
        folder_path = Path(folder_path)
        pupil_size_file = folder_path / 'pupil_size_r.json'
        assert pupil_size_file.exists(), f'Could not find {pupil_size_file}'
        
        # Load pupil size data and set data attributes
        pupil_size_data = json.load(open(pupil_size_file, 'r'))
        self.set_original_timestamps(np.array(pupil_size_data['times']))
        self._pupil_size = np.array(pupil_size_data['values'])

    def add_to_nwbfile(self, nwbfile: NWBFile, metadata: dict):
        # Make SpatialSeries
        pupil_size = TimeSeries(
            name='pupil_size',
            data=H5DataIO(self._pupil_size, compression='gzip'),
            unit='pixels',
            conversion=1.0,
            timestamps=H5DataIO(self._timestamps, compression='gzip'),
            description='Pupil size data recorded by EyeLink camera',
        )

        # Get processing module
        module_description = 'Contains behavioral data from experiment.'
        processing_module = get_module(
            nwbfile=nwbfile, name='behavior', description=module_description)

        # Add data to module
        processing_module.add_data_interface(pupil_size)

        return nwbfile


class RewardLineInterface(TemporalAlignmentMixin):
    """Reward line interface."""

    def __init__(self, folder_path: FolderPathType):
        # Find reward line file
        folder_path = Path(folder_path)
        reward_line_file = folder_path / 'reward_line.json'
        assert reward_line_file.exists(), f'Could not find {reward_line_file}'
        
        # Load reward line data and set data attributes
        reward_line_data = json.load(open(reward_line_file, 'r'))
        self.set_original_timestamps(np.array(reward_line_data['times']))
        self._reward_line = np.array(reward_line_data['values'])

    def add_to_nwbfile(self, nwbfile: NWBFile, metadata: dict):
        # Make SpatialSeries
        reward_line = TimeSeries(
            name='reward_line',
            data=H5DataIO(self._reward_line, compression='gzip'),
            unit='reward line open',
            timestamps=H5DataIO(self._timestamps, compression='gzip'),
            description=(
                'Reward line data representing events of reward dispenser'
            ),
        )

        # Get processing module
        module_description = 'Contains audio and reward data from experiment.'
        processing_module = get_module(
            nwbfile=nwbfile, name='behavior', description=module_description)

        # Add data to module
        processing_module.add_data_interface(reward_line)

        return nwbfile


class AudioInterface(TemporalAlignmentMixin):
    """Audio interface."""

    def __init__(self, folder_path: FolderPathType):
        # Find sound file
        folder_path = Path(folder_path)
        sound_file = folder_path / 'sound.json'
        assert sound_file.exists(), f'Could not find {sound_file}'
        
        # Load sound data and set data attributes
        sound_data = json.load(open(sound_file, 'r'))
        self.set_original_timestamps(np.array(sound_data['times']))
        self._audio = np.array(sound_data['values'])

    def add_to_nwbfile(self, nwbfile: NWBFile, metadata: dict):
        # Make SpatialSeries
        audio = TimeSeries(
            name='audio',
            data=H5DataIO(self._audio, compression='gzip'),
            unit='audio filename',
            timestamps=H5DataIO(self._timestamps, compression='gzip'),
            description='Audio data representing auditory stimuli events',
        )

        # Get processing module
        module_description = 'Contains audio and reward data from experiment.'
        processing_module = get_module(
            nwbfile=nwbfile, name='behavior', description=module_description)

        # Add data to module
        processing_module.add_data_interface(audio)

        return nwbfile
