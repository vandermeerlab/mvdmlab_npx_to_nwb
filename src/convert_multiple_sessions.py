import manimoh_nwb_converters as mnc
import os
from datetime import datetime
import warnings

def convert_multiple_sessions(directory_list):
    """
    Convert multiple directories of data to NWB format.
    
    Args:
        directory_list (list): List of input directory paths to process
    """
    for input_dir in directory_list:
        try:
            # Extract the date from the directory name (assuming format like 'M540-2024-08-20')
            dir_name = os.path.basename(input_dir)
            date_str = dir_name.split('-', 1)[1]  # Get everything after first dash
            
            # Construct output filepath in the same directory
            output_filename = f"test_{date_str}.nwb"
            output_nwb_filepath = os.path.join(input_dir, output_filename)
            
            # Run the conversion
            mnc.create_nwb_file(input_dir, output_nwb_filepath)
            
            print(f"Successfully processed: {input_dir}")
            
        except Exception as e:
            warnings.warn(f"Failed to process directory: {input_dir}\nError: {str(e)}")
            continue


directories = [
    'E:\\odor-pixels\\fromHector\\NoReward\\M489\\M489-2024-08-05',
    'E:\\odor-pixels\\fromHector\\NoReward\\M489\\M489-2024-08-07',
    'E:\\odor-pixels\\fromHector\\NoReward\\M489\\M489-2024-08-08',
    'E:\\odor-pixels\\fromHector\\NoReward\\M509\\M509-2024-09-10',
    'E:\\odor-pixels\\fromHector\\NoReward\\M509\\M509-2024-09-11',
    'E:\\odor-pixels\\fromHector\\NoReward\\M509\\M509-2024-09-12',
    'E:\\odor-pixels\\fromHector\\NoReward\\M509\\M509-2024-09-13',
    'E:\\odor-pixels\\fromHector\\NoReward\\M509\\M509-2024-08-31',
    'E:\\odor-pixels\\fromHector\\NoReward\\M541\\M541-2024-09-01',
    'E:\\odor-pixels\\fromHector\\NoReward\\M541\\M541-2024-09-02',
    'E:\\odor-pixels\\fromHector\\NoReward\\M541\\M541-2024-09-02',
    'E:\\odor-pixels\\fromHector\\NoReward\\M541\\M541-2024-09-04',
    'E:\\odor-pixels\\fromHector\\NoReward\\M541\\M541-2024-09-05',  
    # Add more directories as needed
]

convert_multiple_sessions(directories)