"""Various functions to help convert preprocessed mvdmlab NPX LFP data to NWB format."""

import h5py
import numpy as np
import math
from hdmf.backends.hdf5.h5_utils import H5DataIO
import os
from pathlib import Path

from pynwb.ecephys import ElectricalSeries, LFP

from neuroconv.tools.spikeinterface.spikeinterface import _get_electrodes_table_global_ids

def add_lfp_electrodes_to_nwb(session_dir, nwbfile, session_metadata, device_labels):
    '''
    Function to add LFP electrodes and probe information to the NWB file.
    '''
    
    sess_dir = Path(session_dir)
    # Add electrode column to nwb file (This will get poulated later)
    nwbfile.add_electrode_column(name="label", description="Identifier for the channel on the probe") # Calling this label to ensure compatibility with pynapple
    nwbfile.add_electrode_column(name="depth", description="Location of the electrode on the probe")
    nwbfile.add_electrode_column(name="hemisphere", description="Location of the electrode on the probe")
    
    for device_label in device_labels:
    # Determine whether probe1 or probe2 is imec0s
        if session_metadata['probe1_ID'] == device_label:
            device_key = 'probe1'
        else:
            device_key ='probe2'

        device_metadata = {}
        for key in session_metadata:
            if device_key in key and 'ID' not in key:
                device_metadata[key.split('_')[-1]] = session_metadata[key]
        
        # TODO: Should the description be changed to something more standard?
        device = nwbfile.create_device(name=device_label, \
            description="4-shank NPX2.0 ", manufacturer="IMEC")
        
        # Reading and parsing the .mat file to create the electrode table
        lfp_matfile = h5py.File(os.path.join(sess_dir, device_label + '_clean_lfp.mat'), 'r')
    
        # get channel_ids
        temp_ch_ids = np.asarray(lfp_matfile[device_label]['channel_ids'][:], dtype='uint32')
        temp_ch_ids = temp_ch_ids.T.view('U1')
        channel_ids = np.asarray([''.join(x).strip() for x in temp_ch_ids])
        
        # get shank_ids in array
        shank_ids = lfp_matfile[device_label]['shank_ids'][:].flatten()
        
        # Code to get depths ids in array
        depths = lfp_matfile[device_label]['depths'][:].flatten()
        depths = (device_metadata['Depth']*1000 - depths) * np.cos(math.radians(device_metadata['roll']))
        
        hemisphere = device_metadata['hemisphere']
        
        unique_shanks = np.unique(shank_ids).tolist()
        
        #TODO: Resolve brain area later
        for iShank in unique_shanks:
            electrode_group = nwbfile.create_electrode_group(
                name="{}.shank{}".format(device_label,iShank),
                description="electrode group for shank {} on {}".format(iShank, device_label),
                device=device,
                location="brain area",
            )
            # add electrodes to the electrode table
            for ielec,elec in enumerate(np.where(shank_ids == iShank)[0]):
                nwbfile.add_electrode(group=electrode_group, label = channel_ids[elec], \
                    depth=depths[elec], hemisphere=hemisphere, location="brain area")
                

    
def add_lfp_data_to_nwb(session_dir, nwbfile, session_metadata, device_labels):
    ''' 
    Function to add LFP traces to the NWB file.
    '''
    sess_dir = Path(session_dir)
    lfp_fs = 0 # Assumes that this gets overwritten and also that all devices have the same fs
    lfp_tvec = 0 # Assumes that this gets overwritten and also that all devices have the same tvec
    lfp_data = []
    electrode_counter = 0
    lfp_channel_ids = []
    for device_label in device_labels:
    # Determine whether probe1 or probe2 is imec0
        if session_metadata['probe1_ID'] == 'device_label':
            device_key = 'probe1'
        else:
            device_key ='probe2'

        device_metadata = {}
        for key in session_metadata:
            if device_key in key and 'ID' not in key:
                device_metadata[key.split('_')[-1]] = session_metadata[key]
        
        lfp_matfile = h5py.File(os.path.join(sess_dir, device_label + '_clean_lfp.mat'), 'r')
        
        # Reading and parsing the .mat file to create the electrode table
        temp_ch_ids = np.asarray(lfp_matfile[device_label]['channel_ids'][:], dtype='uint32')
        temp_ch_ids = temp_ch_ids.T.view('U1')
        channel_ids = np.asarray([''.join(x).strip() for x in temp_ch_ids])
        lfp_channel_ids.extend(channel_ids.tolist())
        electrode_counter += channel_ids.shape[0]
                
        lfp_fs = lfp_matfile[device_label]['lfp_fs'][:].flatten()[0]
        
        # Code to get lfp_tvec in array
        lfp_tvec = lfp_matfile[device_label]['lfp_tvec'][:].flatten()
                               
        # Code to get lfp_traces in array
        this_data = lfp_matfile[device_label]['lfp_traces'][:]
        # Transpose this if dimensions are not correct
        if this_data.shape[1] != channel_ids.shape[0]:
            this_data = np.transpose(this_data)
        lfp_data.append(this_data)
     
    # Create LFP table
    nwb_channel_ids = _get_electrodes_table_global_ids(nwbfile)
    lfp_channel_ids = [x.strip() for x in lfp_channel_ids]
    nwb_table_indices = _match_indices(nwb_channel_ids,lfp_channel_ids)
    lfp_table = nwbfile.create_electrode_table_region(\
        region=nwb_table_indices,  # reference row indices in the electrode table corresponding to the lfp table
        description="LFP electrodes")   
    
    if len(lfp_data) > 1:
        lfp_data = np.concatenate(lfp_data, axis=1)
    else:
        lfp_data = np.asarray(lfp_data[0]).squeeze()

    lfp_es = ElectricalSeries(name='LFP', data=H5DataIO(lfp_data, compression=True), electrodes=lfp_table, rate=lfp_fs, \
        starting_time=lfp_tvec[0], description = "Raw data subsampled  2500 Hz and bandpass filtered in the range 1-400 Hz")
    # To save without compression, try the line below
    # lfp_es = ElectricalSeries(name='LFP', data=lfp_data, electrodes=lfp_table, rate=lfp_fs, starting_time=lfp_tvec[0])
    lfp_module = nwbfile.create_processing_module(
        name="ecephys", description="LFP data obtained from rawdata"
    )
    lfp_module.add(lfp_es)
    
def _match_indices(electrode_table_channel_ids, matfile_channel_ids):
    # Initialize the result list with None values
    result = [None] * len(matfile_channel_ids)
    
    # Create a dictionary to map (imec_num, ap_num) pairs to indices in electrode_table_channel_ids
    x_map = {}
    for i, x_item in enumerate(electrode_table_channel_ids):
        # Extract the AP number from strings like 'AP200_NeuropixelsImec0Shank2'
        parts = x_item.split('_')
        ap_num = parts[0].replace('AP', '')
        
        # Extract the imec number from 'NeuropixelsImec0Shank2'
        if len(parts) > 1 and 'Imec' in parts[1]:
            imec_str = parts[1]
            imec_num = imec_str[imec_str.index('Imec')+4:imec_str.index('Shank')]
            key = (imec_num, ap_num)
            x_map[key] = i
    
    # For each item in matfile_channel_ids, find the matching index in electrode_table_channel_ids
    for j, y_item in enumerate(matfile_channel_ids):
        # Extract the imec number from strings like 'imec0.ap#AP200'
        imec_part = y_item.split('.')[0]
        imec_num = imec_part.replace('imec', '')
        
        # Extract the AP number
        ap_num = y_item.split('#AP')[1]
        
        # Look up this (imec_num, ap_num) pair in our map
        key = (imec_num, ap_num)
        if key in x_map:
            result[j] = x_map[key]
    
    return result