"""Primary class for converting preprocessed mvdmlab NPX LFP data."""
from pynwb.file import NWBFile
from pathlib import Path
from pydantic import DirectoryPath
import numpy as np

from pynwb.ecephys import ElectricalSeries, LFP
from neuroconv import BaseDataInterface
from neuroconv.tools import nwb_helpers
from neuroconv.utils import get_base_schema

class OdorSeqLFPInterface(BaseDataInterface):
    """Primary class for converting preprocessed mvdmlab NPX LFP data."""

    _path = DirectoryPath
    _lfp_data = np.ndarray

    def run_conversion(self, nwbfile: NWBFile):
        """Primary conversion method."""
        lfp_data = self._lfp_data
        lfp = LFP(name="LFP", data=lfp_data, electrodes=nwbfile.electrodes)
        nwbfile.add_acquisition(lfp)

    @classmethod
    def get_source_schema(cls):
        """Return schema for data interface."""
        return get_base_schema(cls)

    @classmethod
    def get_target_schema(cls):
        """Return schema for data interface."""
        return get_base_schema(cls)

    @classmethod
    def get_data_interface(cls, source_data: dict):
        """Return data interface object."""
        return cls(**source_data)

    @classmethod
    def get_data_interface_source(cls, path: Path):
        """Return data interface source."""
        return {"path": path}

    @classmethod
    def get_data_interface_target(cls, lfp_data: np.ndarray):
        """Return data interface target."""
        return {"lfp_data": lfp_data}