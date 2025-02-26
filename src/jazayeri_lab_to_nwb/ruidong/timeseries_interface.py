"""Primary classes for timeseries variables.

The classes here handle variables like eye position, reward line, and audio
stimuli that are not necessarily tied to the trial structure of display updates.
For trial structured variables, see ../trials_interface.py. For variables
pertaining to display updates, see ../frames_interface.py.
"""

import json
from pathlib import Path

import numpy as np
from hdmf.backends.hdf5 import H5DataIO
from ndx_events import LabeledEvents
from neuroconv.basetemporalalignmentinterface import (
    BaseTemporalAlignmentInterface,
)
from neuroconv.tools.nwb_helpers import get_module
from neuroconv.utils import FolderPathType
from pynwb import NWBFile, TimeSeries
from pynwb.behavior import SpatialSeries


class TimestampsFromArrayInterface(BaseTemporalAlignmentInterface):
    """Interface implementing temporal alignment functions with timestamps."""

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


class EyePositionInterface(TimestampsFromArrayInterface):
    """Eye position interface."""

    def __init__(self, folder_path: FolderPathType):
        folder_path = Path(folder_path)
        super().__init__(folder_path=folder_path)
        # Find eye position files and check they all exist
        eye_h_file = folder_path / "eyex_v.npy"
        eye_v_file = folder_path / "eyey_v.npy"
        eye_xt_file = folder_path / "eyex_t.npy"
        eye_yt_file = folder_path / "eyey_t.npy"
        assert eye_h_file.exists(), f"Could not find {eye_h_file}"
        assert eye_v_file.exists(), f"Could not find {eye_v_file}"

        # Load eye data
        eye_h_data = np.load(eye_h_file)
        eye_v_data = np.load(eye_v_file)
        eye_h_times = np.load(eye_xt_file)
        eye_h_values = 0.5 + (eye_h_data / 40)
        eye_v_times = np.load(eye_yt_file)
        eye_v_values = 0.5 + (eye_v_data / 40)

        # Check eye_h and eye_v have the same number of samples
        if len(eye_h_times) != len(eye_v_times):
            raise ValueError(
                f"len(eye_h_times) = {len(eye_h_times)}, but len(eye_v_times) "
                f"= {len(eye_v_times)}"
            )
        # Check that eye_h_times and eye_v_times are similar to within 0.5ms
        if not np.allclose(eye_h_times, eye_v_times, atol=0.0005):
            raise ValueError(
                "eye_h_times and eye_v_times are not sufficiently similar"
            )

        # Set data attributes
        self.set_original_timestamps(eye_h_times)
        self._eye_pos = np.stack([eye_h_values, eye_v_values], axis=1)

    def add_to_nwbfile(self, nwbfile: NWBFile, metadata: dict):
        del metadata

        # Make SpatialSeries
        eye_position = SpatialSeries(
            name="eye_position",
            data=H5DataIO(self._eye_pos, compression="gzip"),
            reference_frame="(0,0) is bottom left corner of screen",
            unit="meters",
            conversion=0.257,
            timestamps=H5DataIO(self._timestamps, compression="gzip"),
            description="Eye position data recorded by EyeLink camera",
        )

        # Get processing module
        module_description = "Contains behavior from experiment."
        processing_module = get_module(
            nwbfile=nwbfile, name="behavior", description=module_description
        )

        # Add data to module
        processing_module.add_data_interface(eye_position)

        return nwbfile


class JoystickInterface(TimestampsFromArrayInterface):
    """Eye position interface."""

    def __init__(self, folder_path: FolderPathType, id: int):
        folder_path = Path(folder_path)
        super().__init__(folder_path=folder_path)
        # Find joystick position files and check they all exist
        joystick_h_file = folder_path / f"joyx{id}_v.npy"
        joystick_xt_file = folder_path / f"joyx{id}_t.npy"
        assert joystick_h_file.exists(), f"Could not find {joystick_h_file}"

        # Load joystick data
        joystick_h_data = np.load(joystick_h_file)
        joystick_h_times = np.load(joystick_xt_file)
        joystick_h_values = joystick_h_data

        # Set data attributes
        self.set_original_timestamps(joystick_h_times)
        self._joystick_pos = joystick_h_values

    def add_to_nwbfile(self, nwbfile: NWBFile, metadata: dict):
        del metadata

        # Make SpatialSeries
        joystick_position = SpatialSeries(
            name="joystick_position",
            data=H5DataIO(self._joystick_pos, compression="gzip"),
            reference_frame="(0) is neutral",
            unit="level",
            timestamps=H5DataIO(self._timestamps, compression="gzip"),
            description="joystick position data recorded by joystick",
        )

        # Get processing module
        module_description = "Contains behavior from experiment."
        processing_module = get_module(
            nwbfile=nwbfile, name="behavior", description=module_description
        )

        # Add data to module
        processing_module.add_data_interface(joystick_position)

        return nwbfile
