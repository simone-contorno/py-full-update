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
        log_and_print(f"- Blacklisted packages:")
        for pkg in blacklist:
            log_and_print(f"  - {pkg}")
        
        if specific_versions:
            log_and_print("- Packages with specific versions:")
            for pkg, ver in specific_versions.items():
                log_and_print(f"  - {pkg}: {ver}")
        else:
            log_and_print("- No packages with specific versions")
        

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
    packages = set()
    lines = result.stdout.strip().split('\n')
    
    # Skip the first two lines (header and separator)
    if len(lines) > 2:
        for line in lines[2:]:
            if line.strip():  # Skip empty lines
                # First column is the package name
                package_name = line.split()[0]
                packages.add(package_name)
                print(f"- {package_name}")
        
        log_and_print(f"Found {len(packages)} outdated packages.", prefix="📦")
    else:
        log_and_print("No outdated packages found.", prefix="✅")
    
    return packages

conflict_dependency_memory = set()
def check_dependency_conflicts(blacklist: set):
    """
    Check for existing dependency conflicts before upgrading.
    
    Returns:
        list: List of conflict lines from pip check output, empty if no conflicts
    """
    global conflict_dependency_memory

    log_and_print("Checking for dependency conflicts...", prefix="🔍")

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
    
    conflict_packages = set()
    conflict_lines = []
    if result.returncode != 0:
        conflict_lines = [line for line in result.stdout.split('\n') if line.strip()]
        
        # Remove the ones in the blacklist
        flag = False
        if len(blacklist) > 0:
            for line in conflict_lines:
                element = line.split()[0].lower().replace("-","").replace("_","")
                for pkg in blacklist:
                    if pkg.lower().replace("-","").replace("_","") in element:
                        if flag == False:
                            log_and_print(f"Ignoring blacklisted packages:", prefix="🚫")
                            flag = True
                        log_and_print(f"- {pkg}")
                        conflict_lines.remove(line)

        if len(conflict_lines) > 0:
            log_and_print("WARNING: Dependency conflicts exist:", prefix="⚠️")
            for line in conflict_lines:
                log_and_print(f"- {line}")
        else:
            log_and_print("No dependency conflicts detected!", prefix="✅")
            return conflict_lines, sorted(conflict_packages)

        for line in conflict_lines:
            conflict_packages.add(line.split()[0])
        log_and_print(f"Found {len(conflict_packages)} packets with dependency conflicts.", prefix="📦")
        
        new_blacklist = set()
        for pkg in conflict_packages:
            conflict_dependency_memory.add(pkg) if pkg not in conflict_dependency_memory else new_blacklist.add(pkg)

        if len(new_blacklist) > 0:
            log_and_print(f"Potential blacklist packages detected:", prefix="⚠️")
    
            for package in new_blacklist:
                log_and_print(f"- {package}")
            
            res = input(f"\n❓ Would you like to add these packages to the blacklist? (Y/n)")
            if res.strip().lower() != "n":
                blacklist.update(new_blacklist)
            log_and_print(f"Blacklist packages updated.", prefix="✅")
    else:
        log_and_print("No dependency issues detected!", prefix="✅")

    return conflict_lines, sorted(conflict_packages)

def get_installed_version(package):
    """
    Get the currently installed version of a package.
    
    Parameters:
        package (str): Name of the package
        
    Returns:
        str or None: The installed version as a string, or None if not installed or error
    """
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "show", package],
            capture_output=True,
            text=True,
            check=False
        )
        
        if result.returncode == 0:
            for line in result.stdout.splitlines():
                if line.startswith("Version:"):
                    return line.split(":", 1)[1].strip()
        return None
    except Exception as e:
        log_and_print(f"Error getting version for {package}: {e}", prefix="⚠️")
        return None

def upgrade_packages(packages, specific_versions={}):
    """
    Upgrade multiple packages while handling dependencies.
    
    Parameters:
        packages (list): List of package names to upgrade
        specific_versions (dict, optional): Dictionary mapping package names to specific versions
    
    Returns:
        tuple: (successful_upgrades, failed_upgrades, skipped_versions) where:
            - successful_upgrades is a list of successfully upgraded package names
            - failed_upgrades is a list of tuples (package_name, error_message)
            - skipped_versions is a list of packages skipped because already at specified version
    """
    successful_upgrades = []
    failed_upgrades = []
    skipped_versions = []
    
    for i, package in enumerate(sorted(packages), 1):
        current_version = get_installed_version(package)
        if package in specific_versions:
            target_version = specific_versions[package]
            
            if current_version == target_version:
                log_and_print(f"Skipping {package}: Already at specified version {target_version} ({i}/{len(packages)})", prefix="⏭️")
                skipped_versions.append(package)
                successful_upgrades.append(package)  # Consider this successful since it's at desired version
                continue
                
            package_spec = f"{package}=={target_version}"
            log_and_print(f"Installing specific version: {package_spec} (current: {current_version or 'not installed'}) ({i}/{len(packages)})", prefix="🔄")
        else:
            package_spec = package
        
        log_and_print(f"Updating: {package} {current_version} ({i}/{len(packages)})", prefix="🔄")
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
            if package in specific_versions and package not in skipped_versions:
                log_and_print(f"Successfully installed {package}=={specific_versions[package]}", prefix="✅")
            elif package not in specific_versions:
                log_and_print(f"Successfully upgraded {package}", prefix="✅")
        else:
            failed_upgrades.append((package, result.stderr))
            log_and_print(f"Failed to upgrade {package}", prefix="❌")
    
    log_and_print("Update process completed!", prefix="✅")

    return successful_upgrades, failed_upgrades, skipped_versions

def display_summary(successful, failed, blacklisted, specific_versions, skipped_versions=None):
    """
    Display a summary of upgrade results.
    
    Parameters:
        successful (list): List of successfully upgraded package names
        failed (list): List of tuples (package_name, error_message) for failed upgrades
        blacklisted (list): List of blacklisted package names that were skipped
        specific_versions (dict): Dict of packages installed with specific versions
        skipped_versions (list, optional): List of packages skipped because already at specified version
    """
    log_and_print("\n=== UPGRADE SUMMARY ===")
    log_and_print(f"Successfully upgraded: {len(successful) - len(skipped_versions)}/{len(successful) + len(failed)} packages", prefix="✅")
    
    # Display specific versions packages successfully installed or skipped
    if specific_versions:
        installed_specific = [pkg for pkg in successful if pkg in specific_versions and pkg not in skipped_versions]
        if installed_specific:
            log_and_print(f"Packages installed with specific versions: {len(installed_specific)}")
            for package in installed_specific:
                log_and_print(f"- {package}: {specific_versions[package]}")
            
        
        skipped_specific = [pkg for pkg in successful if pkg in specific_versions and pkg in skipped_versions]
        if skipped_specific:
            log_and_print(f"Packages already at specified version (skipped): {len(skipped_specific)}")
            for package in skipped_specific:
                log_and_print(f"- {package}: {specific_versions[package]}")
            
    
    # Display skipped blacklist packages
    if blacklisted:
        log_and_print(f"Skipped {len(blacklisted)} blacklisted packages: ")
        for package in blacklisted:
            log_and_print(f"- {package}")
        
    
    # Display failed upgrades
    if failed:
        log_and_print(f"Failed {len(failed)} upgrades:", prefix="❌")
        for package, error in failed:
            log_and_print(f"- {package}: {error.splitlines()[0] if error else 'Unknown error'}")
        
def filter_outdated_list(outdated_packages: set, skipped_packages: set, filter_packages):

    if len(filter_packages) > 0:
        remove_packages = set()
        flag = False
        for package in outdated_packages:
            if package in filter_packages:
                if flag == False:
                    log_and_print(f"Skipping packages:", prefix="⏭️")
                    flag = True
                skipped_packages.add(package)
                remove_packages.add(package)
                log_and_print(f"- {package}")
        
        for pkg in remove_packages:
            outdated_packages.remove(pkg)
        
def check_blacklist(outdated_packages: set, conflict_lines: list, blacklisted_packages: set):
    log_and_print("Checking for potential blacklist packages...", prefix="🔍")
    blacklist = set()

    for package in outdated_packages:
        for line in conflict_lines:
            elements = line.split()[1:]
            for index, element in enumerate(elements):
                elements[index] = element.lower().replace("-","").replace("_","")
            if package.lower().replace("-","").replace("_","") in elements:
                blacklist.add(package)
    blacklist = sorted(blacklist)

    if blacklist:
        log_and_print(f"Potential blacklist packages detected:", prefix="⚠️")
        
        for package in blacklist:
            log_and_print(f"- {package}")
        
        res = input(f"\n❓ Would you like to add these packages to the blacklist? (Y/n)")
        if res.strip().lower() != "n":
            blacklisted_packages.update(blacklist)
        log_and_print(f"Blacklist packages updated.", prefix="✅")
    else:
        log_and_print("No potential blacklist packages detected.", prefix="✅")

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
    blacklisted_packages = set(blacklisted_packages)
    blacklisted_packages_backup = blacklisted_packages.copy()

    # Skipped packages initilization
    skipped_packages = set()
    
    # Ask for starting the upgrade
    res = input("\n❓ Proceed with the full upgrade? (Y/n) ")
    if res.strip().lower() == "n":
        log_and_print("Upgrade cancelled by user.", prefix="❌")
    else:
        # Upgrade pip
        upgrade_pip()
        
        # Get outdated packages
        outdated_packages = list_outdated_packages()
        
        # Filter the outdated packages based on the blacklisted ones
        filter_outdated_list(outdated_packages, skipped_packages, blacklisted_packages)

        if not outdated_packages:
            log_and_print("No packages to upgrade.", prefix="✅")
        
        # Check dependencies before upgrading
        conflict_lines, conflict_packages = check_dependency_conflicts(blacklisted_packages)
        if conflict_packages:
            # Ask for reinstalling or skipping packages with existing dependency conflicts
            res = input("\n❓ Would you like to reinstall packages with existing dependency conflicts? (Y/n) ")
            if res.strip().lower() != "n":
                log_and_print("The following packages will be reinstalled to the most recent version:", prefix="🔄")

                for package in conflict_packages:
                    if package not in outdated_packages:
                        log_and_print(f"- {package}")
                        outdated_packages.add(package)
            else:
                log_and_print("Skipping packages with dependency conflicts.", prefix="⚠️")
                
                # Filter out packages with conflicts
                filter_outdated_list(outdated_packages, skipped_packages, conflict_packages)

        if not outdated_packages:
            log_and_print("No packages to upgrade after filtering dependency conflicts.", prefix="✅")
            input("\n🔑 Press any key to exit...")
            exit(0)
        
        # Handle packages with specific versions
        specific_version_packages = {}
        for package in outdated_packages:
            if package in specific_versions:
                specific_version_packages[package] = specific_versions[package]
        
        # Upgrade packages
        successful, failed, skipped = upgrade_packages(outdated_packages, specific_version_packages)
        
        # Show summary
        display_summary(successful, failed, skipped_packages, specific_versions, skipped)
        
        # Check dependencies again after updates
        conflict_lines, conflict_packages = check_dependency_conflicts(blacklisted_packages)
        conflict_packages = set(conflict_packages)

        # Blacklist the packages that have generated a dependency conflict
        check_blacklist(outdated_packages, conflict_lines, blacklisted_packages)
        #conflict_packages = set(conflict_packages)
        
        # Upgrade packages with conflict dependencies until they are solved
        if conflict_packages:
            res = input("\n❓ Would you like to reinstall packages with existing dependency conflicts? (Y/n) ")
            while conflict_packages and res.strip().lower() != "n":
                # Upgrade packages
                conflict_packages_prev = set()
                successful, failed, skipped_versions = upgrade_packages(conflict_packages, specific_version_packages)
                conflict_packages_prev.update(conflict_packages)

                # Show summary
                display_summary(successful, failed, skipped_packages, specific_versions, skipped_versions)

                # Reckeching 
                conflict_lines, conflict_packages = check_dependency_conflicts(blacklisted_packages)
                conflict_packages = set(conflict_packages)

                # Blacklist the packages that have generated a dependency conflict
                check_blacklist(conflict_packages, conflict_lines, blacklisted_packages)
                filter_outdated_list(conflict_packages, skipped_packages, blacklisted_packages)
                if conflict_packages:
                    res = input("\n❓ Would you like to reinstall packages with existing dependency conflicts? (Y/n) ")
        
        # Update the blacklist field in the configuration JSON file
        if blacklisted_packages != blacklisted_packages_backup:
            res = input("\n❓ Would you like to update the package_config.json blacklist field? (Y/n) ")
            if res.strip().lower() != "n":
                with open("package_config.json", "r") as file:
                    data = json.load(file)
            
                log_and_print("Updating package_config.json blacklist field...", prefix="📝")
                for package in blacklisted_packages:
                    if package not in data["blacklist"]:
                        data["blacklist"].append(package)
                
                with open("package_config.json", "w") as file:
                    json.dump(data, file, indent=4)
                log_and_print("package_config.json blacklist field updated.", prefix="✅")

        """
        # Update the specified_version field in the configuration JSON file
        res = input("\n❓ Would you like to update the package_config.json specific_version field? (Y/n) ")
        if res.strip().lower() != "n": 
            with open("package_config.json", "r") as file:
                data = json.load(file)
            
            log_and_print("Updating package_config.json specific_version field...", prefix="📝")
            for package in conflict_packages:
                data["specific_versions"][package] = get_installed_version(package)  
            
            with open("package_config.json", "w") as file:
                json.dump(data, file, indent=4)
            log_and_print(f"package_config.json specific_version field updated.", prefix="✅")     
        """   

    # Wait for user input to terminate
    input("\n🔑 Press any key to exit...")

if __name__ == "__main__":
    main()