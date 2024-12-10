"""Primary script for converting preprocessed mvdmlab NPX LFP data to NWB format."""

import h5py
import numpy as np
import math
from hdmf.backends.hdf5.h5_utils import H5DataIO

from pynwb.ecephys import ElectricalSeries, LFP

def add_lfp_electrodes_to_nwb(session_dir, nwbfile, session_metadata, device_labels):
    '''
    Function to add LFP electrodes and probe information to the NWB file.
    '''
    electrode_counter = 0
    # Add electrode column to nwb file (This will get poulated later)
    nwbfile.add_electrode_column(name="channel_id", description="Identifier for the channel on the probe")
    
    for device_label in device_labels:
    # Determine whether probe1 or probe2 is imec0s
        if session_metadata['probe1_ID'] == 'device_label':
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
        lfp_matfile = h5py.File(session_dir + '\\' + device_label + '_clean_lfp.mat', 'r')
    
        # get channel_ids TODO: See if we need to get rid the 'imec0ap.AP#' 
        temp_ch_ids = np.asarray(lfp_matfile[device_label]['channel_ids'][:], dtype='uint32')
        temp_ch_ids = temp_ch_ids.T.view('U1')
        channel_ids = np.asarray([''.join(x).strip() for x in temp_ch_ids])
        
        # get shank_ids in array
        shank_ids = lfp_matfile[device_label]['shank_ids'][:].flatten()
        
        # Code to get depths ids in array
        depths = lfp_matfile[device_label]['depths'][:].flatten()
        depths = (device_metadata['Depth']*1000 - depths) * np.cos(math.radians(device_metadata['roll']))
        
        
        unique_shanks = np.unique(shank_ids).tolist()
        
        for iShank in unique_shanks:
            electrode_group = nwbfile.create_electrode_group(
                name="{}.shank{}".format(device_label,iShank),
                description="electrode group for shank {} on {}".format(iShank, device_label),
                device=device,
                location="brain area", # Need to figure this out, should this be the same as depth
            )
            # add electrodes to the electrode table
            for ielec,elec in enumerate(np.where(shank_ids == iShank)[0]):
                # print
                nwbfile.add_electrode(group=electrode_group, channel_id = channel_ids[elec], \
                    location="brain area",  # Need to figure this out, should this be the same as depth
                )
                electrode_counter += 1
                

    
def add_lfp_data_to_nwb(session_dir, nwbfile, session_metadata, device_labels):
    
    lfp_fs = 0 # Assumes that this gets overwritten and also that all devices have the same fs
    lfp_tvec = 0 # Assumes that this gets overwritten and also that all devices have the same tvec
    lfp_data = []
    electrode_counter = 0
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
        
        lfp_matfile = h5py.File(session_dir + '\\' + device_label + '_clean_lfp.mat', 'r')
        
        # Reading and parsing the .mat file to create the electrode table
        temp_ch_ids = np.asarray(lfp_matfile[device_label]['channel_ids'][:], dtype='uint32')
        temp_ch_ids = temp_ch_ids.T.view('U1')
        channel_ids = np.asarray([''.join(x).strip() for x in temp_ch_ids])
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
    lfp_table = nwbfile.create_electrode_table_region(\
        region=list(range(electrode_counter)),  # reference row indices 0 to N-1\
        description="LFP electrodes")   
    
    if len(lfp_data) > 1:
        lfp_data = np.concatenate(lfp_data, axis=1)
    else:
        lfp_data = np.asarray(lfp_data[0]).squeeze()

    # The compression stuff doesn't work yet (the output NWB file is smaller but can't be validated or read by NWBinspector)
    # lfp_es = ElectricalSeries(name='LFP', data=H5DataIO(lfp_data, compression=True), electrodes=lfp_table, rate=lfp_fs, starting_time=lfp_tvec[0])
    lfp_es = ElectricalSeries(name='LFP', data=lfp_data, electrodes=lfp_table, rate=lfp_fs, starting_time=lfp_tvec[0])
    lfp_module = nwbfile.create_processing_module(
        name="ecephys", description="LFP data subsampled at 2500 Hz and bandpass filtered in the range 1-400 Hz "
    )
    lfp_module.add(lfp_es)