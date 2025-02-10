import manimoh_nwb_converters as mnc

input_dir = 'E:\\odor-pixels\\fromHector\\NoReward\\M540\\M540-2024-08-20'
output_nwb_filepath = 'E:\\odor-pixels\\fromHector\\NoReward\\M540\\M540-2024-08-20\\test_2024-08-20.nwb'
mnc.create_nwb_file(input_dir, output_nwb_filepath)