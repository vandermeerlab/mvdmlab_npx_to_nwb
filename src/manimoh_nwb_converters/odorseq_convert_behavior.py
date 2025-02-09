"""Various functions to help convert preprocessed mvdmlab behavioral and stimuli control data to NWB format."""
import numpy as np
import os
import pandas as pd
from pathlib import Path

from pynwb.epoch import TimeIntervals

def add_intervals_to_nwb(session_dir, nwbfile, session_metadata):
    '''
    Function to add intervals to the NWB file
    '''
    # Code to add odor presentation times
    sess_dir = Path(session_dir)
    odor_ids = ['A', 'B', 'C', 'D', 'E', 'F', 'G']
    for oid in odor_ids:
        fname = 'odor{}_channel'.format(oid)
        cname = session_metadata[fname]
        on_fname = os.path.join(sess_dir, "{}_ON.txt".format(cname))
        off_fname = os.path.join(sess_dir, "{}_OFF.txt".format(cname))
        if os.path.exists(on_fname) and os.path.getsize(on_fname) != 0:
            this_on_times = np.asarray(pd.read_csv(on_fname, header=None)).squeeze()
            this_off_times = np.asarray(pd.read_csv(off_fname, header=None)).squeeze()
            # Clean up the on and off times
            # print('Cleaning up ON and OFF times for Odor {}'.format(oid))
            clean_on, clean_off= match_on_off_times(this_on_times, this_off_times)
            this_on = TimeIntervals(name = "Odor {} ON".format(oid), \
                description = "Intervals when Odor {} was being presented".format(oid))
            for x in range(len(clean_on)):
                this_on.add_row(start_time= clean_on[x], stop_time = clean_off[x])
            nwbfile.add_time_intervals(this_on)
    # Code to add block start and end times
    block_ids = [1,2,3]
    # Some code to add ExpKeys for blocks
    for bid in block_ids:
        this_block = "block{}".format(bid)
        if np.any([this_block in x for x in session_metadata]):
            this_interval = TimeIntervals(name = "Block {}".format(bid), \
                description = "Interval when Block {} odors were being presented".format(bid))
            this_interval.add_row(start_time= session_metadata["block{}start".format(bid)], \
                stop_time = session_metadata["block{}end".format(bid)])
            nwbfile.add_time_intervals(this_interval)


def match_on_off_times(on_times, off_times, expected_delay=2.0, tolerance=0.25):
    """
    Match ON and OFF times ensuring they occur in pairs approximately 2 seconds apart.
    
    Parameters:
    -----------
    on_times : np.ndarray
        Array of ON event timestamps
    off_times : np.ndarray
        Array of OFF event timestamps
    expected_delay : float, optional
        Expected time difference between ON and OFF events (default: 2.0 seconds)
    tolerance : float, optional
        Allowable deviation from expected_delay (default: 0.25 seconds)
        
    Returns:
    --------
    tuple: (matched_on_times, matched_off_times)
        Arrays of matched ON and OFF times
    """
    # Initialize lists to store matched pairs
    matched_on = []
    matched_off = []
    
    # Sort arrays to ensure temporal order
    on_times = np.sort(on_times)
    off_times = np.sort(off_times)
    
    # For each ON time, find matching OFF time
    for on_time in on_times:
        # Calculate time differences with all OFF times
        time_diffs = off_times - on_time
        
        # Find OFF times that occur after this ON time
        valid_offs = time_diffs[time_diffs > 0]
        
        if len(valid_offs) > 0:
            # Find the time difference closest to expected_delay
            closest_diff_idx = np.argmin(np.abs(valid_offs - expected_delay))
            closest_diff = valid_offs[closest_diff_idx]
            
            # Check if within tolerance
            if abs(closest_diff - expected_delay) <= tolerance:
                matched_on.append(on_time)
                matched_off.append(on_time + closest_diff)
        #     else:
        #         print("OFF time {} deviates from expected delay for ON time: {}".format(on_time + closest_diff, on_time))
        # else:
        #     # print("No matching OFF time found for ON time: {}".format(on_time))
    
    return np.array(matched_on), np.array(matched_off)

