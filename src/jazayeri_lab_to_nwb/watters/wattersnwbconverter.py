"""Primary NWBConverter class for this dataset."""
import json
from typing import Optional
from pathlib import Path

from neuroconv import NWBConverter
from neuroconv.utils import FolderPathType
from neuroconv.datainterfaces import (
    SpikeGLXRecordingInterface,
    KiloSortSortingInterface,
)

from jazayeri_lab_to_nwb.watters import WattersBehaviorInterface


class WattersNWBConverter(NWBConverter):
    """Primary conversion class for my extracellular electrophysiology dataset."""

    data_interface_classes = dict(
        Recording=SpikeGLXRecordingInterface,
        LFP=SpikeGLXRecordingInterface,
        Sorting=KiloSortSortingInterface,
        # Behavior=WattersBehaviorInterface,
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

    def temporally_align_data_interfaces(self):
        if self.sync_dir is None:
            return
        sync_dir = Path(self.sync_dir)
        # constant bias
        with open(sync_dir / "mworks" / "open_source_minus_processed", "r") as f:
            bias = float(f.read().strip())
        # neuropixel alignment
        orig_timestamps = self.data_interface_objects["Recording"].get_timestamps()
        with open(sync_dir / "spikeglx" / "transform", "r") as f:
            transform = json.load(f)
        aligned_timestamps = bias + transform["intercept"] + transform["coef"] * orig_timestamps
        self.data_interface_objects["Recording"].set_aligned_timestamps(aligned_timestamps)
        # neuropixel LFP alignment
        orig_timestamps = self.data_interface_objects["LFP"].get_timestamps()
        aligned_timestamps = bias + transform["intercept"] + transform["coef"] * orig_timestamps
        self.data_interface_objects["LFP"].set_aligned_timestamps(aligned_timestamps)
        # neuropixel sorting alignment
        self.data_interface_objects["Sorting"].register_recording(self.data_interface_objects["Recording"])
