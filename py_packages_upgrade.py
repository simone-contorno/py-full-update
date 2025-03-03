import subprocess
import datetime
import os

def upgradePip():
    """Upgrade pip to the latest version."""
    subprocess.run(["python", "-m", "pip", "install", "--upgrade", "pip"], check=True)

def listOutdatedPackages():
    """Returns a list of all outdated packages."""
    outdated = subprocess.run(["pip", "list", "--outdated"], capture_output=True, text=True)
    packages = [line.split(" ")[0] for line in outdated.stdout.split("\n") if line]

    # Remove headers
    if len(packages) > 2:
        packages = packages[2:]
    
    # Print the available packages
    for package in packages:
        print(package)

    return packages

def checkDependencyConflicts():
    """Check for existing dependency conflicts before upgrading."""
    
    result = subprocess.run(["pip", "check"], capture_output=True, text=True)
    
    if result.returncode != 0:
        return result.stdout.split("\n")
    
    return None

def upgradePackages(packages):
    """Upgrade packages while handling dependencies."""
    for package in packages:
        print(f"🔄 Updating: {package} ({packages.index(package) + 1}/{len(packages)})")

        # Create the output folder
        folder_name = "out" 
        if not os.path.exists(folder_name):
            os.makedirs(folder_name)

        # Upgrade package and save the output in a text file
        current_date_time = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        file_name = current_date_time + "output.txt"
        file_path = os.path.join(folder_name, file_name)
        with open(file_path, "a") as file:
            subprocess.run(["pip", "install", "--upgrade", package], check=True, stdout=file, stderr=file)

if __name__ == "__main__":
    print("\n🚀 Python Package Auto-Updater 🚀\n")

    res = input("Proceed with the full upgrade? (Y/n) ")
    if res.lower() == "n":
        exit(0)

    print("\n⬆️  Upgrading pip...")
    upgradePip()

    print("\n🔍 Checking for outdated packages...")
    outdated_packages = listOutdatedPackages()
    if outdated_packages:
        print(f"\n📦 Found {len(outdated_packages)} outdated packages.")

        # Check dependencies before upgrading
        existing_conflicts = checkDependencyConflicts()
        if existing_conflicts is not None:
            print("\n⚠️ WARNING: Dependency conflicts exist:")

            for conflict in existing_conflicts:
                print(f"    - {conflict}")
            
            res = input("Would you like to attempt a full upgrade to fix them? (Y/n) ")
            if res.lower() != "n":
                upgradePackages(outdated_packages)

                # Check again after updates
                print("\n🔄 Rechecking dependencies after upgrade...")
                
                conflicts_after = checkDependencyConflicts()
                if conflicts_after is not None:
                    print("\n⚠️ Some dependencies are still conflicting. Consider reinstalling:\n")
                    
                    for conflict in conflicts_after:
                        print(f"    - {conflict}")
                
                else:
                    print("\n✅ No dependency issues detected!")

            else:
                res = input("Would you like to attempt a full upgrade by skipping them? (Y/n) ")
                if res.lower() != "n":
                    
                    print("\n⚠️ Skipping existing dependency conflicts.")
                    
                    for outdated_package in outdated_packages:
                        if outdated_package in existing_conflicts:
                            print(f"    - Skipping: {outdated_package}")
                            outdated_packages.remove(outdated_package)
                    
                    upgradePackages(outdated_packages)
                    print("\n✅ All packages updated!")
        else:
            upgradePackages(outdated_packages)
        print("\n✅ All packages updated!")
    else:
        print("\n✅ No packages need updating.")

    input("\nPress any key to exit...")
