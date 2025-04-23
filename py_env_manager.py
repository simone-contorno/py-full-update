import os
import subprocess
import sys
import venv

# Get current folder absolute path
PARENT_FOLDER = os.path.abspath(os.path.dirname(__file__))
FOLDER = PARENT_FOLDER + "\\venv"
ENV = FOLDER + "\\environments"
REQ = FOLDER + "\\requirements"

def create_virtualenv(env_name):
    """Create a new virtual environment and generate a bat alias for it."""

    env_path = os.path.join(ENV, env_name)
    if os.path.exists(env_path):
        print(f"The environment '{env_name}' already exists.")
    else:
        print(f"Creating the virtual environment '{env_name}'...")
        venv.create(env_path, with_pip=True)
        print(f"The environment '{env_name}' has been successfully created!")
        
        # Create a bat alias for the new environment
        try:
            from create_venv_alias import create_venv_alias
            alias_path = create_venv_alias(env_name, os.getcwd())
            if alias_path:
                print(f"Created activation alias: {os.path.basename(alias_path)}")
        except ImportError:
            print("Note: Could not create bat alias (create_venv_alias.py not found)")
        except Exception as e:
            print(f"Note: Could not create bat alias: {str(e)}")

def activate_virtualenv(env_name):
    """Generate the command to activate a virtual environment."""

    env_path = os.path.join(ENV, env_name)
    if os.name == 'nt':  # Windows
        activate_script = os.path.join(env_path, 'Scripts', 'activate')
    else:  # macOS/Linux
        activate_script = os.path.join(env_path, 'bin', 'activate')

    if os.path.exists(activate_script):
        print(f"To activate the environment '{env_name}', run the following command:")
        print(f"source {activate_script} (on macOS/Linux) or {activate_script} (on Windows)")
    else:
        print(f"The virtual environment '{env_name}' was not found.")

def deactivate_virtualenv():
    """Deactivate the currently active virtual environment."""
    print("To deactivate the active virtual environment, run 'deactivate' in the terminal.")
    # The "deactivate" command is already available once the environment is activated.

def install_requirements(env_src, env_dst):
    """Install dependencies from a requirements.txt file."""

    env_path = os.path.join(ENV, env_src)
    if not os.path.exists(env_path):
        print(f"The environment '{env_src}' does not exist.")
        return

    # Check for requirements file in the requirements directory
    file = f"requirements_{env_src}.txt"
    req_path = os.path.join(REQ, file)
    if not os.path.exists(req_path):
        # Create the file
        with open(req_path, 'w') as f:
            f.write("")
        print(f"Created '{file}' file.")
        return
    
    # Check if the requirements file is empty
    with open(req_path, 'r') as f:
        if not f.read().strip():
            print(f"The requirements file '{file}' is empty.")
            return

    if os.path.exists(req_path):
        print(f"Installing dependencies from '{file}'...")
        # Determine the pip path based on OS
        env_dst_path = os.path.join(ENV, env_dst)
        if not os.path.exists(env_dst_path):
            print(f"The environment '{env_dst}' does not exist.")
            res = input("Do you want to create it? (Y/n): ")
            if res.lower() != 'n':
                create_virtualenv(env_dst)
            else:
                return

        if os.name == 'nt':  # Windows
            pip_path = os.path.join(env_dst_path, 'Scripts', 'pip.exe')
        else:  # macOS/Linux
            pip_path = os.path.join(env_dst_path, 'bin', 'pip.exe')
        
        subprocess.run([pip_path, 'install', '-r', req_path], check=True)
        print("The dependencies have been successfully installed.")
    else:
        print(f"The requirements file '{file}' was not found in the '{req_path}' directory.")

def generate_requirements(env_name):
    """Generate or update requirements.txt file for a virtual environment."""
    env_path = os.path.join(ENV, env_name)
    if not os.path.exists(env_path):
        print(f"The environment '{env_name}' does not exist.")
        return
    
    # Check for requirements file in the requirements directory
    file = f"requirements_{env_name}.txt"
    req_path = os.path.join(REQ, file)
    if not os.path.exists(req_path):
        # Create the file
        with open(req_path, 'w') as f:
            f.write("")
        print(f"Created '{file}' file.")
    
    print(f"Generating requirements file for '{env_name}'...")
    
    # Determine the pip path based on OS
    if os.name == 'nt':  # Windows
        pip_path = os.path.join(env_path, 'Scripts', 'pip')
    else:  # macOS/Linux
        pip_path = os.path.join(env_path, 'bin', 'pip')
    
    # Run pip freeze to generate requirements
    with open(req_path, 'w') as f:
        subprocess.run([pip_path, 'freeze'], stdout=f, check=True)
    
    print(f"Requirements file '{file}' has been generated in the '{req_path}' directory.")
    print(f"Path: {os.path.abspath(req_path)}")


def delete_virtualenv(env_name):
    """Delete an existing virtual environment and its corresponding bat alias file if it exists."""

    # Check and delete the virtual environment
    env_path = os.path.join(ENV, env_name)
    if os.path.exists(env_path):
        print(f"Deleting the virtual environment '{env_name}'...")
        # Use appropriate command based on OS
        if os.name == 'nt':  # Windows
            subprocess.run(['rmdir', '/s', '/q', env_path], check=True, shell=True)
        else:  # macOS/Linux
            subprocess.run(['rm', '-rf', env_path], check=True)
        print(f"The virtual environment '{env_name}' has been deleted.")
        
        # Check and delete the corresponding bat file if it exists
        bat_dir = os.path.join(os.getcwd(), "bat")
        bat_file = os.path.join(bat_dir, f"activate_{env_name}.bat")
        if os.path.exists(bat_file):
            os.remove(bat_file)
            print(f"The corresponding bat alias file for '{env_name}' has been deleted.")
    else:
        print(f"The virtual environment '{env_name}' does not exist.")

def list_virtualenvs():
    """List the virtual environments in the current directory."""
    path = os.path.join(os.getcwd(), ENV)
    envs = [d for d in os.listdir(path)]
    print("Virtual environments present:")
    for env in envs:
        print(f"- {env}")

def show_menu():
    """Display the options menu."""
    print("\nVirtual Environment Management")
    print("1. Create a new virtual environment")
    print("2. Activate a virtual environment")
    print("3. Deactivate the active virtual environment")  
    print("4. Generate/Update requirements.txt file")
    print("5. Install dependencies from requirements.txt")
    print("6. Delete a virtual environment")
    print("7. List virtual environments")
    print("8. Exit")

def main():
    """Main function to handle user interaction."""

    # Create venv folder if it doesn't exist
    if not os.path.exists(FOLDER):
        os.makedirs(FOLDER)
        print(f"Created '{FOLDER}' directory.")

    # Create environments folder if it doesn't exist
    if not os.path.exists(ENV):
        os.makedirs(ENV)
        print(f"Created '{ENV}' directory.")

    # Create requirements folder if it doesn't exist
    if not os.path.exists(REQ):
        os.makedirs(REQ)
        print(f"Created '{REQ}' directory.")

    while True:
        show_menu()
        choice = input("\nChoose an option (1-8): ")

        if choice == '1':
            env_name = input("Enter the name of the virtual environment: ")
            create_virtualenv(env_name)
        elif choice == '2':
            env_name = input("Enter the name of the virtual environment to activate: ")
            activate_virtualenv(env_name)
        elif choice == '3':
            deactivate_virtualenv()
        elif choice == '4':
            env_name = input("Enter the name of the virtual environment to generate requirements for: ")
            generate_requirements(env_name)
        elif choice == '5':
            env_src = input("Enter the name of the source virtual environment requirements file: ")
            env_dst = input("Enter the name of the destination virtual environment: ")
            install_requirements(env_src, env_dst)
        elif choice == '6':
            env_name = input("Enter the name of the virtual environment to delete: ")
            delete_virtualenv(env_name)
        elif choice == '7':
            list_virtualenvs()
        elif choice == '8':
            print("Exiting...")
            sys.exit(0)
        else:
            print("Invalid choice, please try again.")

if __name__ == '__main__':
    main()
