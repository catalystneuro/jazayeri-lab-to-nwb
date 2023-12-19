"""Primary classes for converting experiment-specific behavior."""
from pathlib import Path

import numpy as np
from hdmf.backends.hdf5 import H5DataIO
from neuroconv.basetemporalalignmentinterface import BaseTemporalAlignmentInterface
from neuroconv.tools.nwb_helpers import get_module
from neuroconv.utils import DeepDict, FilePathType, FolderPathType
from pynwb import NWBFile, TimeSeries
from pynwb.behavior import SpatialSeries


class NumpyTemporalAlignmentMixin:
    """Mixin that implements temporal alignment functions with .npy timestamps"""

    timestamp_file_path: FilePathType
    timestamps: np.ndarray

    def get_original_timestamps(self) -> np.ndarray:
        return np.load(self.timestamp_file_path)

    def get_timestamps(self) -> np.ndarray:
        return self.timestamps

    def set_aligned_timestamps(self, aligned_timestamps: np.ndarray) -> None:
        self.timestamps = aligned_timestamps


class WattersEyePositionInterface(NumpyTemporalAlignmentMixin, BaseTemporalAlignmentInterface):
    """Eye position interface for Watters conversion"""

    def __init__(self, folder_path: FolderPathType):
        # initialize interface
        super().__init__(folder_path=folder_path)

        # find eye position files and check they all exist
        folder_path = Path(folder_path)
        eye_h_file = folder_path / "eye.h.values.npy"
        eye_h_times_file = folder_path / "eye.h.times.npy"
        eye_v_file = folder_path / "eye.v.values.npy"
        eye_v_times_file = folder_path / "eye.v.times.npy"
        for file_path in [eye_h_file, eye_h_times_file, eye_v_file, eye_v_times_file]:
            assert file_path.exists(), f"Could not find {file_path}"

        # load timestamps for both fields and check that they're close/equal
        eye_h_times = np.load(eye_h_times_file)
        eye_v_times = np.load(eye_v_times_file)
        assert np.allclose(eye_h_times, eye_v_times)

        # set timestamps for temporal alignment
        self.timestamp_file_path = eye_h_times_file
        self.timestamps = eye_h_times

    def add_to_nwbfile(self, nwbfile: NWBFile, metadata: dict):
        # get file paths and load eye position data
        folder_path = Path(self.source_data["folder_path"])
        eye_h = np.load(folder_path / "eye.h.values.npy")
        eye_v = np.load(folder_path / "eye.v.values.npy")

        # stack and transform data into screen coordinate system
        eye_pos = np.stack([eye_h, eye_v], axis=1)
        eye_pos = (eye_pos + 10.0) / 20.0  # desired conversion specified by Nick

        # make SpatialSeries
        eye_position = SpatialSeries(
            name="eye_position",
            data=H5DataIO(eye_pos, compression="gzip"),
            reference_frame="(0,0) is bottom left corner of screen",
            unit="meters",
            conversion=0.257,
            timestamps=H5DataIO(self.timestamps, compression="gzip"),
            description="Eye position data recorded by EyeLink camera",
        )

        # get processing module
        module_name = "behavior"
        module_description = "Contains behavioral data from experiment."
        processing_module = get_module(nwbfile=nwbfile, name=module_name, description=module_description)

        # add data to module
        processing_module.add_data_interface(eye_position)

        return nwbfile


class WattersPupilSizeInterface(NumpyTemporalAlignmentMixin, BaseTemporalAlignmentInterface):
    """Pupil size interface for Watters conversion"""

    def __init__(self, folder_path: FolderPathType):
        # initialize interface with timestamps
        super().__init__(folder_path=folder_path)

        # find eye position files (assume they all exist)
        folder_path = Path(folder_path)
        pupil_file = folder_path / "eye.pupil.values.npy"
        pupil_times_file = folder_path / "eye.pupil.times.npy"
        assert pupil_file.exists(), f"Could not find {pupil_file}"
        assert pupil_times_file.exists(), f"Could not find {pupil_times_file}"

        # set timestamps for temporal alignment
        self.timestamp_file_path = pupil_times_file
        self.timestamps = np.load(pupil_times_file)

    def add_to_nwbfile(self, nwbfile: NWBFile, metadata: dict):
        # get file paths and load eye position data
        folder_path = Path(self.source_data["folder_path"])
        pupil = np.load(folder_path / "eye.pupil.values.npy")

        # make SpatialSeries
        pupil_size = TimeSeries(
            name="pupil_size",
            data=H5DataIO(pupil, compression="gzip"),
            unit="pixels",
            conversion=1.0,
            timestamps=H5DataIO(self.timestamps, compression="gzip"),
            description="Pupil size data recorded by EyeLink camera",
        )

        # get processing module
        module_name = "behavior"
        module_description = "Contains behavioral data from experiment."
        processing_module = get_module(nwbfile=nwbfile, name=module_name, description=module_description)

        # add data to module
        processing_module.add_data_interface(pupil_size)

        return nwbfile
