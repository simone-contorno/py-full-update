# Python Full Update

## Overview
This script automates the process of checking, managing, and upgrading Python packages using `pip`. It includes advanced features such as logging, blacklisting problematic packages, handling dependency conflicts, and enforcing specific package versions.

## Features
- Automatically creates a `logs/` directory and maintains timestamped logs.
- Loads configuration from `package_config.json`, allowing package blacklisting and specific version enforcement.
- Upgrades `pip` to the latest version.
- Lists all outdated packages.
- Checks for dependency conflicts before upgrading.
- Upgrades packages while considering blacklists and specific version constraints.
- Detects and suggests packages to add to the blacklist based on recurring dependency issues.
- Provides a detailed summary after upgrades.

## Requirements
- Python 3.x
- `pip` (installed by default with Python)

## Installation
Clone this repository and navigate to the directory:

```bash
git clone https://github.com/simone-contorno/py-full-update
cd py-full-update
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
Run the script with:

```bash
python py_packages_update.py
```

### Main Functions
- **Logging**: All actions are logged in a timestamped file inside the logs/ directory.
- **Upgrade pip**: Ensures pip is at the latest version.
- **Check outdated packages**: Lists outdated packages using pip list --outdated.
- **Check dependency conflicts**: Uses pip check to identify dependency issues.
- **Upgrade packages**: Upgrades packages, skipping blacklisted ones and respecting specific version constraints.
- **Handle dependency issues**: Detects and suggests adding problematic packages to the blacklist.
- **Summary report**: Displays and logs a detailed report of successful, failed, and skipped upgrades.

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
