import os
import re

def parse_expkeys(directory):
    """
    Find and parse an ExpKeys file from a directory.
    
    Args:
        directory (str): Path to the directory containing the ExpKeys file
        
    Returns:
        dict: Dictionary containing the parsed ExpKeys values
        
    Raises:
        ValueError: If no ExpKeys file is found or if multiple ExpKeys files are found
    """
    # Find all files ending with 'keys.m'
    keys_files = [f for f in os.listdir(directory) if f.endswith('keys.m')]
    
    # Check number of files found
    if len(keys_files) == 0:
        raise ValueError(f"No ExpKeys exist in {directory}")
    elif len(keys_files) > 1:
        raise ValueError(f"Multiple ExpKeys exist in {directory}")
        
    # Process the single found file
    filename = os.path.join(directory, keys_files[0])
    expkeys = {}
    
    with open(filename, 'r') as f:
        lines = f.readlines()
    
    for line in lines:
        # Skip commented lines
        if line.strip().startswith('%'):
            continue
            
        # Look for lines containing 'ExpKeys.'
        if 'ExpKeys.' in line:
            # Split only on first occurrence of '='
            parts = line.split('=', 1)
            if len(parts) != 2:
                continue
                
            # Get key (remove 'ExpKeys.' and strip whitespace)
            key = parts[0].replace('ExpKeys.', '').strip()
            
            # Get value (remove comments and strip whitespace/semicolon)
            value = parts[1].split('%')[0].strip().rstrip(';').strip()
            
            # Handle empty strings
            if value == '""' or value == "''":
                expkeys[key] = None
                continue
            
            # Handle quoted strings (both single and double quotes)
            if (value.startswith('"') and value.endswith('"')) or \
               (value.startswith("'") and value.endswith("'")):
                expkeys[key] = value[1:-1]
                continue
            
            # Handle cell arrays (like {'UE', 'Odor A', 'Odor B', 'Odor C'})
            if value.startswith('{') and value.endswith('}'):
                # Extract strings between quotes, handle both single and double quotes
                cell_values = re.findall(r'["\']([^"\']*)["\']', value)
                expkeys[key] = cell_values
                continue
            
            # Try to convert to float for numerical values
            try:
                expkeys[key] = float(value)
            except ValueError:
                # If conversion fails, store as string
                expkeys[key] = value
    
    # Some manual cleanup_steps
    if "Manish" in expkeys['experimenter']:
        expkeys['experimenter'] = "Mohapatra, Manish"
    elif "Kyoko" in expkeys['experimenter']:
        expkeys['experimenter'] = "Leaman, Kyoko R."
    elif "Mimi" in expkeys['experimenter']:
        expkeys['experimenter'] = "Janssen, Mimi"
    else :
        expkeys['experimenter'] = "Leaman, Kyoko R."
    return expkeys