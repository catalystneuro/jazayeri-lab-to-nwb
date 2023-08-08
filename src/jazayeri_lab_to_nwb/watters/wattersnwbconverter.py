"""Primary NWBConverter class for this dataset."""
from neuroconv import NWBConverter
from neuroconv.datainterfaces import (
    SpikeGLXRecordingInterface,
    SpikeGLXNIDQInterface,
    PhySortingInterface,
    KiloSortSortingInterface,
)

from jazayeri_lab_to_nwb.watters import (
    WattersBehaviorInterface,
    WattersOpenEphysRecordingInterface,
)


class WattersNWBConverter(NWBConverter):
    """Primary conversion class for my extracellular electrophysiology dataset."""

    data_interface_classes = dict(
        # NPRecording=SpikeGLXRecordingInterface,
        # OERecording=WattersOpenEphysRecordingInterface,
        # VP1Recording=WattersOpenEphysRecordingInterface,
        # VP2Recording=WattersOpenEphysRecordingInterface,
        # LFP=SpikeGLXRecordingInterface,
        # NIDQ=SpikeGLXNIDQInterface,
        VP1Sorting=KiloSortSortingInterface,
        VP2Sorting=KiloSortSortingInterface,
        NPSorting=KiloSortSortingInterface,
        # Behavior=WattersBehaviorInterface,
    )
