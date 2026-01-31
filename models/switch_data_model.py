"""
Model for storing and retrieving switch data for comparison.
"""
import os
import json
import pandas as pd
from datetime import datetime

class SwitchDataModel:
    """
    Handles storage and retrieval of switch interface and MAC data.
    
    Data is stored in both CSV files (for compatibility with existing scripts)
    and a JSON metadata file for easier access by the application.
    """
    
    def __init__(self, data_dir="saved_data"):
        """
        Initialize the switch data model.
        
        Args:
            data_dir (str): Directory to store saved data
        """
        self._data_dir = data_dir
        self._metadata_file = os.path.join(data_dir, "switch_data_metadata.json")
        self._metadata = {}
        self._observers = []
        
        # Ensure the data directory exists
        os.makedirs(data_dir, exist_ok=True)
        
        # Load metadata if it exists
        self._load_metadata()
    
    def _load_metadata(self):
        """Load metadata from file if it exists."""
        if os.path.exists(self._metadata_file):
            try:
                with open(self._metadata_file, 'r') as f:
                    self._metadata = json.load(f)
            except Exception:
                # If loading fails, start with empty metadata
                self._metadata = {}
    
    def _save_metadata(self):
        """Save metadata to file."""
        try:
            with open(self._metadata_file, 'w') as f:
                json.dump(self._metadata, f, indent=2)
        except Exception as e:
            print(f"Error saving metadata: {e}")
        
        # Notify observers
        self._notify_observers()
    
    def save_interface_data(self, switch_ip, hostname, interface_data):
        """
        Save interface data for a switch.
        
        Args:
            switch_ip (str): The switch IP address
            hostname (str): The switch hostname
            interface_data (list/DataFrame): Interface data to save
        
        Returns:
            str: The path to the saved file
        """
        # Convert to DataFrame if it's a list
        if isinstance(interface_data, list):
            df = pd.DataFrame(interface_data)
        else:
            df = interface_data
        
        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        filename = f"{hostname}_interfaces_{timestamp}.csv"
        filepath = os.path.join(self._data_dir, filename)
        
        # Save to CSV
        df.to_csv(filepath, index=False)
        
        # Update metadata
        if switch_ip not in self._metadata:
            self._metadata[switch_ip] = {"hostname": hostname, "data": []}
        
        # Add this capture to the metadata
        self._metadata[switch_ip]["data"].append({
            "type": "interfaces",
            "filename": filename,
            "timestamp": timestamp,
            "datetime": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "count": len(df)
        })
        
        self._save_metadata()
        return filepath
    
    def save_mac_data(self, switch_ip, hostname, mac_data):
        """
        Save MAC address data for a switch.
        
        Args:
            switch_ip (str): The switch IP address
            hostname (str): The switch hostname
            mac_data (list/DataFrame): MAC address data to save
        
        Returns:
            str: The path to the saved file
        """
        # Convert to DataFrame if it's a list
        if isinstance(mac_data, list):
            df = pd.DataFrame(mac_data)
        else:
            df = mac_data
        
        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        filename = f"{hostname}_mac_addresses_{timestamp}.csv"
        filepath = os.path.join(self._data_dir, filename)
        
        # Save to CSV
        df.to_csv(filepath, index=False)
        
        # Update metadata
        if switch_ip not in self._metadata:
            self._metadata[switch_ip] = {"hostname": hostname, "data": []}
        
        # Add this capture to the metadata
        self._metadata[switch_ip]["data"].append({
            "type": "mac_addresses",
            "filename": filename,
            "timestamp": timestamp,
            "datetime": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "count": len(df)
        })
        
        self._save_metadata()
        return filepath
    
    def get_saved_interface_captures(self, switch_ip=None):
        """
        Get saved interface data captures.
        
        Args:
            switch_ip (str, optional): Filter by switch IP
            
        Returns:
            list: List of interface captures with metadata
        """
        captures = []
        
        if switch_ip:
            # Get captures for a specific switch
            if switch_ip in self._metadata:
                for item in self._metadata[switch_ip]["data"]:
                    if item["type"] == "interfaces":
                        captures.append({
                            "switch_ip": switch_ip,
                            "hostname": self._metadata[switch_ip]["hostname"],
                            **item
                        })
        else:
            # Get all interface captures
            for ip, switch_data in self._metadata.items():
                for item in switch_data["data"]:
                    if item["type"] == "interfaces":
                        captures.append({
                            "switch_ip": ip,
                            "hostname": switch_data["hostname"],
                            **item
                        })
        
        # Sort by timestamp (newest first)
        captures.sort(key=lambda x: x["timestamp"], reverse=True)
        return captures
    
    def get_saved_mac_captures(self, switch_ip=None):
        """
        Get saved MAC address captures.
        
        Args:
            switch_ip (str, optional): Filter by switch IP
            
        Returns:
            list: List of MAC address captures with metadata
        """
        captures = []
        
        if switch_ip:
            # Get captures for a specific switch
            if switch_ip in self._metadata:
                for item in self._metadata[switch_ip]["data"]:
                    if item["type"] == "mac_addresses":
                        captures.append({
                            "switch_ip": switch_ip,
                            "hostname": self._metadata[switch_ip]["hostname"],
                            **item
                        })
        else:
            # Get all MAC address captures
            for ip, switch_data in self._metadata.items():
                for item in switch_data["data"]:
                    if item["type"] == "mac_addresses":
                        captures.append({
                            "switch_ip": ip,
                            "hostname": switch_data["hostname"],
                            **item
                        })
        
        # Sort by timestamp (newest first)
        captures.sort(key=lambda x: x["timestamp"], reverse=True)
        return captures
    
    def load_data_from_file(self, filename):
        """
        Load data from a saved CSV file.
        
        Args:
            filename (str): The filename to load
            
        Returns:
            DataFrame: The loaded data
        """
        filepath = os.path.join(self._data_dir, filename)
        if os.path.exists(filepath):
            return pd.read_csv(filepath)
        return None
    
    def add_observer(self, observer):
        """
        Add an observer for data changes.
        
        Args:
            observer: A function to call when data changes
        """
        if observer not in self._observers:
            self._observers.append(observer)
    
    def remove_observer(self, observer):
        """
        Remove an observer.
        
        Args:
            observer: The observer to remove
        """
        if observer in self._observers:
            self._observers.remove(observer)
    
    def _notify_observers(self):
        """Notify all observers of a change."""
        for observer in self._observers:
            observer()