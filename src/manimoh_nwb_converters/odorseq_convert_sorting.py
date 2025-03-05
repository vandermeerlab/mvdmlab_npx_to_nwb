"""Various functions to help convert spike-sorted and curated mvdmlab NPX spiking data to NWB format."""

import scipy.io as sio
import numpy as np
import math
import os
from pathlib import Path

def add_sorting_electrodes_to_nwb(session_dir, nwbfile, session_metadata, device_labels):
    '''
    Function to add electrodes and devices that 
    '''
    
    sess_dir = Path(session_dir)
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
        
        if device_label not in nwbfile.devices.keys():
            # TODO: Should the description be changed to something more standard?
            device = nwbfile.create_device(name=device_label, \
                description="4-shank NPX2.0 ", manufacturer="IMEC")
            
        # Reading and parsing the .mat file to add the electrodes that didn't exist in the electrode table before
        sorting_matfile = sio.loadmat(os.path.join(sess_dir, 'clean_units_' + device_label + '.mat'))
    
        # get channel_ids 
        if 'channel_ids' in sorting_matfile.keys():
            channel_ids = sorting_matfile['channel_ids']
        
        # get shank_ids in array
        shank_ids = sorting_matfile['shank_ids'].squeeze()
        
        # get depths ids in array
        depths = sorting_matfile['depths'].squeeze()
        depths = (device_metadata['Depth']*1000 - depths) * np.cos(math.radians(device_metadata['roll']))
        
        unique_shanks = np.unique(shank_ids).tolist() 
        
        for iShank in unique_shanks:
            this_shank_group = "{}.shank{}".format(device_label,iShank)
            # Add this shank to an electrode group if it doesn't already exist
            if this_shank_group not in nwbfile.electrode_groups.keys():
                electrode_group = nwbfile.create_electrode_group(
                    name="{}.shank{}".format(device_label,iShank),
                    description="electrode group for shank {} on {}".format(iShank, device_label),
                    device=device,
                    location="brain area", #TODO: Need to figure this out, should this be the same as depth
                )
            else:
                electrode_group = nwbfile.electrode_groups[this_shank_group]
                
            # Can't seemn to add electrodes properly during add_unit, so tabling this for now    
            # # add electrodes to the electrode table
            # for ielec,elec in enumerate(np.where(shank_ids == iShank)[0]):
            #     cur_channel_ids = nwbfile.electrodes.to_dataframe()['label'].values.tolist()
            #     if channel_ids[elec] not in cur_channel_ids:
            #         nwbfile.add_electrode(group=electrode_group, label = channel_ids[elec], \
            #             location="brain area",  #TODO: Need to figure this out, should this be the same as depth
            #         )

def add_sorting_data_to_nwb(session_dir, nwbfile, session_metadata, device_labels):
    '''
    Function to add spikesorting data to the NWB file.
    '''
    sess_dir = Path(session_dir)
    nwbfile.add_unit_column(name='depth', description='Depth of the unit from the surface of the brain')
    nwbfile.add_unit_column(name='hemisphere', description='Hemisphere of the brain where the unit was recorded')
    nwbfile.add_unit_column(name='global_id', description='ID to uniquely identify the unit')
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
        
        if device_label not in nwbfile.devices.keys():
            # TODO: Should the description be changed to something more standard?
            device = nwbfile.create_device(name=device_label, \
                description="4-shank NPX2.0 ", manufacturer="IMEC")
            
        # Reading and parsing the .mat file
        sorting_matfile = sio.loadmat(os.path.join(sess_dir, 'clean_units_' + device_label + '.mat'))
        
        # Get spike_times
        spike_trains = sorting_matfile['spike_train'].T
        
        # Get average waveform from the best channel
        all_wv = sorting_matfile['mean_waveforms'].squeeze()
        big_idx = [np.argmax(abs(np.max(all_wv[x], axis=1) - np.min(all_wv[x], axis=1))) for x in range(all_wv.shape[0])]
        big_wv = np.asarray([all_wv[x][y][:] for x,y in enumerate(big_idx)])
        # nwbfile.add_unit_column(name='mean_waveform', description='Mean waveform of the unit from the channel with the highest amplitude')
        
        # get channel_ids TODO: See if we need to get rid the 'imec0ap.AP#'
        if 'channel_ids' in sorting_matfile.keys(): 
            channel_ids = sorting_matfile['channel_ids']
            # nwbfile.add_unit_column(name='channel_id', description='Channel ID on which this neuron was best identified as per spikeinterface')
        
        # get shank_ids in array
        shank_ids = sorting_matfile['shank_ids'].squeeze()
        
        # get depths ids in array
        depths = sorting_matfile['depths'].squeeze()
        depths = (device_metadata['Depth']*1000 - depths) * np.cos(math.radians(device_metadata['roll']))
        
        this_hemi = device_metadata['hemisphere']
            
        # get unit_ids 
        unit_ids = sorting_matfile['unit_ids'].squeeze()
        
        for x in range(len(unit_ids)):
            this_shank_group = "{}.shank{}".format(device_label,shank_ids[x])
            this_electrode_group = nwbfile.electrode_groups[this_shank_group]
            this_id = this_shank_group+'.'+unit_ids[x].split('_')[-1]
            nwbfile.add_unit(spike_times=spike_trains[x][0].squeeze(), \
                waveform_mean = big_wv[x].T, \
                # id=this_id, \
                global_id=this_id, \
                electrode_group=this_electrode_group, \
                depth=depths[x], \
                hemisphere=this_hemi)
    
        
        # # Adding peak and valley amps is not simple as they are ragged arrays; skipping for now
        # # Add fields that are not present in every session
        # peak_amps, valley_amps = None, None
        # if 'peak_amp' in sorting_matfile.keys():
        #     if 'peak_amp' not in nwbfile.units.colnames:
        #         nwbfile.add_unit_column(name='peak_amp', description='Peak amplitude as calculated by spikeinterface')
        #     peak_amps = sorting_matfile['peak_amp'].squeeze()
        # if 'valley_amp' in sorting_matfile.keys():
        #     if 'valley_amp' not in nwbfile.units.colnames:
        #         nwbfile.add_unit_column(name='valley_amp', description='Valley amplitude as calculated by spikeinterface')
        #     valley_amps = sorting_matfile['valley_amp'].squeeze()
        
        # for x in range(len(unit_ids)):
        #     this_shank_group = "{}.shank{}".format(device_label,shank_ids[x])
        #     this_electrode_group = nwbfile.electrode_groups[this_shank_group]
        #     # this_id = int(unit_ids[x].split('_')[-1])
        #     this_id = this_shank_group+'.'+unit_ids[x].split('_')[-1]
        #     # cur_ch_list = nwbfile.electrodes.to_dataframe()['channel_id'].values
        #     # this_ch_idx = np.where(cur_ch_list == channel_ids[x])[0][0]
        #     if peak_amps is not None:        
        #         nwbfile.add_unit(spike_times=spike_trains[x][0].squeeze(), \
        #             waveform_mean = big_wv[x].T, \
        #             # id=this_id, \
        #             global_id=this_id, \
        #             electrode_group=this_electrode_group, \
        #             depth=depths[x], \
        #             hemisphere=this_hemi, \
        #             peak_amp=peak_amps[x], \
        #             valley_amp=valley_amps[x])    
        #     else:
        #         nwbfile.add_unit(spike_times=spike_trains[x][0].squeeze(), \
        #             waveform_mean = big_wv[x].T, \
        #             # id=this_id, \
        #             global_id=this_id, \
        #             electrode_group=this_electrode_group, \
        #             depth=depths[x], \
        #             hemisphere=this_hemi)
        