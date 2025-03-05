import manimoh_nwb_converters as mnc

input_dir = '/mnt/datasets/incoming/mvdm/OdorSequence/sourcedata/preprocessed/M541/M541-2024-08-31'
# output_nwb_filepath = '/mnt/datasets/incoming/mvdm/OdorSequence/sourcedata/preprocessed/M541/M541-2024-08-31/M541-2024-08-31.nwb'
output_nwb_filepath = '/home/manishm/test_metadata_M541-2024-08-31.nwb'
mnc.create_nwb_file(input_dir, output_nwb_filepath)
