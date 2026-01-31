"""
Utility for loading external script modules dynamically.
"""

import importlib.util
import traceback
import sys
import os
from config.script_types import ScriptType

class ScriptLoader:
    """
    Handles loading of external script modules required by the application.
    """
    def __init__(self):
        """Initialize the script loader."""
        self.modules = {}
        self.script_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts")
        
    def get_script_path():
        """Get the path to the scripts directory, works both in development and when packaged."""
        if getattr(sys, 'frozen', False):
            # Running as an executable
            base_path = os.path.dirname(sys.executable)
        else:
            # Running in a normal Python environment
            base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        return os.path.join(base_path, 'scripts')
    
    def load_scripts(self):
        """
        Load all required script modules using ScriptType enum.

        Returns:
            dict: A dictionary of loaded modules or None if loading failed
        """
        try:
            # Define the scripts to load using ScriptType enum
            scripts = {
                ScriptType.COMPARE_INTERFACES: "compare_interface_status.py",
                ScriptType.COMPARE_MAC: "compare_mac_address_table.py",
                ScriptType.CONVERT: "convert_catalyst_to_meraki.py"  # Unified conversion script
            }

            # Load each script
            for script_type, filename in scripts.items():
                spec = importlib.util.spec_from_file_location(
                    script_type.name,
                    os.path.join(self.script_dir, filename)
                )
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                self.modules[script_type] = module

            return self.modules

        except Exception as e:
            print(f"Error loading scripts: {e}")
            traceback.print_exc()
            return None
    
    def get_module(self, script_type):
        """
        Get a loaded module by ScriptType.

        Args:
            script_type (ScriptType): The ScriptType enum value of the module to get

        Returns:
            module or None: The requested module or None if not found
        """
        if not isinstance(script_type, ScriptType):
            raise ValueError(f"Expected ScriptType enum, got {type(script_type)}")
        return self.modules.get(script_type)