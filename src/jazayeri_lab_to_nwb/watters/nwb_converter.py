"""Primary NWBConverter class for this dataset."""

import json
import logging
from pathlib import Path
from typing import Optional

import display_interface
import neuroconv
import numpy as np
import timeseries_interface
import trials_interface
from neuroconv.datainterfaces.ecephys.basesortingextractorinterface import (
    BaseSortingExtractorInterface,
)
from neuroconv.utils import FolderPathType
from recording_interface import DatRecordingInterface
from spikeinterface.core import waveform_tools


class NWBConverter(neuroconv.NWBConverter):
    """Primary conversion class for extracellular electrophysiology dataset."""

    data_interface_classes = dict(
        RecordingVP0=DatRecordingInterface,
        SortingVP0=neuroconv.datainterfaces.KiloSortSortingInterface,
        RecordingVP1=DatRecordingInterface,
        SortingVP1=neuroconv.datainterfaces.KiloSortSortingInterface,
        RecordingNP=neuroconv.datainterfaces.SpikeGLXRecordingInterface,
        LF=neuroconv.datainterfaces.SpikeGLXRecordingInterface,
        SortingNP=neuroconv.datainterfaces.KiloSortSortingInterface,
        EyePosition=timeseries_interface.EyePositionInterface,
        PupilSize=timeseries_interface.PupilSizeInterface,
        RewardLine=timeseries_interface.RewardLineInterface,
        Audio=timeseries_interface.AudioInterface,
        Trials=trials_interface.TrialsInterface,
        Display=display_interface.DisplayInterface,
    )

    def __init__(
        self,
        source_data: dict[str, dict],
        sync_dir: Optional[FolderPathType] = None,
        verbose: bool = True,
    ):
        """Validate source_data and initialize all data interfaces."""
        super().__init__(source_data=source_data, verbose=verbose)
        self.sync_dir = sync_dir

        unit_name_start = 0
        for data_interface in self.data_interface_objects.values():
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

        # Align each recording
        for name, recording_interface in self.data_interface_objects.items():
            if "Recording" not in name:
                continue
            probe_name = name.split("Recording")[1]

            # Load timescale transform
            if "VP" in probe_name:
                start_path = sync_dir / "open_ephys" / "recording_start_time"
                start = float(open(start_path).read().strip())
                transform_path = sync_dir / "open_ephys" / "transform"
                transform = json.load(open(transform_path, "r"))
                lf_interface = None
            elif "NP" in probe_name:
                start = 0.0
                transform_path = sync_dir / "spikeglx" / "transform"
                transform = json.load(open(transform_path, "r"))
                lf_interface = self.data_interface_objects["LF"]
            else:
                raise ValueError("Invalid probe_name {probe_name}")
            intercept = transform["intercept"]
            coef = transform["coef"]

            # Align recording timestamps
            orig_timestamps = recording_interface.get_original_timestamps()
            aligned_timestamps = intercept + coef * (start + orig_timestamps)
            recording_interface.set_aligned_timestamps(aligned_timestamps)

            # Align LFP timestamps
            if lf_interface is not None:
                orig_timestamps = lf_interface.get_original_timestamps()
                aligned_timestamps = intercept + coef * (
                    start + orig_timestamps
                )
                lf_interface.set_aligned_timestamps(aligned_timestamps)

            # If sorting exists, register recording to it
            if f"Sorting{probe_name}" in self.data_interface_objects:
                sorting_interface = self.data_interface_objects[
                    f"Sorting{probe_name}"
                ]

                # Sanity check no sorted spikes are outside recording range
                exceeded_spikes = waveform_tools.has_exceeding_spikes(
                    recording=recording_interface.recording_extractor,
                    sorting=sorting_interface.sorting_extractor,
                )
                if exceeded_spikes:
                    raise ValueError(
                        "Spikes exceeding recording found in "
                        f"Sorting{probe_name}"
                    )

                # Register recording
                sorting_interface.register_recording(recording_interface)

        # Align so that 0 is the first of all timestamps
        aligned_start_times = []
        for data_interface in self.data_interface_objects.values():
            start_time = data_interface.get_timestamps()[0]
            aligned_start_times.append(start_time)
        zero_time = -1.0 * min(aligned_start_times)
        for data_interface in self.data_interface_objects.values():
            if isinstance(data_interface, BaseSortingExtractorInterface):
                # Do not need to align because recording will be aligned
                continue
            start_time = data_interface.set_aligned_starting_time(
                aligned_starting_time=zero_time
            )
