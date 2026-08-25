import manimoh_nwb_converters as mnc

input_dir = 'E:\\npx_quadprobe\\LC_Pilot\\preprocessed'
output_nwb_filepath = 'E:\\npx_quadprobe\\LC_Pilot\\preprocessed\\MM019_2026_08_15.nwb'
mnc.create_nwb_file(input_dir, output_nwb_filepath, add_lfp=False)