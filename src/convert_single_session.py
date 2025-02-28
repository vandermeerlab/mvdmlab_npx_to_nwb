import manimoh_nwb_converters as mnc

input_dir = 'E:\\odor-pixels\\fromHector\\NoReward\\M541\\M541-2024-08-31'
output_nwb_filepath = 'E:\\odor-pixels\\fromHector\\NoReward\\M541\\M541-2024-08-31\\test_2024-08-31.nwb'
mnc.create_nwb_file(input_dir, output_nwb_filepath, overwrite=True)