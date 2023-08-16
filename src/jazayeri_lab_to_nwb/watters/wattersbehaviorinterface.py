"""Primary classes for converting experiment-specific behavior."""
import numpy as np
from pathlib import Path
from pynwb import NWBFile, TimeSeries
from pynwb.behavior import SpatialSeries
from hdmf.backends.hdf5 import H5DataIO

from neuroconv.basedatainterface import BaseDataInterface
from neuroconv.utils import DeepDict, FolderPathType
from neuroconv.tools.nwb_helpers import get_module


# TODO: make a BaseTemporalAlignmentInterface subclass that assumes
# numpy array timestamps and can apply transforms as they specify


class WattersEyePositionInterface(BaseDataInterface):
    """Eye position interface for watters conversion"""

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

    def add_to_nwbfile(self, nwbfile: NWBFile, metadata: dict):
        # get file paths and load eye position data
        folder_path = Path(self.source_data["folder_path"])
        eye_h = np.load(folder_path / "eye.h.values.npy")
        eye_v = np.load(folder_path / "eye.v.values.npy")
        eye_h_times = np.load(folder_path / "eye.h.times.npy")
        eye_v_times = np.load(folder_path / "eye.v.times.npy")
        assert np.allclose(eye_h_times, eye_v_times)
        timestamps = eye_h_times

        # stack and transform data into screen coordinate system
        eye_pos = np.stack([eye_h, eye_v], axis=1)
        eye_pos = (eye_pos + 10.0) / 20.0

        # make SpatialSeries
        eye_position = SpatialSeries(
            name="eye_position",
            data=H5DataIO(eye_pos, compression="gzip"),
            reference_frame="(0,0) is bottom left corner of screen",
            unit="meters",
            conversion=1.0,  # TODO: determine this
            timestamps=H5DataIO(timestamps, compression="gzip"),
            description="Eye position data recorded by EyeLink camera",
        )

        # get processing module
        module_name = "behavior"
        module_description = "Contains behavioral data from experiment"
        processing_module = get_module(nwbfile=nwbfile, name=module_name, description=module_description)

        # add data to module
        processing_module.add_data_interface(eye_position)

        return nwbfile


class WattersPupilSizeInterface(BaseDataInterface):
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

    def add_to_nwbfile(self, nwbfile: NWBFile, metadata: dict):
        # get file paths and load eye position data
        folder_path = Path(self.source_data["folder_path"])
        pupil = np.load(folder_path / "eye.pupil.values.npy")
        timestamps = np.load(folder_path / "eye.pupil.times.npy")

        # make SpatialSeries
        pupil_size = TimeSeries(
            name="pupil_size",
            data=H5DataIO(pupil, compression="gzip"),
            unit="meters",  # TODO: determine this
            conversion=1.0,  # TODO: determine this
            timestamps=H5DataIO(timestamps, compression="gzip"),
            description="Pupil size data recorded by EyeLink camera",
        )

        # get processing module
        module_name = "behavior"
        module_description = "Contains behavioral data from experiment"
        processing_module = get_module(nwbfile=nwbfile, name=module_name, description=module_description)

        # add data to module
        processing_module.add_data_interface(pupil_size)

        return nwbfile
