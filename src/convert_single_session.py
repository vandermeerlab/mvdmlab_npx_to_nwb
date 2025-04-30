#!/usr/bin/env python3
# import manimoh_nwb_converters as mnc

# raw_session_dir = '/mnt/datasets/incoming/mvdm/OdorSequence/sourcedata/raw/M541/M541-2024-08-31_g0'
# preprocessed_session_dir = '/mnt/datasets/incoming/mvdm/OdorSequence/sourcedata/preprocessed/M541/M541-2024-08-31'

# # output_nwb_filepath = '/mnt/datasets/incoming/mvdm/OdorSequence/sourcedata/preprocessed/M541/M541-2024-08-31/M541-2024-08-31.nwb'
# output_nwb_filepath = '/home/manishm/M541-2024-08-31.nwb'
# mnc.create_nwb_file(raw_session_dir, preprocessed_session_dir, output_nwb_filepath)
#!/usr/bin/env python3
import argparse
import os
import sys
import manimoh_nwb_converters as mnc

def parse_text_file(filename):
    """Parse a text file containing parameters."""
    try:
        with open(filename, 'r') as f:
            params = f.read().strip().split()
            
        # Ensure we have at least 2 parameters
        if len(params) < 2:
            print(f"Error: Text file {filename} must contain at least 2 parameters.")
            sys.exit(1)
            
        raw_dir = params[0]
        preprocessed_dir = params[1]
        output_filepath = params[2] if len(params) >= 3 else None
        
        return raw_dir, preprocessed_dir, output_filepath
    except FileNotFoundError:
        print(f"Error: Text file {filename} not found.")
        sys.exit(1)
    except Exception as e:
        print(f"Error parsing text file: {str(e)}")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description='Create NWB file from session data')
    
    # Create a mutually exclusive group for input methods
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument('-f', '--file', help='Text file containing parameters (raw_dir, preprocessed_dir, [output_path])')
    input_group.add_argument('-r', '--raw', help='Raw session directory')
    
    # Only required if using command line arguments instead of file
    parser.add_argument('-p', '--preprocessed', help='Preprocessed session directory')
    parser.add_argument('-o', '--output', help='Output NWB filepath (optional)')
    
    args = parser.parse_args()
    
    # Get parameters from either text file or command line
    if args.file:
        raw_dir, preprocessed_dir, output_filepath = parse_text_file(args.file)
    else:
        # Ensure preprocessed directory is provided if using command line args
        if not args.preprocessed:
            print("Error: Preprocessed directory (-p/--preprocessed) is required when using command line arguments.")
            sys.exit(1)
            
        raw_dir = args.raw
        preprocessed_dir = args.preprocessed
        output_filepath = args.output
    
    # Validate directories
    if not os.path.isdir(raw_dir):
        print(f"Error: Raw session directory does not exist: {raw_dir}")
        sys.exit(1)
        
    if not os.path.isdir(preprocessed_dir):
        print(f"Error: Preprocessed session directory does not exist: {preprocessed_dir}")
        sys.exit(1)
    
    # If output_filepath is not provided, generate it from the preprocessed directory
    if not output_filepath:
        folder_name = os.path.basename(preprocessed_dir)
        output_filepath = os.path.join(preprocessed_dir, f"{folder_name}.nwb")
        print(f"No output path specified. Using: {output_filepath}")
    
    # Create the NWB file
    try:
        print(f"Creating NWB file with:")
        print(f"  Raw directory: {raw_dir}")
        print(f"  Preprocessed directory: {preprocessed_dir}")
        print(f"  Output filepath: {output_filepath}")
        
        mnc.create_nwb_file(raw_dir, preprocessed_dir, output_filepath)
        print(f"Successfully created NWB file: {output_filepath}")
    except Exception as e:
        print(f"Error creating NWB file: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
    
# Usage examples
# python convert_single_session.py --raw /path/to/raw_dir --preprocessed /path/to/preprocessed_dir [--output /path/to/output.nwb]
# OR
# python convert_single_session.py --file params.txt
# where params.txt contains
# /path/to/raw_dir /path/to/preprocessed_dir [/path/to/output.nwb]
