import os
import sys

# ===== SCRIPT DESCRIPTION =====
# This script creates Windows batch (.bat) alias files for virtual environments
# in the project. These aliases make it easier to activate environments with a simple command.
# When executed, it will create a 'bat' folder with activation scripts for each environment.
# 
# The script can be used in two ways:
# 1. Standalone execution: Creates aliases for all virtual environments
# 2. Function import: Can be imported and used to create an alias for a specific environment

# ===== CONFIGURATION =====
# Whether to open a new terminal window when activating an environment
# - True: Opens a new terminal window with the environment activated
# - False: Activates the environment in the current terminal
open_in_new_terminal = False

def create_venv_alias(venv_name=None, base_dir=None):
    """
    Create a batch file alias for a virtual environment.
    
    Args:
        venv_name (str, optional): Name of the specific virtual environment to create an alias for.
                                   If None, creates aliases for all environments.
        base_dir (str, optional): Base directory of the project. If None, uses the current directory.
                                 
    Returns:
        str: Path to the created alias file, or None if no alias was created
    """
    # Use provided base directory or get the current directory
    current_directory = base_dir if base_dir else os.getcwd()
    
    # Path to the folder containing all virtual environments
    venv_root = os.path.join(current_directory, "venv", "environments")
    # Directory where .bat alias files will be saved
    alias_output_dir = os.path.join(current_directory, "bat")
    
    # Create the bat directory if it doesn't exist
    os.makedirs(alias_output_dir, exist_ok=True)
    
    # Function to create a single alias file
    def create_single_alias(env_name):
        # Get the full path to the virtual environment
        venv_path = os.path.join(venv_root, env_name)
        # Path to the activation script for this environment
        activate_bat = os.path.join(venv_path, "Scripts", "activate.bat")
        
        # Only create aliases for valid virtual environments with activation scripts
        if os.path.isdir(venv_path) and os.path.isfile(activate_bat):
            # Define the alias filename and full path
            alias_file = f"activate_{env_name}.bat"
            alias_path = os.path.join(alias_output_dir, alias_file)
            
            # Create the .bat file with appropriate commands
            with open(alias_path, "w") as f:
                # Disable command echo in the batch file
                f.write("@echo off\n")
                if open_in_new_terminal:
                    # Open a new terminal window and activate the environment
                    f.write(f'start cmd /k call "{activate_bat}"\n')
                else:
                    # Activate the environment in the current terminal
                    f.write(f'call "{activate_bat}"\n')
            
            print(f"✅ Alias created: {alias_file}")
            return alias_path
        else:
            print(f"⚠️ Warning: Environment '{env_name}' does not exist or is not valid.")
            return None
    
    # If a specific environment name is provided, create an alias only for that environment
    if venv_name:
        return create_single_alias(venv_name)
    # Otherwise, create aliases for all environments
    else:
        created_aliases = []
        for env_name in os.listdir(venv_root):
            alias_path = create_single_alias(env_name)
            if alias_path:
                created_aliases.append(alias_path)
        
        # Summary message showing where all the alias files were saved
        if created_aliases:
            print(f"\n📁 All alias scripts saved in: {alias_output_dir}")
            print("Use these .bat files to quickly activate your virtual environments.")
        return created_aliases

# Execute as standalone script
if __name__ == '__main__':
    # Check if an environment name was provided as a command-line argument
    if len(sys.argv) > 1:
        venv_name = sys.argv[1]
        create_venv_alias(venv_name)
    else:
        # Create aliases for all environments
        create_venv_alias()
