import re

from ndx_mvdmlab_metadata import (
    LabMetaDataExtension, 
    ProbeExtension, 
    OdorantInfoExtension, 
    ExperimentalBlockExtension, 
    PreprocessedAnnotationExtension
)

def add_lab_metadata_to_nwb(nwbfile, session_metadata):
    '''
    Function to add lab-specific metadata to the NWB file.
    '''
    # Create probe extension for probe 1
    probe1_extension = None
    if 'probe1_ID' in session_metadata:
        probe1_metadata = {}
        for key in session_metadata:
            if 'probe1_' in key and 'ID' not in key and 'location' not in key:
                if 'Depth' not in key:
                    probe1_metadata[key.split('_')[-1]] = session_metadata[key]
                else:
                    probe1_metadata['depth'] = session_metadata[key]

        probe1_extension = ProbeExtension(
            name='probe1',
            ID=session_metadata.get('probe1_ID'),
            **probe1_metadata
        )

    # Create probe extension for probe 2 (if exists)
    probe2_extension = None
    if 'probe2_ID' in session_metadata:
        probe2_metadata = {}
        for key in session_metadata:
            if 'probe2_' in key and 'ID' not in key and 'location' not in key:
                if 'Depth' not in key:
                    probe2_metadata[key.split('_')[-1]] = session_metadata[key]
                else:
                    probe2_metadata['depth'] = session_metadata[key]
        
        probe2_extension = ProbeExtension(
            name='probe2',
            ID=session_metadata.get('probe2_ID'),
            **probe2_metadata
        )

    # Create odorant info extension
    odorant_info = {}
    for odor in ['A', 'B', 'C', 'D', 'E', 'F', 'G']:
        odor_field = f'odor{odor}'
        if odor_field in session_metadata:
            key = f'Odor {odor}'
            odorant_info[key] = session_metadata[odor_field]
    
    odorant_info_extension = None
    if odorant_info:
        odorant_info_extension = OdorantInfoExtension(
            name='odorant_info',
            **odorant_info
        )

    # Create experimental block extension
    block_info = {}
    for block in [1, 2, 3]:
        block_type_field = f'block{block}_type'
        if block_type_field in session_metadata:
            block_info[block_type_field] = ','.join(session_metadata[block_type_field])
    
    block_info_extension = None
    if block_info:
        block_info_extension = ExperimentalBlockExtension(
            name='block_info',
            **block_info
        )

    # Create preprocessed annotation extension
    preprocessed_annotations = {}
    
    # Pattern for matching SWR and control channel metadata
    annotation_patterns = [
        r'imec(\d+)_shank(\d+)_SWR_channel',
        r'imec(\d+)_best_SWR_channel',
        r'imec(\d+)_best_control_channel'
    ]
    
    # Find all keys in session_metadata that match our patterns
    for key in session_metadata:
        for pattern in annotation_patterns:
            if re.match(pattern, key):
                preprocessed_annotations[key] = session_metadata[key]
                break
    
    annotation_extension = None
    if preprocessed_annotations:
        annotation_extension = PreprocessedAnnotationExtension(
            name='preprocessed_annotations',
            **preprocessed_annotations
        )

    # Prepare the metadata dictionary for LabMetaDataExtension
    lab_metadata_dict = {
        'name': 'LabMetaData',
    }
    
    # Add probes if they exist
    if probe1_extension:
        lab_metadata_dict['probe1'] = probe1_extension
    
    if probe2_extension:
        lab_metadata_dict['probe2'] = probe2_extension
    
    # Add other extensions if they exist
    if odorant_info_extension:
        lab_metadata_dict['odorant_info'] = odorant_info_extension
    
    if block_info_extension:
        lab_metadata_dict['block_info'] = block_info_extension
    
    if annotation_extension:
        lab_metadata_dict['preprocessed_annotations'] = annotation_extension

    # Populate metadata extension 
    lab_metadata = LabMetaDataExtension(**lab_metadata_dict)

    # Add to file
    nwbfile.add_lab_meta_data(lab_metadata)