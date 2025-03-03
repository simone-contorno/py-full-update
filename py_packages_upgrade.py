import subprocess
import datetime
import os
import sys
import json

# Global constants
LOGS_FOLDER = "logs"
LOG_FILE = None  # Will be set in main() before use
CONFIG_FILE = "package_config.json"

def create_logs_folder():
    """
    Create the logs folder if it doesn't exist.
    
    Returns:
        logs_path (str): Logs absolute path folder
    """
    # Get script path
    script_path = os.path.dirname(os.path.abspath(__file__))
    logs_path = os.path.join(script_path, LOGS_FOLDER)
    if not os.path.exists(logs_path):
        os.makedirs(logs_path)
    return logs_path

def get_log_file_path(logs_folder_path):
    """
    Generate a timestamped log file path.
    
    Parameters:
        logs_folder_path (str): The absolute path to the logs folder

    Returns:
        str: Full path to the log file with timestamp in format 'YYYY-MM-DD_HH-MM-SS_log.txt'
    """
    current_date_time = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    file_name = f"{current_date_time}_log.txt"
    return os.path.join(logs_folder_path, file_name)

def log_and_print(message, prefix=None, write_to_log=True):
    """
    Print a message with optional prefix and write to log file.
    
    Parameters:
        message (str): The message to display and log
        prefix (str, optional): An emoji or text prefix to display before the message
        write_to_log (bool, optional): Whether to write the message to the log file
    """
    if prefix:
        print(f"\n{prefix} {message}")
    else:
        print(message)
    
    if write_to_log and LOG_FILE:
        try:
            with open(LOG_FILE, "a") as file:
                file.write(f"\n{message}")
        except PermissionError:
            print("❌ Logs writing permission denied! Try running as Administrator or changing the file path.")
        except Exception as e:
            print(f"⚠️ Logs writing error: {e}")

def load_config():
    """
    Load the configuration file containing blacklisted packages and version-specific packages.
    
    Returns:
        tuple: (blacklisted_packages, version_specific_packages) where:
            - blacklisted_packages is a list of package names to skip
            - version_specific_packages is a dict of {package_name: version}
    """
    default_config = {
        "blacklist": [],
        "specific_versions": {}
    }
    
    if not os.path.exists(CONFIG_FILE):
        log_and_print(f"Config file {CONFIG_FILE} not found. Creating default config.", prefix="📝")
        with open(CONFIG_FILE, "w") as file:
            json.dump(default_config, file, indent=4)
        return default_config["blacklist"], default_config["specific_versions"]
    
    try:
        with open(CONFIG_FILE, "r") as file:
            config = json.load(file)
        
        # Ensure required keys exist with default values
        blacklist = config.get("blacklist", [])
        specific_versions = config.get("specific_versions", {})
        
        log_and_print(f"Loaded configuration:", prefix="📋")
        log_and_print(f"- Blacklisted packages: {', '.join(blacklist) if blacklist else 'None'}")
        if specific_versions:
            log_and_print("- Packages with specific versions:")
            for pkg, ver in specific_versions.items():
                log_and_print(f"  - {pkg}: {ver}")
        else:
            log_and_print("- No packages with specific versions")
        log_and_print("")

        return blacklist, specific_versions
        
    except (json.JSONDecodeError, IOError) as e:
        log_and_print(f"Error loading config file: {e}", prefix="❌")
        return [], {}

def upgrade_pip():
    """
    Upgrade pip to the latest version.
    
    Returns:
        bool: True if pip was successfully upgraded or already at latest version
    """
    log_and_print("Upgrading pip...", prefix="⬆️")
    
    result = subprocess.run(
        [sys.executable, "-m", "pip", "install", "--upgrade", "pip"], 
        capture_output=True, 
        text=True,
        check=False
    )
    
    with open(LOG_FILE, "a") as file:
        file.write(f"\n{result.stdout}")
        if result.stderr:
            file.write(f"\n{result.stderr}")
    
    if "Requirement already satisfied" in result.stdout:
        log_and_print("pip already at the latest version.", prefix="✅")
        return True
    
    if result.returncode == 0:
        log_and_print("pip upgraded to the latest version.", prefix="✅")
        return True
    else:
        log_and_print(f"Error upgrading pip: {result.stderr}", prefix="❌")
        return False

def list_outdated_packages():
    """
    Get a list of all outdated packages using pip.
    
    Returns:
        list: List of outdated package names, empty if none found or error occurred
    """
    log_and_print("Checking for outdated packages...", prefix="🔍")

    # Use standard format output for simplicity and reliability
    result = subprocess.run(
        [sys.executable, "-m", "pip", "list", "--outdated"],
        capture_output=True,
        text=True,
        check=False
    )
    
    with open(LOG_FILE, "a") as file:
        file.write(f"\n{result.stdout}")
        if result.stderr:
            file.write(f"\n{result.stderr}")
    
    if result.returncode != 0:
        log_and_print(f"Error checking outdated packages: {result.stderr}", prefix="❌")
        return []
    
    # Parse the standard pip output format
    packages = []
    lines = result.stdout.strip().split('\n')
    
    # Skip the first two lines (header and separator)
    if len(lines) > 2:
        for line in lines[2:]:
            if line.strip():  # Skip empty lines
                # First column is the package name
                package_name = line.split()[0]
                packages.append(package_name)
                print(f"- {package_name}")
        
        log_and_print(f"Found {len(packages)} outdated packages.", prefix="📦")
    else:
        log_and_print("No outdated packages found.", prefix="✅")
    
    return packages

def check_dependency_conflicts():
    """
    Check for existing dependency conflicts before upgrading.
    
    Returns:
        list: List of conflict lines from pip check output, empty if no conflicts
    """
    result = subprocess.run(
        [sys.executable, "-m", "pip", "check"],
        capture_output=True,
        text=True,
        check=False
    )
    
    with open(LOG_FILE, "a") as file:
        if result.stdout:
            file.write(f"\nDependency check results:\n{result.stdout}")
        if result.stderr:
            file.write(f"\nDependency check errors:\n{result.stderr}")
    
    if result.returncode != 0:
        conflict_lines = [line for line in result.stdout.split('\n') if line.strip()]
        
        log_and_print("WARNING: Dependency conflicts exist:", prefix="⚠️")
        for line in conflict_lines:
            print(f"- {line}")
            with open(LOG_FILE, "a") as file:
                file.write(f"\n- {line}")
        
        return conflict_lines
    
    log_and_print("No dependency issues detected!", prefix="✅")
    return []

def upgrade_packages(packages, specific_versions=None):
    """
    Upgrade multiple packages while handling dependencies.
    
    Parameters:
        packages (list): List of package names to upgrade
        specific_versions (dict, optional): Dictionary mapping package names to specific versions
    
    Returns:
        tuple: (successful_upgrades, failed_upgrades) where:
            - successful_upgrades is a list of successfully upgraded package names
            - failed_upgrades is a list of tuples (package_name, error_message)
    """
    specific_versions = specific_versions or {}
    successful_upgrades = []
    failed_upgrades = []
    
    for i, package in enumerate(packages, 1):
        if package in specific_versions:
            version = specific_versions[package]
            package_spec = f"{package}=={version}"
            log_and_print(f"Installing specific version: {package_spec} ({i}/{len(packages)})", prefix="🔄")
        else:
            package_spec = package
            log_and_print(f"Updating: {package} ({i}/{len(packages)})", prefix="🔄")
        
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "--upgrade", package_spec],
            capture_output=True,
            text=True,
            check=False
        )
        
        with open(LOG_FILE, "a") as file:
            file.write(f"\n{result.stdout}")
            if result.stderr:
                file.write(f"\n{result.stderr}")
        
        if result.returncode == 0:
            successful_upgrades.append(package)
            if package in specific_versions:
                log_and_print(f"Successfully installed {package}=={specific_versions[package]}", prefix="✅")
            else:
                log_and_print(f"Successfully upgraded {package}", prefix="✅")
        else:
            failed_upgrades.append((package, result.stderr))
            log_and_print(f"Failed to upgrade {package}", prefix="❌")
    
    return successful_upgrades, failed_upgrades

def display_summary(successful, failed, blacklisted, specific_versions):
    """
    Display a summary of upgrade results.
    
    Parameters:
        successful (list): List of successfully upgraded package names
        failed (list): List of tuples (package_name, error_message) for failed upgrades
        blacklisted (list): List of blacklisted package names that were skipped
        specific_versions (dict): Dict of packages installed with specific versions
    """
    log_and_print("=== UPGRADE SUMMARY ===")
    log_and_print(f"Successfully upgraded: {len(successful)}/{len(successful) + len(failed)} packages")
    
    if specific_versions:
        installed_specific = [pkg for pkg in successful if pkg in specific_versions]
        if installed_specific:
            log_and_print(f"Packages installed with specific versions: {len(installed_specific)}")
            for package in installed_specific:
                log_and_print(f"- {package}: {specific_versions[package]}")
    
    if blacklisted:
        log_and_print(f"Blacklisted packages skipped: {len(blacklisted)}")
        for package in blacklisted:
            log_and_print(f"- {package}")
    
    if failed:
        log_and_print("Failed upgrades:", prefix="❌")
        for package, error in failed:
            log_and_print(f"- {package}: {error.splitlines()[0] if error else 'Unknown error'}")

def main():
    """
    Main function that orchestrates the package update process.
    """
    global LOG_FILE
    
    # Create logs folder
    logs_folder_path = create_logs_folder()
    LOG_FILE = get_log_file_path(logs_folder_path)
    log_and_print("Python Package Auto-Updater", prefix="🚀")
    log_and_print(f"Log file path: {LOG_FILE}", prefix="📝")
    
    # Load configuration
    blacklisted_packages, specific_versions = load_config()
    
    # Ask for starting the upgrade
    res = input("❓ Proceed with the full upgrade? (Y/n) ")
    if res.lower() != "n":
        # Upgrade pip
        upgrade_pip()
        
        # List outdated packages
        all_outdated_packages = list_outdated_packages()
        
        if not all_outdated_packages:
            log_and_print("No packages to upgrade. Exiting.", prefix="✅")
        else:
            # Filter out blacklisted packages
            skipped_packages = []
            outdated_packages = []
            
            for package in all_outdated_packages:
                if package in blacklisted_packages:
                    skipped_packages.append(package)
                    log_and_print(f"Skipping blacklisted package: {package}", prefix="⏭️")
                else:
                    outdated_packages.append(package)
            
            # Check if all packages are blacklisted
            if not outdated_packages:
                log_and_print("All outdated packages are blacklisted. Exiting.", prefix="✅")
            else:
                # Check dependencies before upgrading
                conflict_lines = check_dependency_conflicts()
                
                if conflict_lines:
                    # Ask for upgrading anyway
                    res = input("\n❓ Would you like to attempt a full upgrade anyway? (Y/n) ")
                    if res.lower() == "n":
                        # Ask for upgrading by skipping dependencies conflicts 
                        res = input("❓ Would you like to upgrade while skipping packages with dependency conflicts? (Y/n) ")
                        if res.lower() != "n":
                            log_and_print("Skipping packages with dependency conflicts:", prefix="⚠️")
                            
                            # Extract package names from conflict lines
                            conflict_packages = set()
                            for line in conflict_lines:
                                parts = line.split()
                                if len(parts) >= 1:
                                    conflict_packages.add(parts[0])
                            
                            # Filter out packages with conflicts
                            filtered_packages = []
                            for package in outdated_packages:
                                if package in conflict_packages:
                                    skipped_packages.append(package)
                                    log_and_print(f"- Skipping: {package}")
                                else:
                                    filtered_packages.append(package)
                            
                            outdated_packages = filtered_packages
                        else:
                            log_and_print("Update cancelled due to dependency conflicts.", prefix="✅")

                            # Wait for user input to terminate
                            input("\n🔑 Press any key to exit...")
                            sys.exit(0)
                
                if not outdated_packages:
                    log_and_print("No packages to upgrade after filtering conflicts. Exiting.", prefix="✅")
                else:
                    # Handle packages with specific versions
                    specific_version_packages = {}
                    for package in outdated_packages:
                        if package in specific_versions:
                            specific_version_packages[package] = specific_versions[package]
                    
                    # Upgrade packages
                    successful, failed = upgrade_packages(outdated_packages, specific_version_packages)
                    log_and_print("Update process completed!", prefix="✅")
                    
                    # Show summary
                    display_summary(successful, failed, skipped_packages, specific_versions)
                    
                    # Check dependencies again after updates
                    log_and_print("Rechecking dependencies after upgrade...", prefix="🔄")
                    check_dependency_conflicts()
    
    else:
        log_and_print("Upgrade cancelled by user.", prefix="❌")

    # Wait for user input to terminate
    input("\n🔑 Press any key to exit...")

if __name__ == "__main__":
    main()