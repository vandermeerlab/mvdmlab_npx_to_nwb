"""Primary script to run to convert an entire session of preprocessed mvdmlab NPX data."""
from pathlib import Path
import datetime
from zoneinfo import ZoneInfo
import shutil
from datetime import datetime
from dateutil.tz import tzlocal
import os

from pynwb import NWBHDF5IO, NWBFile
from pynwb.ecephys import LFP, ElectricalSeries, SpikeEventSeries
from pynwb.file import Subject

import manimoh_utils as mu
import manimoh_nwb_converters as mnc

def create_nwb_file(session_dir, nwb_file_path, overwrite=False):
    """Create an NWB file from the data in the session directory.
    
    Parameters
    ----------
    session_dir : str or Path
        The directory containing the session data.
    nwb_file_path : str or Path
        The path to the NWB file to create.
    overwrite : bool, optional
        If True, overwrite the NWB file if it already exists. If False, raise an error if the file already exists.
    
    Returns
    -------
    nwb_file : NWBFile
        The NWB file object.
    """
    session_dir = Path(session_dir)
    nwb_file_path = Path(nwb_file_path)
    
    if nwb_file_path.exists() and not overwrite:
        raise FileExistsError(f"File {nwb_file_path} already exists. Set overwrite=True to overwrite.")
    
    # Get the session metadata present in exp_keys file
    session_metadata = mu.parse_expkeys(session_dir)
    
    out_nwb = NWBFile(
    session_description=session_metadata['notes'], 
    identifier='-'.join([session_metadata['subject'], session_metadata['date']]),
    session_start_time=datetime.now(tzlocal()), # Get from .meta file
    experimenter=[
        session_metadata['experimenter']
    ],
    lab="vandermeerlab",
    institution="Dartmouth College",
    experiment_description="Head-fixed mouse presented with odor sequences",
    keywords=["ecephys", "neuropixels", "odor-sequences", "hippocampus"], # needs to be edited
    )

    # Create subject
    subject = Subject(subject_id=session_metadata['subject'], age="P8W/",  # Dummy value/hard-coded for now, but replace with logic to calculate from DOB and experiment date
        species = "Mus musculus", description = "Headbar-ed mouse with craniotomies over dCA1", 
        sex = "M",  # Dummy value/hard-coded for now, but replace with real value from updated ExpKeys
        )
    out_nwb.subject = subject
    
    # Add LFP data
    device_labels = []
    if os.path.exists(os.path.join(session_dir,"imec0_clean_lfp.mat")):
        device_labels.append("imec0")
    if os.path.exists(os.path.join(session_dir,"imec1_clean_lfp.mat")):
        device_labels.append("imec1")
    # add LFP electrodes table to nwb file
    mnc.add_lfp_electrodes_to_nwb(session_dir, out_nwb, session_metadata, device_labels)
    # add LFP traces to nwb file
    mnc.add_lfp_data_to_nwb(session_dir, out_nwb, session_metadata, device_labels)
        
    # Add spiking data
    device_labels = []
    if os.path.exists(os.path.join(session_dir,"clean_units_imec0.mat")):
        device_labels.append("imec0")
    if os.path.exists(os.path.join(session_dir,"clean_units_imec1.mat")):
        device_labels.append("imec1")
    mnc.add_sorting_electrodes_to_nwb(session_dir, out_nwb, session_metadata, device_labels)
    # add spike times, waveforms, and other information to nwb file
    mnc.add_sorting_data_to_nwb(session_dir, out_nwb, session_metadata, device_labels)
    
    # Add behavioral epochs
    mnc.add_intervals_to_nwb(session_dir, out_nwb, session_metadata)
    
    # Add lab metadata using the custom extension
    mnc.add_lab_metadata_to_nwb(out_nwb, session_metadata)
    
    # Write NWB file
    io = NWBHDF5IO(nwb_file_path, mode='w')
    io.write(out_nwb)
    io.close() # This is crtitcal and nwbinspector won't work without it


