"""Primary NWBConverter class for this dataset."""
from neuroconv import NWBConverter

from manimoh_nwb_converters import (
    OdorSeqLFPInterface #,
    # OdorSeqSortingInterface,
    # OdorSeqEventInterface,
    # OdorSeqBehaviorInterface,
)


class OdorSeqNWBConverter(NWBConverter):
    """Primary conversion class for my extracellular electrophysiology dataset."""

    data_interface_classes = dict(
        LFP=OdorSeqLFPInterface #,
        # Sorting=OdorSeqSortingInterface,
        # Event=OdorSeqEventInterface,
        # Behavior=OdorSeqBehaviorInterface,
    )