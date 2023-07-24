"""Primary NWBConverter class for this dataset."""
from neuroconv import NWBConverter
from neuroconv.datainterfaces import (
    SpikeGLXRecordingInterface,
    SpikeGLXNIDQInterface,
    PhySortingInterface,
)

from jazayeri_lab_to_nwb.watters import (
    WattersBehaviorInterface,
    WattersOpenEphysRecordingInterface,
)


class WattersNWBConverter(NWBConverter):
    """Primary conversion class for my extracellular electrophysiology dataset."""

    data_interface_classes = dict(
        # Recording=SpikeGLXRecordingInterface,
        OERecording=WattersOpenEphysRecordingInterface,
        # LFP=SpikeGLXRecordingInterface,
        # NIDQ=SpikeGLXNIDQInterface,
        # Sorting=PhySortingInterface,
        # Behavior=WattersBehaviorInterface,
    )
