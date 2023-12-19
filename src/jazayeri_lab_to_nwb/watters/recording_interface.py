"""Primary class for recording data."""
import json
from typing import Optional

import numpy as np
import probeinterface
from neuroconv.datainterfaces.ecephys.baserecordingextractorinterface import (
    BaseRecordingExtractorInterface,
)
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


class DatRecordingInterface(BaseRecordingExtractorInterface):
    ExtractorName = "BinaryRecordingExtractor"

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
        gain_to_uv: list = 1.0,
        offset_to_uv: list = 0.0,
        probe_metadata_file: Optional[FilePathType] = None,
        probe_name: str = "vprobe",
        probe_key: Optional[str] = None,
    ):
        source_data = {
            "file_paths": [file_path],
            "sampling_frequency": sampling_frequency,
            "num_channels": channel_count,
            "t_starts": [t_start],
            "channel_ids": channel_ids,
            "gain_to_uV": gain_to_uv,
            "offset_to_uV": offset_to_uv,
            "dtype": dtype,
        }
        super().__init__(verbose=verbose, es_key=es_key, **source_data)

        # this is used for metadata naming
        self.probe_name = probe_name

        # add probe information
        probe_metadata = None
        if probe_metadata_file is not None and probe_key is not None:
            with open(probe_metadata_file, "r") as f:
                all_probe_metadata = json.load(f)
            for entry in all_probe_metadata:
                if entry["label"] == probe_key:
                    probe_metadata = entry

        if probe_metadata is not None and "electrodes_locations" in probe_metadata:
            # Grab electrode position from metadata
            locations_array = np.array(probe_metadata["electrodes_locations"])
            ndim = locations_array.shape[1]
            probe = probeinterface.Probe(ndim=ndim)
            probeinterface.set_contacts(locations_array)
        else:
            # Generate V-probe geometry: 64 channels arranged vertically with 50 um spacing
            probe = probeinterface.generate_linear_probe(num_elec=channel_count, ypitch=50)
        probe.set_device_channel_indices(np.arange(channel_count))
        probe.name = probe_name

        # set probe to interface recording
        self.set_probe(probe, group_mode="by_probe")

        # set group_name property to match electrode group name in metadata
        self.recording_extractor.set_property(
            key="group_name",
            values=[probe_name] * len(self.recording_extractor.channel_ids),
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

        return metadata
