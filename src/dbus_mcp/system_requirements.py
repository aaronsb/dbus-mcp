"""
System Requirements Checker

Checks for system-level Python packages that cannot be installed via pip
and must be installed through the system package manager.
"""

import importlib
import logging
import platform
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class SystemPackage:
    """Represents a system-level Python package requirement."""
    
    def __init__(
        self,
        import_name: str,
        package_names: Dict[str, str],
        description: str,
        required: bool = False,
        features: Optional[List[str]] = None
    ):
        self.import_name = import_name
        self.package_names = package_names  # Distro -> package name mapping
        self.description = description
        self.required = required
        self.features = features or []
    
    def check(self) -> Tuple[bool, Optional[str]]:
        """Check if the package is available."""
        try:
            importlib.import_module(self.import_name)
            return True, None
        except ImportError as e:
            return False, str(e)


# System packages registry
SYSTEM_PACKAGES = [
    SystemPackage(
        import_name="systemd",
        package_names={
            "arch": "python-systemd",
            "debian": "python3-systemd",
            "ubuntu": "python3-systemd",
            "fedora": "python3-systemd",
            "rhel": "python3-systemd",
            "centos": "python3-systemd",
            "opensuse": "python3-systemd",
        },
        description="Python bindings for systemd",
        required=False,
        features=["systemd service monitoring", "journal access", "socket activation"]
    ),
    # Future system packages can be added here:
    # SystemPackage(
    #     import_name="dbus",
    #     package_names={
    #         "arch": "python-dbus",
    #         "debian": "python3-dbus",
    #         ...
    #     },
    #     description="Python bindings for D-Bus",
    #     required=True
    # ),
]


def detect_distro() -> str:
    """Detect the Linux distribution."""
    try:
        # Try to read /etc/os-release
        with open('/etc/os-release', 'r') as f:
            for line in f:
                if line.startswith('ID='):
                    return line.strip().split('=')[1].strip('"').lower()
    except:
        pass
    
    # Fallback to platform
    dist = platform.linux_distribution()[0].lower()
    if 'debian' in dist or 'ubuntu' in dist:
        return 'debian'
    elif 'arch' in dist:
        return 'arch'
    elif 'fedora' in dist:
        return 'fedora'
    elif 'rhel' in dist or 'centos' in dist:
        return 'rhel'
    
    return 'unknown'


def check_system_requirements() -> Dict[str, Dict]:
    """
    Check all system requirements and return status.
    
    Returns:
        Dict with 'missing', 'optional_missing', and 'available' lists
    """
    distro = detect_distro()
    results = {
        'distro': distro,
        'missing': [],
        'optional_missing': [],
        'available': []
    }
    
    for package in SYSTEM_PACKAGES:
        available, error = package.check()
        
        if available:
            results['available'].append({
                'name': package.import_name,
                'description': package.description
            })
        else:
            missing_info = {
                'name': package.import_name,
                'description': package.description,
                'features': package.features,
                'install_command': get_install_command(distro, package),
                'error': error
            }
            
            if package.required:
                results['missing'].append(missing_info)
            else:
                results['optional_missing'].append(missing_info)
    
    return results


def get_install_command(distro: str, package: SystemPackage) -> str:
    """Get the installation command for a package on the given distro."""
    package_name = package.package_names.get(distro, package.package_names.get('debian', 'python3-' + package.import_name))
    
    if distro == 'arch':
        return f"sudo pacman -S {package_name}"
    elif distro in ['debian', 'ubuntu']:
        return f"sudo apt install {package_name}"
    elif distro in ['fedora']:
        return f"sudo dnf install {package_name}"
    elif distro in ['rhel', 'centos']:
        return f"sudo yum install {package_name}"
    elif distro == 'opensuse':
        return f"sudo zypper install {package_name}"
    else:
        return f"Install {package_name} using your system package manager"


def print_requirements_report():
    """Print a human-readable requirements report."""
    results = check_system_requirements()
    
    print("System Requirements Check")
    print("=" * 50)
    print(f"Detected Distribution: {results['distro']}")
    print()
    
    if results['missing']:
        print("❌ Required Packages Missing:")
        for pkg in results['missing']:
            print(f"  - {pkg['name']}: {pkg['description']}")
            print(f"    Install: {pkg['install_command']}")
            print()
    
    if results['optional_missing']:
        print("⚠️  Optional Packages Missing:")
        for pkg in results['optional_missing']:
            print(f"  - {pkg['name']}: {pkg['description']}")
            print(f"    Features: {', '.join(pkg['features'])}")
            print(f"    Install: {pkg['install_command']}")
            print()
    
    if results['available']:
        print("✅ Available Packages:")
        for pkg in results['available']:
            print(f"  - {pkg['name']}: {pkg['description']}")
    
    return len(results['missing']) == 0  # Return True if all required packages are available


def check_and_warn():
    """Check requirements and log warnings for missing packages."""
    results = check_system_requirements()
    
    if results['missing']:
        logger.error("Missing required system packages:")
        for pkg in results['missing']:
            logger.error(f"  - {pkg['name']}: {pkg['install_command']}")
        return False
    
    if results['optional_missing']:
        logger.info("Optional system packages not installed:")
        for pkg in results['optional_missing']:
            logger.info(f"  - {pkg['name']} ({', '.join(pkg['features'])}): {pkg['install_command']}")
    
    return True


if __name__ == "__main__":
    # Run as a standalone script to check requirements
    import sys
    if not print_requirements_report():
        sys.exit(1)