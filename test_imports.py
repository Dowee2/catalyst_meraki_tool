#!/usr/bin/env python3
"""
Import Verification Test Script
================================

This script tests that all modules can be imported correctly when the
catalyst_meraki_tool is run standalone (outside of the full Automation directory).

Run this from the catalyst_meraki_tool directory to verify imports work.

Usage:
    python test_imports.py
"""

import sys
import os
from pathlib import Path

# Color codes for terminal output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def print_header(text):
    """Print a header section."""
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}{text:^60}{RESET}")
    print(f"{BLUE}{'='*60}{RESET}\n")

def print_success(text):
    """Print a success message."""
    print(f"{GREEN}[OK] {text}{RESET}")

def print_error(text):
    """Print an error message."""
    print(f"{RED}[FAIL] {text}{RESET}")

def print_warning(text):
    """Print a warning message."""
    print(f"{YELLOW}[WARN] {text}{RESET}")

def print_info(text):
    """Print an info message."""
    print(f"{BLUE}[INFO] {text}{RESET}")


class ImportTester:
    """Tests all imports required by the catalyst_meraki_tool application."""

    def __init__(self):
        self.passed = []
        self.failed = []
        self.warnings = []

    def test_import(self, module_path, friendly_name, test_func=None):
        """
        Test importing a module.

        Args:
            module_path: Import path (e.g., 'config.constants')
            friendly_name: Human-readable name for the test
            test_func: Optional function to verify module contents
        """
        try:
            # Dynamic import
            module = __import__(module_path, fromlist=['*'])

            # Run additional verification if provided
            if test_func:
                test_func(module)

            self.passed.append(friendly_name)
            print_success(f"{friendly_name}: OK")
            return True

        except ImportError as e:
            self.failed.append((friendly_name, str(e)))
            print_error(f"{friendly_name}: FAILED")
            print(f"  Error: {e}")
            return False

        except Exception as e:
            self.warnings.append((friendly_name, str(e)))
            print_warning(f"{friendly_name}: WARNING")
            print(f"  {e}")
            return False

    def test_external_dependencies(self):
        """Test that external dependencies are available."""
        print_header("Testing External Dependencies")

        deps = [
            ('tkinter', 'Tkinter (GUI framework)'),
            ('meraki', 'Meraki Dashboard API'),
            ('netmiko', 'Netmiko (network automation)'),
            ('pandas', 'Pandas (data analysis)'),
        ]

        for module, name in deps:
            self.test_import(module, name)

    def test_config_modules(self):
        """Test config package imports."""
        print_header("Testing Config Package")

        # Test config package
        self.test_import('config', 'Config package')

        # Test constants
        def verify_constants(module):
            required = [
                'DEFAULT_DEVICE_TYPE',
                'DEFAULT_READ_TIMEOUT',
                'DEFAULT_MERAKI_PORT_CONFIG',
                'UPLINK_PORT_THRESHOLD'
            ]
            for const in required:
                if not hasattr(module, const):
                    raise AttributeError(f"Missing constant: {const}")

        self.test_import('config.constants', 'Config constants', verify_constants)

        # Test ScriptType enum
        def verify_script_types(module):
            if not hasattr(module, 'ScriptType'):
                raise AttributeError("Missing ScriptType enum")
            script_type = module.ScriptType
            required_types = ['CONVERT', 'COMPARE_INTERFACES', 'COMPARE_MAC']
            for st in required_types:
                if not hasattr(script_type, st):
                    raise AttributeError(f"Missing ScriptType.{st}")

        self.test_import('config.script_types', 'ScriptType enum', verify_script_types)

    def test_utils_modules(self):
        """Test utils package imports."""
        print_header("Testing Utils Package")

        # Test utils package
        self.test_import('utils', 'Utils package')

        # Test InterfaceParser
        def verify_interface_parser(module):
            if not hasattr(module, 'InterfaceParser'):
                raise AttributeError("Missing InterfaceParser class")
            parser = module.InterfaceParser
            required_methods = [
                'parse_interface',
                'is_valid_interface',
                'extract_port_number',
                'filter_interfaces'
            ]
            for method in required_methods:
                if not hasattr(parser, method):
                    raise AttributeError(f"Missing method: {method}")

        self.test_import('utils.interface_parser', 'InterfaceParser', verify_interface_parser)

        # Test port_config_builder
        def verify_port_config_builder(module):
            if not hasattr(module, 'build_meraki_port_config'):
                raise AttributeError("Missing build_meraki_port_config function")

        self.test_import('utils.port_config_builder', 'Port config builder', verify_port_config_builder)

        # Test script_loader
        def verify_script_loader(module):
            if not hasattr(module, 'ScriptLoader'):
                raise AttributeError("Missing ScriptLoader class")

        self.test_import('utils.script_loader', 'ScriptLoader', verify_script_loader)

        # Test workers
        self.test_import('utils.workers', 'Background workers')

        # Test console_redirect
        self.test_import('utils.console_redirect', 'Console redirect')

    def test_script_imports(self):
        """Test that scripts can import their dependencies."""
        print_header("Testing Script Modules")

        # Note: We can't fully import scripts without netmiko_utils in parent,
        # but we can verify the files exist and basic structure

        script_files = [
            'scripts.convert_catalyst_to_meraki',
            'scripts.compare_interface_status',
            'scripts.compare_mac_address_table'
        ]

        for script in script_files:
            module_name = script.split('.')[-1]
            # Just check if the module can be accessed
            try:
                __import__(script, fromlist=['run'])
                print_success(f"Script: {module_name}")
                self.passed.append(f"Script: {module_name}")
            except ImportError as e:
                if "netmiko_utils" in str(e):
                    print_warning(f"Script: {module_name} (needs netmiko_utils from parent)")
                    self.warnings.append((f"Script: {module_name}", "Requires netmiko_utils"))
                else:
                    print_error(f"Script: {module_name}")
                    print(f"  Error: {e}")
                    self.failed.append((f"Script: {module_name}", str(e)))

    def test_controller_imports(self):
        """Test controller imports."""
        print_header("Testing Controller Modules")

        controllers = [
            'controllers.app_controller',
            'controllers.settings_controller',
            'controllers.conversion_controller',
            'controllers.comparison_controller'
        ]

        for controller in controllers:
            name = controller.split('.')[-1]
            self.test_import(controller, f"Controller: {name}")

    def test_model_imports(self):
        """Test model imports."""
        print_header("Testing Model Modules")

        models = [
            'models.credentials_model',
            'models.serials_model',
            'models.progress_model',
            'models.switch_data_model'
        ]

        for model in models:
            name = model.split('.')[-1]
            self.test_import(model, f"Model: {name}")

    def test_view_imports(self):
        """Test view imports."""
        print_header("Testing View Modules")

        views = [
            'views.main_window',
            'views.conversion_view',
            'views.interface_compare_view',
            'views.mac_compare_view',
            'views.settings_view'
        ]

        for view in views:
            name = view.split('.')[-1]
            self.test_import(view, f"View: {name}")

    def print_summary(self):
        """Print test summary."""
        print_header("Test Summary")

        total = len(self.passed) + len(self.failed) + len(self.warnings)

        print(f"Total tests: {total}")
        print(f"{GREEN}Passed: {len(self.passed)}{RESET}")
        print(f"{YELLOW}Warnings: {len(self.warnings)}{RESET}")
        print(f"{RED}Failed: {len(self.failed)}{RESET}")

        if self.warnings:
            print(f"\n{YELLOW}Warnings:{RESET}")
            for name, msg in self.warnings:
                print(f"  - {name}: {msg}")

        if self.failed:
            print(f"\n{RED}Failures:{RESET}")
            for name, msg in self.failed:
                print(f"  - {name}")
                print(f"    {msg}")
            print(f"\n{RED}IMPORT TEST FAILED - Application may not run correctly{RESET}")
            return False
        else:
            if self.warnings:
                print(f"\n{GREEN}All critical imports passed!{RESET}")
                print(f"{YELLOW}Some warnings present - review above{RESET}")
            else:
                print(f"\n{GREEN}ALL IMPORTS PASSED!{RESET}")
            return True


def main():
    """Run all import tests."""
    print_header("Catalyst-Meraki Tool Import Verification")

    # Print environment info
    print_info(f"Python: {sys.version}")
    print_info(f"Working directory: {os.getcwd()}")
    print_info(f"Script location: {__file__}")

    # Check we're in the right directory
    expected_path = Path(__file__).parent
    if not (expected_path / 'config').exists():
        print_error("Not in catalyst_meraki_tool directory!")
        print_error("Please run this script from the catalyst_meraki_tool root directory")
        return 1

    # Run tests
    tester = ImportTester()

    tester.test_external_dependencies()
    tester.test_config_modules()
    tester.test_utils_modules()
    tester.test_script_imports()
    tester.test_controller_imports()
    tester.test_model_imports()
    tester.test_view_imports()

    # Print summary
    success = tester.print_summary()

    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())
