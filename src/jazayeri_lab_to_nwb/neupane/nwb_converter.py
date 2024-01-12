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
from spikeinterface import curation


def _trim_excess_spikes(
    recording_interface, sorting_interface, max_excess_samples=300
):
    """Trim sorting object spikes that exceed the recording number of samples.

    Args:
        recording: BaseRecording instance. The recording object.
        sorting: BaseSorting instance. The sorting object.
        max_excess_samples: Int. If a spike exists more than this number of
            samples beyond the end of the recording, an error is raised. This is
            in units of samples, which is typically 30000Hz.

    Returns:
        bool True if exceeding spikes, False otherwise.
    """
    recording_extractor = recording_interface.recording_extractor
    sorting_extractor = sorting_interface.sorting_extractor
    spike_vector = sorting_extractor.to_spike_vector()
    has_exceeding_spikes = False
    for segment_index in range(recording_extractor.get_num_segments()):
        start_seg_ind, end_seg_ind = np.searchsorted(
            spike_vector["segment_index"], [segment_index, segment_index + 1]
        )
        spike_vector_seg = spike_vector[start_seg_ind:end_seg_ind]
        if len(spike_vector_seg) > 0:
            last_spike_vector_sample = spike_vector_seg["sample_index"][-1]
            last_recording_sample = recording_extractor.get_num_samples(
                segment_index=segment_index
            )
            excess = last_spike_vector_sample - last_recording_sample + 1
            if excess > max_excess_samples:
                raise ValueError(
                    f"Spikes detected at least {excess} samples after the end "
                    "of the recording."
                )
            elif excess > 0:
                has_exceeding_spikes = True

    if has_exceeding_spikes:
        # Sometimes kilosort can detect spike that happen very
        # slightly after the recording stopped
        sorting_interface.sorting_extractor = curation.remove_excess_spikes(
            recording=recording_extractor,
            sorting=sorting_extractor,
        )

    return


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

