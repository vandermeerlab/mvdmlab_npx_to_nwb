"""Various functions to help convert preprocessed mvdmlab behavioral and stimuli control data to NWB format."""
import numpy as np
import os
import pandas as pd
from pathlib import Path

from pynwb.epoch import TimeIntervals
from hdmf.common import VectorData

def add_intervals_to_nwb(session_dir, nwbfile, session_metadata):
    '''
    Function to add TTL-derived event intervals to the NWB file.

    Any ExpKeys field ending in "_channel" (e.g. odorB_channel = "XA1", airPuff_channel = "XD5",
    cameraFrames_channel = "XD6") is treated as a candidate event channel: if matching
    "<channel>_ON.txt" / "<channel>_OFF.txt" files exist in the session directory, they are
    added as a TimeIntervals table named after the ExpKeys field. Which events exist is therefore
    driven entirely by what's present in ExpKeys and the session directory, not a hardcoded list.

    ON/OFF pairing makes no assumption about pulse duration (odor presentations run for seconds,
    an air puff for a fraction of a second, a camera frame-sync pulse shorter still) -- see
    pair_on_off_times.
    '''
    sess_dir = Path(session_dir)

    # Map raw channel name (e.g. "XA1") -> event label (e.g. "odorB"), from any ExpKeys "*_channel" field
    channel_to_label = {}
    for key, value in session_metadata.items():
        if key.endswith('_channel'):
            channel_to_label[value] = key[:-len('_channel')]

    for cname, label in channel_to_label.items():
        on_fname = os.path.join(sess_dir, "{}_ON.txt".format(cname))
        off_fname = os.path.join(sess_dir, "{}_OFF.txt".format(cname))
        if not (os.path.exists(on_fname) and os.path.getsize(on_fname) != 0):
            continue
        if not (os.path.exists(off_fname) and os.path.getsize(off_fname) != 0):
            continue

        this_on_times = np.asarray(pd.read_csv(on_fname, header=None)).squeeze()
        this_off_times = np.asarray(pd.read_csv(off_fname, header=None)).squeeze()

        clean_on, clean_off = pair_on_off_times(this_on_times, this_off_times)

        # Build columns in bulk instead of calling add_row per event -- for a dense channel
        # like a camera frame-sync line (tens of thousands of events), add_row's per-call
        # overhead makes a row-by-row loop take minutes; this is effectively instant.
        start_col = VectorData(name='start_time', description='Start time of interval, in seconds', data=clean_on)
        stop_col = VectorData(name='stop_time', description='Stop time of interval, in seconds', data=clean_off)
        this_interval = TimeIntervals(name = label, \
            description = "Intervals when {} was ON".format(label), \
            columns=[start_col, stop_col])
        nwbfile.add_time_intervals(this_interval)
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


def pair_on_off_times(on_times, off_times):
    """
    Pair each ON time with the next OFF time that follows it, with no assumption about
    how long the pulse lasts -- this must work for an odor presentation (seconds), an
    air puff (a fraction of a second), and a camera frame-sync pulse (shorter still).

    An ON time is dropped if no OFF time falls between it and the next ON time (i.e. the
    pulse never went low before the next one started).

    on_times and off_times are each assumed to already be sorted ascending, as recorded.
    Matching is fully vectorized (via searchsorted) rather than looping in Python, since a
    frame-sync channel can have tens of thousands of events.

    Parameters:
    -----------
    on_times : np.ndarray
        Array of ON event timestamps, sorted ascending
    off_times : np.ndarray
        Array of OFF event timestamps, sorted ascending

    Returns:
    --------
    tuple: (matched_on_times, matched_off_times)
        Arrays of matched ON and OFF times
    """
    on_times = np.atleast_1d(on_times)
    off_times = np.atleast_1d(off_times)

    if on_times.size == 0 or off_times.size == 0:
        return np.array([]), np.array([])

    # For each ON time, the index of the first OFF time strictly after it
    idx = np.searchsorted(off_times, on_times, side='right')
    valid = idx < off_times.size
    off_candidate = np.where(valid, off_times[np.clip(idx, 0, off_times.size - 1)], np.inf)

    # Drop an ON time if its candidate OFF only occurs after the next ON has already started
    next_on = np.append(on_times[1:], np.inf)
    keep = valid & (off_candidate < next_on)

    return on_times[keep], off_candidate[keep]

