"""Primary class for Watters Plexon probe data."""
import os
import numpy as np
from pynwb import NWBFile
from pathlib import Path
from typing import Optional, Union

from neuroconv.datainterfaces.ecephys.baserecordingextractorinterface import BaseRecordingExtractorInterface
from neuroconv.utils import FilePathType


class WattersDatRecordingInterface(BaseRecordingExtractorInterface):

    ExtractorName = "NumpyRecording"

    def __init__(
        self,
        file_path: FilePathType,
        verbose: bool = True,
        es_key: str = "ElectricalSeries",
        channel_count: int = 64,
        dtype: str = "int16",
        t_start: float = 0.0,
        sampling_frequency: float = 30000.0,
        channel_ids: Optional[list] = None,
        gain_to_uv: list = [1.0],
    ):
        traces = np.memmap(file_path, dtype=dtype, mode="r").reshape(-1, channel_count)
        source_data = {
            "traces_list": [traces],
            "sampling_frequency": sampling_frequency,
            "t_starts": [t_start],
            "channel_ids": channel_ids,
        }
        super().__init__(verbose=verbose, es_key=es_key, **source_data)
        if gain_to_uv is not None:
            if len(gain_to_uv) == 1:
                gain_to_uv = np.full((channel_count,), gain_to_uv[0], dtype=float)
            else:
                assert len(gain_to_uv) == channel_count, (
                    f"There are {channel_count} channels " f"but `gain_to_uv` has length {len(gain_to_uv)}"
                )
                gain_to_uv = np.array(gain_to_uv, dtype=float)
            self.recording_extractor.set_property("gain_to_uV", gain_to_uv)
