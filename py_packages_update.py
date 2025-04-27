import subprocess
import datetime
import os
import sys
import json
from collections import defaultdict

class PackageUpdater:
    """
    A class to manage Python package updates, handle dependency conflicts,
    and maintain a blacklist of problematic packages.
    """

    # Class constants
    LOGS_FOLDER = "logs"
    CONFIG_FILE = "package_config.json"

    def __init__(self):
        """Initialize the PackageUpdater with log file setup and configuration loading."""
        self.logs_folder_path = self._create_logs_folder()
        self.log_file_path = self._get_log_file_path(self.logs_folder_path)
        self.conflict_dependency_memory = set()
        self.conflict_history = []
        
        # Display startup message
        self._log_and_print("Python Package Auto-Updater", prefix="🚀")
        self._log_and_print(f"Log file path: {self.log_file_path}", prefix="📝")
        
        # Load configuration and initialize tracking sets
        self.blacklisted_packages, self.specific_versions = self._load_config()
        self.blacklisted_packages = set(self.blacklisted_packages)
        self.blacklisted_packages_backup = self.blacklisted_packages.copy()
        self.skipped_packages = set()

    def _create_logs_folder(self):
        """
        Create the logs folder if it doesn't exist.
        
        Returns:
            str: Absolute path to the logs folder
        """
        script_path = os.path.dirname(os.path.abspath(__file__))
        logs_path = os.path.join(script_path, self.LOGS_FOLDER)
        if not os.path.exists(logs_path):
            os.makedirs(logs_path)
        return logs_path

    def _get_log_file_path(self, logs_folder_path):
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

    def _log_and_print(self, message, prefix=None, write_to_log=True):
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
        
        if write_to_log and self.log_file_path:
            try:
                with open(self.log_file_path, "a") as file:
                    file.write(f"\n{message}")
            except PermissionError:
                print("❌ Logs writing permission denied! Try running as Administrator or changing the file path.")
            except Exception as e:
                print(f"⚠️ Logs writing error: {e}")

    def _load_config(self):
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
        
        if not os.path.exists(self.CONFIG_FILE):
            self._log_and_print(f"Config file {self.CONFIG_FILE} not found. Creating default config.", prefix="📝")
            with open(self.CONFIG_FILE, "w") as file:
                json.dump(default_config, file, indent=4)
            return default_config["blacklist"], default_config["specific_versions"]
        
        try:
            with open(self.CONFIG_FILE, "r") as file:
                config = json.load(file)
            
            # Ensure required keys exist with default values
            blacklist = config.get("blacklist", [])
            specific_versions = config.get("specific_versions", {})
            
            self._log_and_print(f"Loaded configuration:", prefix="📋")
            self._log_and_print(f"- Blacklisted packages:")
            for pkg in blacklist:
                self._log_and_print(f"  - {pkg}")
            
            if specific_versions:
                self._log_and_print("- Packages with specific versions:")
                for pkg, ver in specific_versions.items():
                    self._log_and_print(f"  - {pkg}: {ver}")
            else:
                self._log_and_print("- No packages with specific versions")
            
            return blacklist, specific_versions
            
        except (json.JSONDecodeError, IOError) as e:
            self._log_and_print(f"Error loading config file: {e}", prefix="❌")
            return [], {}

    def update_pip(self):
        """
        Update pip to the latest version.
        
        Returns:
            bool: True if pip was successfully updated or already at latest version
        """
        self._log_and_print("Updating pip...", prefix="⬆️")
        
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "--upgrade", "pip"], 
            capture_output=True, 
            text=True,
            check=False
        )
        
        with open(self.log_file_path, "a") as file:
            file.write(f"\n{result.stdout}")
            if result.stderr:
                file.write(f"\n{result.stderr}")
        
        if "Requirement already satisfied" in result.stdout:
            self._log_and_print("pip already at the latest version.", prefix="✅")
            return True
        
        if result.returncode == 0:
            self._log_and_print("pip updated to the latest version.", prefix="✅")
            return True
        else:
            self._log_and_print(f"Error updating pip: {result.stderr}", prefix="❌")
            return False

    def list_outdated_packages(self):
        """
        Get a list of all outdated packages using pip.
        
        Returns:
            set: Set of outdated package names, empty if none found or error occurred
        """
        self._log_and_print("Checking for outdated packages...", prefix="🔍")

        # Use standard format output for simplicity and reliability
        result = subprocess.run(
            [sys.executable, "-m", "pip", "list", "--outdated"],
            capture_output=True,
            text=True,
            check=False
        )
        
        with open(self.log_file_path, "a") as file:
            file.write(f"\n{result.stdout}")
            if result.stderr:
                file.write(f"\n{result.stderr}")
        
        if result.returncode != 0:
            self._log_and_print(f"Error checking outdated packages: {result.stderr}", prefix="❌")
            return set()
        
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
            
            self._log_and_print(f"Found {len(packages)} outdated packages.", prefix="📦")
        else:
            self._log_and_print("No outdated packages found.", prefix="✅")
        
        return packages

    def check_dependency_conflicts(self, blacklist_set):
        """
        Check for existing dependency conflicts before updating.
        
        Parameters:
            blacklist_set (set): Set of package names to ignore in conflict detection
            
        Returns:
            tuple: (conflict_lines, conflict_packages) where:
                - conflict_lines is a list of text lines describing each conflict
                - conflict_packages is a sorted list of package names with conflicts
        """
        self._log_and_print("Checking for dependency conflicts...", prefix="🔍")

        result = subprocess.run(
            [sys.executable, "-m", "pip", "check"],
            capture_output=True,
            text=True,
            check=False
        )
        
        with open(self.log_file_path, "a") as file:
            if result.stdout:
                file.write(f"\nDependency check results:\n{result.stdout}")
            if result.stderr:
                file.write(f"\nDependency check errors:\n{result.stderr}")
        
        conflict_packages = set()
        conflict_lines = []
        if result.returncode != 0:
            conflict_lines = [line for line in result.stdout.split('\n') if line.strip()]
            
            # Remove packages in the blacklist from conflict reporting
            flag = False
            if len(blacklist_set) > 0:
                filtered_conflict_lines = conflict_lines.copy()
                for line in conflict_lines:
                    element = line.split()[0].lower().replace("-","").replace("_","")
                    for pkg in blacklist_set:
                        if pkg.lower().replace("-","").replace("_","") in element:
                            if flag == False:
                                self._log_and_print(f"Ignoring blacklisted packages:", prefix="🚫")
                                flag = True
                            self._log_and_print(f"- {pkg}")
                            filtered_conflict_lines.remove(line)
                            break
                conflict_lines = filtered_conflict_lines

            if len(conflict_lines) > 0:
                self._log_and_print("WARNING: Dependency conflicts exist:", prefix="⚠️")
                for line in conflict_lines:
                    self._log_and_print(f"- {line}")
            else:
                self._log_and_print("No dependency conflicts detected!", prefix="✅")
                return conflict_lines, sorted(conflict_packages)

            # Extract package names from conflict lines
            for line in conflict_lines:
                conflict_packages.add(line.split()[0])
            self._log_and_print(f"Found {len(conflict_packages)} packages with dependency conflicts.", prefix="📦")
            
            # Identify potential blacklist candidates (packages that repeatedly cause conflicts)
            new_blacklist = set()
            for pkg in conflict_packages:
                if pkg in self.conflict_dependency_memory:
                    new_blacklist.add(pkg)
                else:
                    self.conflict_dependency_memory.add(pkg)

            if len(new_blacklist) > 0:
                self._log_and_print(f"Potential blacklist packages detected:", prefix="⚠️")
        
                for package in new_blacklist:
                    self._log_and_print(f"- {package}")
                
                res = input(f"\n❓ Would you like to add these packages to the blacklist? (Y/n)")
                if res.strip().lower() != "n":
                    blacklist_set.update(new_blacklist)
                    self._log_and_print(f"Blacklist packages updated.", prefix="✅")
        else:
            self._log_and_print("No dependency issues detected!", prefix="✅")

        # Update the conflict history
        new_conflict_history = [
            [conflict_lines[i].split()[0], conflict_lines[i].split()[-2], self.get_conflict_version(conflict_lines[i])]
            for i in range(len(conflict_lines))
            if self.get_conflict_version(conflict_lines[i]) is not None and self.get_conflict_version(conflict_lines[i]) != []
        ]
        for history in new_conflict_history:
            if history not in self.conflict_history:
                self.conflict_history.append(history)

        return conflict_lines, sorted(conflict_packages)

    def get_installed_version(self, package):
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
            self._log_and_print(f"Error getting version for {package}: {e}", prefix="⚠️")
            return None

    def update_packages(self, packages, specific_versions={}):
        """
        Update multiple packages while handling dependencies.
        
        Parameters:
            packages (list or set): Collection of package names to update
            specific_versions (dict, optional): Dictionary mapping package names to specific versions
        
        Returns:
            tuple: (successful_updates, failed_updates, skipped_updates) where:
                - successful_updates is a list of successfully updated package names
                - failed_updates is a list of tuples (package_name, error_message)
                - skipped_updates is a list of packages skipped because already at specified version
        """
        successful_updates = []
        failed_updates = []
        skipped_updates = []
        
        for i, package in enumerate(sorted(packages), 1):
            current_version = self.get_installed_version(package)
            if package in specific_versions:
                target_version = specific_versions[package]
                
                if current_version == target_version:
                    self._log_and_print(f"Skipping {package}: Already at specified version {target_version} ({i}/{len(packages)})", prefix="⏭️")
                    skipped_updates.append(package)
                    successful_updates.append(package)  # Consider this successful since it's at desired version
                    continue
                    
                package_spec = f"{package}=={target_version}"
                self._log_and_print(f"Installing specific version: {package_spec} (current: {current_version or 'not installed'}) ({i}/{len(packages)})", prefix="🔄")
            else:
                package_spec = package
            
            self._log_and_print(f"Updating: {package} {current_version} ({i}/{len(packages)})", prefix="🔄")
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", "--upgrade", package_spec],
                capture_output=True,
                text=True,
                check=False
            )
            
            with open(self.log_file_path, "a") as file:
                file.write(f"\n{result.stdout}")
                if result.stderr:
                    file.write(f"\n{result.stderr}")
            
            if result.returncode == 0:
                successful_updates.append(package)
                if package in specific_versions and package not in skipped_updates:
                    self._log_and_print(f"Successfully installed {package}=={specific_versions[package]}", prefix="✅")
                elif package not in specific_versions:
                    self._log_and_print(f"Successfully updated {package}", prefix="✅")
            else:
                failed_updates.append((package, result.stderr))
                self._log_and_print(f"Failed to update {package}", prefix="❌")
        
        self._log_and_print("Update process completed!", prefix="✅")

        return successful_updates, failed_updates, skipped_updates

    def display_summary(self, successful, failed, blacklisted, specific_versions, skipped_updates=None):
        """
        Display a summary of update results.
        
        Parameters:
            successful (list): List of successfully updated package names
            failed (list): List of tuples (package_name, error_message) for failed updates
            blacklisted (list or set): Collection of blacklisted package names that were skipped
            specific_versions (dict): Dict of packages installed with specific versions
            skipped_updates (list, optional): List of packages skipped because already at specified version
        """
        if skipped_updates is None:
            skipped_updates = []
            
        self._log_and_print("\n=== UPDATE SUMMARY ===")
        self._log_and_print(f"Successfully updated: {len(successful) - len(skipped_updates)}/{len(successful) + len(failed)} packages", prefix="✅")
        
        # Display specific versions packages successfully installed or skipped
        if specific_versions:
            installed_specific = [pkg for pkg in successful if pkg in specific_versions and pkg not in skipped_updates]
            if installed_specific:
                self._log_and_print(f"Packages installed with specific versions: {len(installed_specific)}")
                for package in installed_specific:
                    self._log_and_print(f"- {package}: {specific_versions[package]}")
                
            
            skipped_specific = [pkg for pkg in successful if pkg in specific_versions and pkg in skipped_updates]
            if skipped_specific:
                self._log_and_print(f"Packages already at specified version (skipped): {len(skipped_specific)}")
                for package in skipped_specific:
                    self._log_and_print(f"- {package}: {specific_versions[package]}")
                
        # Display skipped blacklist packages
        if blacklisted:
            self._log_and_print(f"Skipped {len(blacklisted)} blacklisted packages: ")
            for package in blacklisted:
                self._log_and_print(f"- {package}")
            
        # Display failed updates
        if failed:
            self._log_and_print(f"Failed {len(failed)} updates:", prefix="❌")
            for package, error in failed:
                self._log_and_print(f"- {package}: {error.splitlines()[0] if error else 'Unknown error'}")

    def filter_outdated_list(self, outdated_packages, skipped_packages, filter_packages):
        """
        Filter out packages that should be skipped from the outdated packages set.
        
        Parameters:
            outdated_packages (set): Set of outdated package names to filter
            skipped_packages (set): Set to store skipped package names
            filter_packages (set or list): Collection of package names to filter out
        """
        if len(filter_packages) > 0:
            remove_packages = set()
            flag = False
            for package in outdated_packages:
                if package in filter_packages:
                    if flag == False:
                        self._log_and_print(f"Skipping packages:", prefix="⏭️")
                        flag = True
                    skipped_packages.add(package)
                    remove_packages.add(package)
                    self._log_and_print(f"- {package}")
            
            for pkg in remove_packages:
                outdated_packages.remove(pkg)

    def check_blacklist(self, outdated_packages, conflict_lines, blacklisted_packages):
        """
        Identify potential blacklist candidates from dependency conflicts.
        
        Parameters:
            outdated_packages (set): Set of outdated package names
            conflict_lines (list): List of dependency conflict text lines
            blacklisted_packages (set): Set of currently blacklisted packages
        """
        self._log_and_print("Checking for potential blacklist packages...", prefix="🔍")
        blacklist_candidates = set()

        for package in outdated_packages:
            for line in conflict_lines:
                elements = line.split()[1:]
                for index, element in enumerate(elements):
                    elements[index] = element.lower().replace("-","").replace("_","")
                if package.lower().replace("-","").replace("_","") in elements:
                    blacklist_candidates.add(package)
                    
        blacklist_candidates = sorted(blacklist_candidates)

        if blacklist_candidates:
            self._log_and_print(f"Potential blacklist packages detected:", prefix="⚠️")
            
            for package in blacklist_candidates:
                self._log_and_print(f"- {package}")
            
            res = input(f"\n❓ Would you like to add these packages to the blacklist? (Y/n)")
            if res.strip().lower() != "n":
                blacklisted_packages.update(blacklist_candidates)
                self._log_and_print(f"Blacklist packages updated.", prefix="✅")
        else:
            self._log_and_print("No potential blacklist packages detected.", prefix="✅")

    def update_blacklist_in_config(self):
        """
        Update the blacklist field in the configuration JSON file.
        """
        if self.blacklisted_packages != self.blacklisted_packages_backup:
            res = input("\n❓ Would you like to update the package_config.json blacklist field? (Y/n) ")
            if res.strip().lower() != "n":
                with open(self.CONFIG_FILE, "r") as file:
                    data = json.load(file)
            
                self._log_and_print("Updating package_config.json blacklist field...", prefix="📝")
                for package in self.blacklisted_packages:
                    if package not in data["blacklist"]:
                        data["blacklist"].append(package)
                
                with open(self.CONFIG_FILE, "w") as file:
                    json.dump(data, file, indent=4)
                self._log_and_print("package_config.json blacklist field updated.", prefix="✅")

    def get_conflict_version(self, conflict_line):
        """
        # Save the conflict package
        """

        conflict_line = conflict_line.lower()
        split = conflict_line.split("requirement " + conflict_line.split(" ")[-2])

        # Remove python version spec.
        if len(split) > 0:
            for el in split:
                if "python_version" in el or "sys_platform" in el:
                    split.remove(el)

        if len(split) == 0:
            return None

        # Check for specific versions
        if len(split) > 1:
            split = split[1].split(",")
        version = [el for el in split if "=" in el]

        # Remove incompatible versions
        if len(version) > 0:
            for el in version:
                if "!=" in el:
                    version.remove(el)

        if len(version) == 0: 
            version = [el for el in split if ">" in el or "<" in el]
            if len(version) > 0: version = version[0]

        elif len(version) == 1: 
            version = version[0].split("=")
            if len(version) > 0: version = version[-1]

        elif len(version) == 2:
            if len(version[0].split("=")) > 0:
                version_0 = version[0].split("=")[-1]
            else:
                version_0 = None

            if len(version[1].split("=")) > 0:
                version_1 = version[1].split("=")[-1]
            else:
                version_1 = None

            if version_0 is not None and version_1 is not None:
                version = max(version_0, version_1)
            else:
                version = None

        return version

    def generate_requirements(self, conflict_history_file):
        """
        Generate a requirements.txt file for a virtual environment.
        """
        path = ".\\venv\\requirements\\"
        while True:
            env_name = input("📝 Enter the name of the virtual environment ('none' to quit): ")
            if env_name.lower() == 'none':
                self._log_and_print("Generation cancelled by user.", prefix="❌")
                return

            file_name = f"requirements_{env_name}.txt"
            file_path = os.path.join(path, file_name)
            if os.path.exists(file_path):
                res = input(f"\n❓ The file '{file_name}' already exists. Do you want to overwrite it? (Y/n) ")
                if res.lower() != "n":
                    break
            else:
                break

        # Extract info from JSON file and create a requirements.txt file
        with open(os.path.join("conflict_history", conflict_history_file), 'r') as file:
            data = json.load(file)

        with open(file_path, 'w') as file:
            for item in data.items():
                pkg, infos = item
                for info in infos:
                    line = f"{info['dependency']}=={info['version']}\n"
                    file.write(line)

        self._log_and_print(f"Written '{file_name}' file.", prefix="📝")
            
    def run(self):
        """
        Main method that orchestrates the package update process.
        """
        # Ask for starting the update
        res = input("\n❓ Proceed with the full update? (Y/n) ")
        if res.strip().lower() == "n":
            self._log_and_print("Update cancelled by user.", prefix="❌")
            return
            
        # Update pip
        self.update_pip()
        
        # Get outdated packages
        outdated_packages = self.list_outdated_packages()
        
        # Filter the outdated packages based on the blacklisted ones
        self.filter_outdated_list(outdated_packages, self.skipped_packages, self.blacklisted_packages)

        if not outdated_packages:
            self._log_and_print("No packages to update.", prefix="✅")
            return
        
        # Check dependencies before updating
        conflict_lines, conflict_packages = self.check_dependency_conflicts(self.blacklisted_packages)
        if conflict_packages:
            # Ask for reinstalling or skipping packages with existing dependency conflicts
            res = input("\n❓ Would you like to reinstall packages with existing dependency conflicts? (Y/n) ")
            if res.strip().lower() != "n":
                self._log_and_print("The following packages will be reinstalled to the most recent version:", prefix="🔄")

                for package in conflict_packages:
                    if package not in outdated_packages:
                        self._log_and_print(f"- {package}")
                        outdated_packages.add(package)
            else:
                self._log_and_print("Skipping packages with dependency conflicts.", prefix="⚠️")
                
                # Filter out packages with conflicts
                self.filter_outdated_list(outdated_packages, self.skipped_packages, conflict_packages)

        if not outdated_packages:
            self._log_and_print("No packages to update after filtering dependency conflicts.", prefix="✅")
            return
        
        # Handle packages with specific versions
        specific_version_packages = {}
        for package in outdated_packages:
            if package in self.specific_versions:
                specific_version_packages[package] = self.specific_versions[package]
        
        # Update packages
        successful, failed, skipped = self.update_packages(outdated_packages, specific_version_packages)
        
        # Show summary
        self.display_summary(successful, failed, self.skipped_packages, self.specific_versions, skipped)
        
        # Check dependencies again after updates
        conflict_lines, conflict_packages = self.check_dependency_conflicts(self.blacklisted_packages)
        conflict_packages = set(conflict_packages)

        # Blacklist the packages that have generated a dependency conflict
        self.check_blacklist(outdated_packages, conflict_lines, self.blacklisted_packages)
        
        # Update packages with conflict dependencies until they are solved
        if conflict_packages:
            res = input("\n❓ Would you like to reinstall packages with existing dependency conflicts? (Y/n) ")
            while conflict_packages and res.strip().lower() != "n":
                # Update packages
                conflict_packages_prev = set()
                successful, failed, skipped_updates = self.update_packages(conflict_packages, specific_version_packages)
                conflict_packages_prev.update(conflict_packages)

                # Show summary
                self.display_summary(successful, failed, self.skipped_packages, self.specific_versions, skipped_updates)

                # Rechecking 
                conflict_lines, conflict_packages = self.check_dependency_conflicts(self.blacklisted_packages)
                conflict_packages = set(conflict_packages)

                # Blacklist the packages that have generated a dependency conflict
                self.check_blacklist(conflict_packages, conflict_lines, self.blacklisted_packages)
                self.filter_outdated_list(conflict_packages, self.skipped_packages, self.blacklisted_packages)
                if conflict_packages:
                    res = input("\n❓ Would you like to reinstall packages with existing dependency conflicts? (Y/n) ")

        # Update the blacklist field in the configuration JSON file
        self.update_blacklist_in_config()

def main():
    """
    Entry point function that creates and runs the PackageUpdater.
    """
    updater = PackageUpdater()
    try:
        updater.run()
        # Save the conflict history
        if not os.path.exists("conflict_history"):
            os.makedirs("conflict_history")

        # Using defaultdict to group elements
        conflict_history = defaultdict(list)

        for pkg, dep, ver in updater.conflict_history:
            conflict_history[pkg].append({
                "dependency": dep,
                "version": ver
            })

        if len(conflict_history) > 0:
            current_time = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            conflict_history_file = current_time + "_conflict_history.json"
            with open(os.path.join("conflict_history", conflict_history_file), "w") as file:
                json.dump(conflict_history, file, indent=2)

            # Generate a requirements.txt file
            res = input("\n❓ Would you like to generate a requirements.txt file from the conflict packages? (Y/n) ")
            if res.strip().lower()!= "n":
                updater.generate_requirements(conflict_history_file)

        # Wait for user input before terminating
        updater._log_and_print("Script finished.", prefix="✅")
        input("\n🔑 Press any key to exit...")

    except KeyboardInterrupt:
        updater._log_and_print("\nScript terminated by user.", prefix="❌")

if __name__ == "__main__":
    main()