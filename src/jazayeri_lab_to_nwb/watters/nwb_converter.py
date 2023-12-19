"""Primary NWBConverter class for this dataset."""
import json
import logging
from pathlib import Path
from typing import Optional

import numpy as np
from display_interface import DisplayInterface
from neuroconv import NWBConverter
from neuroconv.datainterfaces import (
    KiloSortSortingInterface,
    SpikeGLXRecordingInterface,
)
from neuroconv.datainterfaces.ecephys.basesortingextractorinterface import (
    BaseSortingExtractorInterface,
)
from neuroconv.utils import FolderPathType
from recording_interface import DatRecordingInterface
from spikeinterface.core.waveform_tools import has_exceeding_spikes
from spikeinterface.curation import remove_excess_spikes
from timeseries_interface import (
    AudioInterface,
    EyePositionInterface,
    PupilSizeInterface,
    RewardLineInterface,
)
from trials_interface import TrialsInterface


class NWBConverter(NWBConverter):
    """Primary conversion class for extracellular electrophysiology dataset."""

    data_interface_classes = dict(
        RecordingVP0=DatRecordingInterface,
        SortingVP0=KiloSortSortingInterface,
        RecordingVP1=DatRecordingInterface,
        SortingVP1=KiloSortSortingInterface,
        RecordingNP=SpikeGLXRecordingInterface,
        LF=SpikeGLXRecordingInterface,
        SortingNP=KiloSortSortingInterface,
        EyePosition=EyePositionInterface,
        PupilSize=PupilSizeInterface,
        RewardLine=RewardLineInterface,
        Audio=AudioInterface,
        Trials=TrialsInterface,
        Display=DisplayInterface,
    )

    def __init__(self, source_data: dict[str, dict], sync_dir: Optional[FolderPathType] = None, verbose: bool = True):
        """Validate source_data and initialize all data interfaces."""
        super().__init__(source_data=source_data, verbose=verbose)
        self.sync_dir = sync_dir

        unit_name_start = 0
        for name, data_interface in self.data_interface_objects.items():
            if isinstance(data_interface, BaseSortingExtractorInterface):
                unit_ids = np.array(data_interface.sorting_extractor.unit_ids)
                data_interface.sorting_extractor.set_property(
                    key="unit_name",
                    values=(unit_ids + unit_name_start).astype(str),
                )
                unit_name_start += np.max(unit_ids) + 1

    def temporally_align_data_interfaces(self):
        logging.info("Temporally aligning data interfaces")

        if self.sync_dir is None:
            return
        sync_dir = Path(self.sync_dir)

        # openephys alignment
        with open(sync_dir / "open_ephys" / "recording_start_time") as f:
            open_ephys_start_time = float(f.read().strip())
        with open(sync_dir / "open_ephys" / "transform", "r") as f:
            open_ephys_transform = json.load(f)
        for i in [0, 1]:
            if f"RecordingVP{i}" in self.data_interface_objects:
                orig_timestamps = self.data_interface_objects[f"RecordingVP{i}"].get_original_timestamps()
                aligned_timestamps = open_ephys_transform["intercept"] + open_ephys_transform["coef"] * (
                    open_ephys_start_time + orig_timestamps
                )
                self.data_interface_objects[f"RecordingVP{i}"].set_aligned_timestamps(aligned_timestamps)
                # openephys sorting alignment
                if f"SortingVP{i}" in self.data_interface_objects:
                    if has_exceeding_spikes(
                        recording=self.data_interface_objects[f"RecordingVP{i}"].recording_extractor,
                        sorting=self.data_interface_objects[f"SortingVP{i}"].sorting_extractor,
                    ):
                        print(
                            f"Spikes exceeding recording found in SortingVP{i}! "
                            "Removing with `spikeinterface.curation.remove_excess_spikes()`"
                        )
                        self.data_interface_objects[f"SortingVP{i}"].sorting_extractor = remove_excess_spikes(
                            recording=self.data_interface_objects[f"RecordingVP{i}"].recording_extractor,
                            sorting=self.data_interface_objects[f"SortingVP{i}"].sorting_extractor,
                        )
                    self.data_interface_objects[f"SortingVP{i}"].register_recording(
                        self.data_interface_objects[f"RecordingVP{i}"]
                    )

        # neuropixel alignment
        orig_timestamps = self.data_interface_objects["RecordingNP"].get_original_timestamps()
        with open(sync_dir / "spikeglx" / "transform", "r") as f:
            spikeglx_transform = json.load(f)
        aligned_timestamps = spikeglx_transform["intercept"] + spikeglx_transform["coef"] * orig_timestamps
        self.data_interface_objects["RecordingNP"].set_aligned_timestamps(aligned_timestamps)
        # neuropixel LFP alignment
        orig_timestamps = self.data_interface_objects["LF"].get_original_timestamps()
        aligned_timestamps = spikeglx_transform["intercept"] + spikeglx_transform["coef"] * orig_timestamps
        self.data_interface_objects["LF"].set_aligned_timestamps(aligned_timestamps)
        # neuropixel sorting alignment
        if "SortingNP" in self.data_interface_objects:
            if has_exceeding_spikes(
                recording=self.data_interface_objects["RecordingNP"].recording_extractor,
                sorting=self.data_interface_objects["SortingNP"].sorting_extractor,
            ):
                print(
                    "Spikes exceeding recording found in SortingNP! "
                    "Removing with `spikeinterface.curation.remove_excess_spikes()`"
                )
                self.data_interface_objects["SortingNP"].sorting_extractor = remove_excess_spikes(
                    recording=self.data_interface_objects["RecordingNP"].recording_extractor,
                    sorting=self.data_interface_objects["SortingNP"].sorting_extractor,
                )
            self.data_interface_objects["SortingNP"].register_recording(self.data_interface_objects["RecordingNP"])

        # align recording start to 0
        aligned_start_times = []
        for name, data_interface in self.data_interface_objects.items():
            start_time = data_interface.get_timestamps()[0]
            aligned_start_times.append(start_time)
        zero_time = -1.0 * min(aligned_start_times)
        for name, data_interface in self.data_interface_objects.items():
            if isinstance(data_interface, BaseSortingExtractorInterface):
                # Do not need to align because recording will be aligned
                continue
            start_time = data_interface.set_aligned_starting_time(aligned_starting_time=zero_time)
