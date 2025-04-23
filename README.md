# Python Full Update

## Overview
This project provides tools for managing Python packages and virtual environments. It includes scripts for automating package updates and comprehensive virtual environment management with easy creation, activation, and dependency handling.

## Features

### Package Management
- Automatically creates a `logs/` directory and maintains timestamped logs.
- Loads configuration from `package_config.json`, allowing package blacklisting and specific version enforcement.
- Upgrades `pip` to the latest version.
- Lists all outdated packages.
- Checks for dependency conflicts before upgrading.
- Upgrades packages while considering blacklists and specific version constraints.
- Detects and suggests packages to add to the blacklist based on recurring dependency issues.
- Provides a detailed summary after upgrades.

### Virtual Environment Management
- **Create and manage** multiple Python virtual environments
- **Generate and update** requirements files for each environment
- **Install dependencies** from one environment to another
- **Quick activation** with Windows batch file aliases
- **Clean removal** of environments and their associated batch files

## Requirements
- Python 3.x
- `pip` (installed by default with Python)

## Installation
Clone this repository and navigate to the directory:

```bash
git clone https://github.com/simone-contorno/py-full-update
cd py-full-update
```

## Project Structure

```
py-full-update/
├── py_packages_update.py  # Package update script
├── py_env_manager.py      # Virtual environment management script
├── create_venv_alias.py   # Script to create batch file aliases for environments
├── package_config.json    # Configuration for package updates
├── venv/                  # Directory containing all virtual environments
│   ├── environments/      # Individual virtual environments
│   └── requirements/      # Requirements files for each environment
├── bat/                   # Directory containing batch file aliases
└── logs/                  # Logs from package update operations
```

## Configuration
Edit the `package_config.json` file to specify blacklisted packages and version-specific requirements:

```json
{
    "blacklist": [
        "package_name_1",
        "...", 
        "package_name_k"
    ],
    "specific_versions": {
        "package_name_k+1": "x.x.x",
        "...": "x.x.x",
        "package_name_n": "x.x.x",
    }
}
```

- `blacklist`: Packages in this list will not be upgraded.
- `specific_versions`: Specifies exact versions for certain packages.

## Usage

### Package Update Tool
Run the package update script with:

```bash
python py_packages_update.py
```

#### Main Functions
- **Logging**: All actions are logged in a timestamped file inside the logs/ directory.
- **Upgrade pip**: Ensures pip is at the latest version.
- **Check outdated packages**: Lists outdated packages using pip list --outdated.
- **Check dependency conflicts**: Uses pip check to identify dependency issues.
- **Upgrade packages**: Upgrades packages, skipping blacklisted ones and respecting specific version constraints.
- **Handle dependency issues**: Detects and suggests adding problematic packages to the blacklist.
- **Summary report**: Displays and logs a detailed report of successful, failed, and skipped upgrades.

### Virtual Environment Manager
Run the virtual environment management script to access the interactive menu:

```bash
python py_env_manager.py
```

This will display a menu with the following options:

1. **Create** a new virtual environment
2. **Activate** a virtual environment
3. **Deactivate** the active virtual environment
4. **Generate/Update** requirements.txt file
5. **Install dependencies** from requirements.txt
6. **Install dependencies** from one environment to another
7. **Delete** a virtual environment (also removes associated bat file)
8. **List** virtual environments
9. **Exit**

### Batch File Aliases
To create batch file aliases for quick activation of your environments:

```bash
python create_venv_alias.py
```

This will create `.bat` files in the `bat` directory that you can use to quickly activate environments by simply running the batch file.

Example:
```bash
.\bat\activate_myenv.bat
```

## Example Output
```plaintext
🔍 Checking for outdated packages...
📦 Found 5 outdated packages.
⬆️ Upgrading pip...
✅ pip upgraded to the latest version.
🔄 Updating: numpy (1/5)
✅ Successfully upgraded numpy
...
✅ Upgrade process completed!
```

## Error Handling
- If a package upgrade fails, the error message is logged.
- If dependency conflicts are detected, the user is prompted with options to resolve them.
- If the `package_config.json` file is missing, a default one is created.
- If logs cannot be written due to permission errors, the script provides troubleshooting suggestions.

## License
This project is open-source under the [MIT License](LICENSE).
