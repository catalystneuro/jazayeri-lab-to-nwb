"""Primary NWBConverter class for this dataset."""
import json
import numpy as np
from typing import Optional
from pathlib import Path

from neuroconv import NWBConverter
from neuroconv.utils import FolderPathType
from neuroconv.datainterfaces import (
    SpikeGLXRecordingInterface,
    SpikeGLXLFPInterface,
    KiloSortSortingInterface,
)
from neuroconv.datainterfaces.ecephys.baserecordingextractorinterface import BaseRecordingExtractorInterface
from neuroconv.datainterfaces.ecephys.basesortingextractorinterface import BaseSortingExtractorInterface
from neuroconv.basetemporalalignmentinterface import BaseTemporalAlignmentInterface
from neuroconv.datainterfaces.text.timeintervalsinterface import TimeIntervalsInterface

from jazayeri_lab_to_nwb.watters import (
    WattersBehaviorInterface,
    WattersDatRecordingInterface,
    WattersTrialsInterface,
)


class WattersNWBConverter(NWBConverter):
    """Primary conversion class for my extracellular electrophysiology dataset."""

    data_interface_classes = dict(
        RecordingNP=SpikeGLXRecordingInterface,
        LFP=SpikeGLXRecordingInterface,
        SortingNP=KiloSortSortingInterface,
        RecordingVP1=WattersDatRecordingInterface,
        SortingVP1=KiloSortSortingInterface,
        RecordingVP2=WattersDatRecordingInterface,
        SortingVP2=KiloSortSortingInterface,
        # Behavior=WattersBehaviorInterface,
        Trials=WattersTrialsInterface,
    )

    def __init__(
        self,
        source_data: dict[str, dict],
        sync_dir: Optional[FolderPathType] = None,
        verbose: bool = True,
    ):
        """Validate source_data against source_schema and initialize all data interfaces."""
        super().__init__(source_data=source_data, verbose=verbose)
        self.sync_dir = sync_dir
        # self._add_missing_recording_properties()

    def temporally_align_data_interfaces(self):
        if self.sync_dir is None:
            return
        sync_dir = Path(self.sync_dir)

        # constant bias
        with open(sync_dir / "mworks" / "open_source_minus_processed", "r") as f:
            bias = float(f.read().strip())

        # openephys alignment
        for probe_num in [1, 2]:
            orig_timestamps = self.data_interface_objects[f"RecordingVP{probe_num}"].get_timestamps()
            with open(sync_dir / "open_ephys" / "recording_start_time") as f:
                start_time = float(f.read().strip())
            with open(sync_dir / "open_ephys" / "transform", "r") as f:
                transform = json.load(f)
            aligned_timestamps = bias + transform["intercept"] + transform["coef"] * (start_time + orig_timestamps)
            self.data_interface_objects[f"RecordingVP{probe_num}"].set_aligned_timestamps(aligned_timestamps)
            # openephys sorting alignment
            self.data_interface_objects[f"SortingVP{probe_num}"].register_recording(
                self.data_interface_objects[f"RecordingVP{probe_num}"]
            )

        # neuropixel alignment
        orig_timestamps = self.data_interface_objects["RecordingNP"].get_timestamps()
        with open(sync_dir / "spikeglx" / "transform", "r") as f:
            transform = json.load(f)
        aligned_timestamps = bias + transform["intercept"] + transform["coef"] * orig_timestamps
        self.data_interface_objects["RecordingNP"].set_aligned_timestamps(aligned_timestamps)
        # neuropixel LFP alignment
        orig_timestamps = self.data_interface_objects["LFP"].get_timestamps()
        aligned_timestamps = bias + transform["intercept"] + transform["coef"] * orig_timestamps
        self.data_interface_objects["LFP"].set_aligned_timestamps(aligned_timestamps)
        # neuropixel sorting alignment
        self.data_interface_objects["SortingNP"].register_recording(self.data_interface_objects["RecordingNP"])

        # align recording start to 0
        aligned_start_times = []
        for name, data_interface in self.data_interface_objects.items():
            if isinstance(data_interface, BaseTemporalAlignmentInterface):
                start_time = data_interface.get_timestamps()[0]
                aligned_start_times.append(start_time)
            elif isinstance(data_interface, TimeIntervalsInterface):
                start_time = data_interface.get_timestamps(column="start_time")[0]
                aligned_start_times.append(start_time)
        zero_time = -1.0 * min(aligned_start_times)
        for name, data_interface in self.data_interface_objects.items():
            if isinstance(data_interface, BaseSortingExtractorInterface):
                # don't need to align b/c recording will be aligned separately
                continue
            elif hasattr(data_interface, "set_aligned_starting_time"):
                start_time = data_interface.set_aligned_starting_time(aligned_starting_time=zero_time)
                aligned_start_times.append(start_time)
