"""Primary class for Watters Plexon probe data."""
import os
import json
import numpy as np
from pynwb import NWBFile
from pathlib import Path
from typing import Optional, Union

from neuroconv.datainterfaces.ecephys.baserecordingextractorinterface import BaseRecordingExtractorInterface
from neuroconv.utils import FilePathType
from spikeinterface import BaseRecording


def add_electrode_locations(
    recording_extractor: BaseRecording,
    probe_metadata_file: FilePathType,
    probe_name: str,
    probe_key: str,
) -> list[dict]:
    with open(probe_metadata_file, "r") as f:
        all_probe_metadata = json.load(f)
    probe_metadata = None
    for entry in all_probe_metadata:
        if entry["label"] == probe_key:
            probe_metadata = entry

    if probe_metadata is None:
        return []

    probe_coord_system = probe_metadata["coordinate_system"]
    coord_names = probe_coord_system.split("[")[1].split("]")[0].split(",")
    electrode_metadata = [
        {
            "name": "x",
            "description": f"{coord_names[0].strip()} coordinate. {probe_coord_system}",
        },
        {
            "name": "y",
            "description": f"{coord_names[1].strip()} coordinate. {probe_coord_system}",
        },
    ]
    if len(coord_names) == 3:
        electrode_metadata.append(
            {
                "name": "z",
                "description": f"{coord_names[2].strip()} coordinate. {probe_coord_system}",
            },
        )

    channel_ids = recording_extractor.get_channel_ids()
    recording_extractor.set_property(
        key="group_name",
        ids=channel_ids,
        values=[probe_name] * len(channel_ids),
    )
    coordinates = probe_metadata["coordinates"]
    recording_extractor.set_property(
        key="x",
        values=[coordinates["first_channel"][0], coordinates["last_channel"][0]],
        ids=channel_ids[[0, -1]],
    )
    recording_extractor.set_property(
        key="y",
        values=[coordinates["first_channel"][1], coordinates["last_channel"][1]],
        ids=channel_ids[[0, -1]],
    )
    if len(coord_names) == 3:
        recording_extractor.set_property(
            key="z",
            values=[coordinates["first_channel"][2], coordinates["last_channel"][2]],
            ids=channel_ids[[0, -1]],
        )

    return electrode_metadata


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
        probe_metadata_file: Optional[FilePathType] = None,
        probe_name: str = "vprobe",
        probe_key: Optional[str] = None,
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
        self.probe_metadata_file = probe_metadata_file
        self.probe_name = probe_name
        self.probe_key = probe_key

        self.electrode_metadata = None
        if self.probe_metadata_file is not None and self.probe_key is not None:
            self.electrode_metadata = add_electrode_locations(
                self.recording_extractor, self.probe_metadata_file, self.probe_name, self.probe_key
            )

    def get_metadata(self) -> dict:
        metadata = super().get_metadata()
        metadata["Ecephys"]["Device"] = [
            dict(
                name=self.probe_name,
                description="64-channel Plexon V-Probe",
                manufacturer="Plexon",
            )
        ]
        electrode_groups = [
            dict(
                name=self.probe_name,
                description=f"a group representing electrodes on {self.probe_name}",
                location="unknown",
                device=self.probe_name,
            )
        ]
        metadata["Ecephys"]["ElectrodeGroup"] = electrode_groups

        if self.electrode_metadata is None:
            return metadata

        metadata["Ecephys"]["Electrodes"] = self.electrode_metadata
        return metadata
