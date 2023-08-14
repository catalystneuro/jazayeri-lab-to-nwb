"""Primary NWBConverter class for this dataset."""
from neuroconv import NWBConverter
from neuroconv.datainterfaces import (
    SpikeGLXRecordingInterface,
    SpikeGLXLFPInterface,
    KiloSortSortingInterface,
)

from jazayeri_lab_to_nwb.watters import (
    WattersBehaviorInterface,
    WattersDatRecordingInterface,
)


class WattersNWBConverter(NWBConverter):
    """Primary conversion class for my extracellular electrophysiology dataset."""

    data_interface_classes = dict(
        Recording=WattersDatRecordingInterface,
        Sorting=KiloSortSortingInterface,
        # Behavior=WattersBehaviorInterface,
    )
