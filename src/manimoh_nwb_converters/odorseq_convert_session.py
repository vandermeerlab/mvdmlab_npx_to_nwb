"""Primary script to run to convert an entire session of preprocessed mvdmlab NPX data."""
from pathlib import Path
import os
import numpy as np
import math
from datetime import datetime

from pynwb import NWBHDF5IO, NWBFile
from pynwb.ecephys import LFP, ElectricalSeries, SpikeEventSeries
from pynwb.file import Subject

from neuroconv.datainterfaces.ecephys.spikeglx.spikeglxdatainterface import SpikeGLXRecordingInterface
from neuroconv.tools.spikeinterface.spikeinterface import (
    add_electrodes_info_to_nwbfile, 
    add_devices_to_nwbfile, 
    add_electrode_groups_to_nwbfile,
    add_electrodes_to_nwbfile
)
import manimoh_utils as mu
import manimoh_nwb_converters as mnc

def create_nwb_file(raw_dirpath, preprocessed_dirpath, output_nwb_filepath, overwrite=True):
    """Create an NWB file from the data in the session directory.
    
    Parameters
    ----------
    raw_dirpath: str
        The directory containing raw, unprocessed source data for the session to be converted
    preprocessed_dirpath : str
        The directory containing the preprocessed data for the session to be converted
    output_nwbf_path : str or Path
        The path to the NWB file to create.
    overwrite : bool, optional
        If True, overwrite the NWB file if it already exists. If False, raise an error if the file already exists.
    
    Returns
    -------
    nwb_file : NWBFile
        The NWB file object.
    """
    raw_dir = Path(raw_dirpath)
    preprocessed_dir = Path(preprocessed_dirpath)
    output_nwb_file = Path(output_nwb_filepath)

    if output_nwb_file.exists() and not overwrite:
        raise FileExistsError(f"File {output_nwb_file} already exists. Set overwrite=True to overwrite.")

    # Get preprocessed_metadata present in ExpKeys file to determine which interfaces to create
    preprocessed_metadata = mu.parse_expkeys(preprocessed_dir)

    raw_interface = SpikeGLXRecordingInterface(folder_path=raw_dir, stream_id=f"{preprocessed_metadata['probe1_ID']}.ap")
    raw_metadata = raw_interface.get_metadata()

    out_nwb = NWBFile(
    session_description=preprocessed_metadata['notes'], 
    identifier='-'.join([preprocessed_metadata['subject'], preprocessed_metadata['date']]),
    session_start_time=raw_metadata['NWBFile']['session_start_time'].astimezone(), 
    experimenter=[
        preprocessed_metadata['experimenter']
    ],
    lab="vandermeerlab",
    institution="Dartmouth College",
    experiment_description="Head-fixed mouse presented with odor sequences",
    keywords=["ecephys", "neuropixels", "odor-sequences", "hippocampus"], # needs to be edited
    )

    sub_age = (datetime.strptime(preprocessed_metadata['date'], '%Y-%m-%d') - \
        datetime.strptime(preprocessed_metadata['DOB'], '%Y-%m-%d')).days//7
    # Create subject
    subject = Subject(subject_id=preprocessed_metadata['subject'], age=f"P{sub_age}W", 
        species = "Mus musculus", description = "Headbar-ed mouse with craniotomies over dCA1", 
        sex = preprocessed_metadata['sex'],
        )
    out_nwb.subject = subject

    # Add all electrodes from the first probe
    # Adding depth as a property
    distance_from_tip = raw_interface.recording_extractor.get_channel_locations()[:,1]
    this_depth = (preprocessed_metadata["probe1_Depth"]*1000 - distance_from_tip) * \
        np.cos(math.radians(preprocessed_metadata["probe1_insertion_roll"]))
    raw_interface.recording_extractor.set_property('recording_depth', values=this_depth)
    # Adding label and hemisphere as additional properties
    imec_id = [(x.split('.')[0]).replace('imec','') for x in raw_interface.recording_extractor.get_channel_ids()]
    channel_id = [(x.split('#')[-1]) for x in raw_interface.recording_extractor.get_channel_ids()]
    shank_id =  raw_interface.recording_extractor.get_channel_groups().tolist()
    this_label = [f"imec{imec_id[x]}_shank{shank_id[x]}_{channel_id[x]}" for x in range(len(imec_id))]
    raw_interface.recording_extractor.set_property('label', values=this_label)
    this_hemi = np.repeat(preprocessed_metadata['probe1_hemisphere'], len(this_label))
    raw_interface.recording_extractor.set_property('hemisphere', values=this_hemi)
    # Adding description of the new column to the metadata (Otherwise nwbinspector will cry that there is no description)
    raw_metadata['Ecephys']['Electrodes'].append({
        'name': 'recording_depth',
        'description': 'Depth of electrode from brain surface in micrometers, based on experimental annotation'
    })
    raw_metadata['Ecephys']['Electrodes'].append({
        'name': 'label',
        'description': 'Unique human-readable label for each recording channel'
    })
    raw_metadata['Ecephys']['Electrodes'].append({
        'name': 'hemisphere',
        'description': 'Brain hemisphere where this recording electrode was present'
    })
    add_electrodes_info_to_nwbfile(recording=raw_interface.recording_extractor, 
        nwbfile=out_nwb, metadata=raw_metadata)
    # if 2nd probe exists, then add electrodes from that too
    if 'probe2_ID' in preprocessed_metadata.keys():
        raw_interface2 = SpikeGLXRecordingInterface(folder_path=raw_dir, stream_id=f"{preprocessed_metadata['probe2_ID']}.ap")
        raw_metadata2 = raw_interface2.get_metadata()
        distance_from_tip = raw_interface2.recording_extractor.get_channel_locations()[:,1]
        this_depth = (preprocessed_metadata["probe2_Depth"]*1000 - distance_from_tip) * \
            np.cos(math.radians(preprocessed_metadata["probe2_insertion_roll"]))
        raw_interface2.recording_extractor.set_property('recording_depth', values=this_depth)
        # Adding label and hemisphere as additional properties
        imec_id2 = [(x.split('.')[0]).replace('imec','') for x in raw_interface2.recording_extractor.get_channel_ids()]
        channel_id2 = [(x.split('#')[-1]) for x in raw_interface2.recording_extractor.get_channel_ids()]
        shank_id2 =  raw_interface2.recording_extractor.get_channel_groups().tolist()
        this_label2 = [f"imec{imec_id2[x]}_shank{shank_id2[x]}_{channel_id2[x]}" for x in range(len(imec_id2))]
        raw_interface2.recording_extractor.set_property('label', values=this_label2)
        this_hemi2 = np.repeat(preprocessed_metadata['probe1_hemisphere'], len(this_label2))
        raw_interface2.recording_extractor.set_property('hemisphere', values=this_hemi2)
        # Adding description of the new column to the metadata (Otherwise nwbinspector will cry that there is no description)
        raw_metadata2['Ecephys']['Electrodes'].append({
            'name': 'recording_depth',
            'description': 'Depth of electrode from brain surface in micrometers, based on experimental annotation'
        })
        raw_metadata2['Ecephys']['Electrodes'].append({
            'name': 'label',
            'description': 'Unique human-readable label for each recording channel'
        })
        raw_metadata2['Ecephys']['Electrodes'].append({
            'name': 'hemisphere',
            'description': 'Brain hemisphere where this recording electrode was present'
        })
        add_electrodes_info_to_nwbfile(recording=raw_interface2.recording_extractor,
            nwbfile=out_nwb, metadata=raw_metadata2)
            
    # Add LFP data
    device_labels = []
    if os.path.exists(os.path.join(preprocessed_dir,"imec0_clean_lfp.mat")):
        device_labels.append("imec0")
    if os.path.exists(os.path.join(preprocessed_dir,"imec1_clean_lfp.mat")):
        device_labels.append("imec1")
    # add LFP traces to nwb file
    mnc.add_lfp_data_to_nwb(preprocessed_dir, out_nwb, preprocessed_metadata, device_labels)
        
    # Add spiking data
    device_labels = []
    if os.path.exists(os.path.join(preprocessed_dir,"clean_units_imec0.mat")):
        device_labels.append("imec0")
    if os.path.exists(os.path.join(preprocessed_dir,"clean_units_imec1.mat")):
        device_labels.append("imec1")
    mnc.add_sorting_data_to_nwb(preprocessed_dir, out_nwb, preprocessed_metadata, device_labels)
    
    # Add behavioral epochs
    mnc.add_intervals_to_nwb(preprocessed_dir, out_nwb, preprocessed_metadata)
    
    # Add lab metadata using the custom extension
    mnc.add_lab_metadata_to_nwb(out_nwb, preprocessed_metadata)
    
    # Write NWB file
    io = NWBHDF5IO(output_nwb_filepath, mode='w')
    io.write(out_nwb)
    io.close() # This is crtitcal and nwbinspector won't work without it


