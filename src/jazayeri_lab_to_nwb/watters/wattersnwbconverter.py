"""Primary NWBConverter class for this dataset."""
from neuroconv import NWBConverter
from neuroconv.datainterfaces import (
    SpikeGLXRecordingInterface,
    SpikeGLXLFPInterface,
    PhySortingInterface,
)

from jazayeri_lab_to_nwb.watters import (
    WattersEyePositionInterface,
    WattersPupilSizeInterface,
    WattersTrialsInterface,
)


class WattersNWBConverter(NWBConverter):
    """Primary conversion class for my extracellular electrophysiology dataset."""

    data_interface_classes = dict(
        # Recording=SpikeGLXRecordingInterface,
        # LFP=SpikeGLXLFPInterface,
        # Sorting=PhySortingInterface,
        EyePosition=WattersEyePositionInterface,
        PupilSize=WattersPupilSizeInterface,
        Trials=WattersTrialsInterface,
    )
