#!/usr/bin/env python3
"""
Refresh Wemo device configuration.
Rediscover Wemo devices on the local network and update config/wemo_config.yaml.
"""

import sys
import os
import yaml
from pathlib import Path

# Add the project root to the import path.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pywemo

def discover_devices():
    """Discover all Wemo devices."""
    print("Scanning local network for Wemo devices...")
    devices = pywemo.discover_devices()
    
    if not devices:
        print("No Wemo devices found")
        return []
    
    print(f"Found {len(devices)} devices:")
    device_list = []
    for device in devices:
        device_info = {
            'name': device.name,
            'host': device.host,
            'port': device.port,
            'type': type(device).__name__
        }
        device_list.append(device_info)
        print(f"  - {device.name} ({device.host}:{device.port}) - {device_info['type']}")
    
    return device_list

def load_existing_config(config_path):
    """Load an existing config file."""
    if not config_path.exists():
        print(f"Config file does not exist: {config_path}")
        return None
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        print(f"Loaded existing config: {config_path}")
        return config
    except Exception as e:
        print(f"Error reading config file: {str(e)}", file=sys.stderr)
        return None

def update_config_with_devices(config, devices):
    """Update config with discovered device information."""
    if config is None:
        # Create a new config.
        config = {
            'devices': [],
            'schedule': {
                'timezone': 'Pacific',
                'tasks': []
            }
        }
    
    # Update device info and preserve optional fields like description.
    existing_devices = {d['name'].lower(): d for d in config.get('devices', [])}
    
    updated_devices = []
    for device in devices:
        device_name_lower = device['name'].lower()
        if device_name_lower in existing_devices:
            # Preserve optional fields from the existing device.
            existing = existing_devices[device_name_lower]
            updated_device = {
                'name': device['name'],
                'host': device['host'],
                'port': device['port'],
                'type': device['type']
            }
            # Preserve optional fields.
            if 'description' in existing:
                updated_device['description'] = existing['description']
            updated_devices.append(updated_device)
            print(f"Updated device: {device['name']}")
        else:
            # New device.
            updated_devices.append(device)
            print(f"Added new device: {device['name']}")
    
    config['devices'] = updated_devices
    
    # Ensure the schedule section exists.
    if 'schedule' not in config:
        config['schedule'] = {
            'timezone': 'Pacific',
            'tasks': []
        }
    
    return config

def save_config(config, config_path):
    """Save config to disk."""
    try:
        # Create backup.
        if config_path.exists():
            backup_path = config_path.with_suffix('.yaml.bak')
            import shutil
            shutil.copy2(config_path, backup_path)
            print(f"Created backup: {backup_path}")
        
        # Save new config.
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
        print(f"Config saved: {config_path}")
        return True
    except Exception as e:
        print(f"Error saving config file: {str(e)}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        return False

def main():
    """Run the refresh command."""
    # Determine config file path.
    project_root = Path(__file__).parent.parent
    config_path = project_root / 'config' / 'wemo_config.yaml'
    
    # Allow an environment override for the config file path.
    config_file_env = os.getenv('WEMO_CONFIG_FILE')
    if config_file_env:
        config_path = Path(config_file_env)
        if not config_path.is_absolute():
            config_path = project_root / config_path
    
    print("=" * 60)
    print("Wemo device config refresh tool")
    print("=" * 60)
    print(f"Config file: {config_path}")
    print()
    
    # Discover devices.
    devices = discover_devices()
    
    if not devices:
        print("\nNo devices found; cannot update config")
        sys.exit(1)
    
    print()
    
    # Load existing config.
    config = load_existing_config(config_path)
    
    # Update config.
    print("\nUpdating config...")
    config = update_config_with_devices(config, devices)
    
    # Save config.
    print("\nSaving config...")
    if save_config(config, config_path):
        print("\nConfig update complete!")
        print("\nNote: restart the server for config changes to take effect")
        sys.exit(0)
    else:
        print("\nConfig update failed")
        sys.exit(1)

if __name__ == "__main__":
    main()
