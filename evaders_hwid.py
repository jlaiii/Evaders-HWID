#!/usr/bin/env python3
"""
Evaders HWID
Main menu system with HWID collection, comparison, and settings management
All data saved to data folder with comprehensive logging

NOTE: This code does not use emojis. Emojis should never be used in this codebase.
"""

import subprocess
import json
import platform
import uuid
import socket
import sys
import os
import logging
import threading
import time
import queue
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict

def install_dependencies():
    """Auto-install required dependencies"""
    required_packages = ['psutil']
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            print(f"Installing {package}...")
            try:
                subprocess.check_call([sys.executable, '-m', 'pip', 'install', package], 
                                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                print(f"Successfully installed {package}")
            except subprocess.CalledProcessError:
                print(f"Trying alternative installation method...")
                try:
                    subprocess.check_call([sys.executable, '-m', 'pip', 'install', '--user', package],
                                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    print(f"Successfully installed {package}")
                except subprocess.CalledProcessError:
                    print(f"Could not install {package}. Some features may be limited.")
                    print("Continuing anyway...")

# Install dependencies first
print("Initializing Evaders HWID...")
install_dependencies()

# Now import the installed packages
try:
    import psutil
except ImportError:
    print("Warning: psutil not available. Some system information will be limited.")
    psutil = None

# Setup logging and data directory
def setup_logging():
    """Setup logging configuration"""
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)
    
    log_file = data_dir / "evaders_hwid.log"
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

# Settings management
class SettingsManager:
    def __init__(self):
        self.data_dir = Path("data")
        self.data_dir.mkdir(exist_ok=True)
        self.settings_file = self.data_dir / "settings.json"
        self.logger = logging.getLogger(__name__)
        self.settings = self.load_settings()
    
    def load_settings(self):
        """Load settings from JSON file"""
        default_settings = {
            "auto_save_reports": True,
            "compare_on_startup": False,
            "detailed_logging": True,
            "backup_reports": True,
            "max_reports": 10,
            "banned_hwids": [],
            "ban_simulator_enabled": True,
            "background_monitoring": False,  # Off by default, needs to be enabled in settings
            "monitoring_interval": 300,  # 5 minutes
            "stats_tracking": True,
            "auto_start_windows": False  # Windows startup option
        }
        
        try:
            if self.settings_file.exists():
                with open(self.settings_file, 'r') as f:
                    settings = json.load(f)
                    # Merge with defaults for any missing keys
                    for key, value in default_settings.items():
                        if key not in settings:
                            settings[key] = value
                    self.logger.info("Settings loaded from file")
                    return settings
            else:
                self.logger.info("Creating default settings file")
                self.save_settings(default_settings)
                return default_settings
        except Exception as e:
            self.logger.error(f"Error loading settings: {e}")
            return default_settings
    
    def save_settings(self, settings=None):
        """Save settings to JSON file"""
        if settings:
            self.settings = settings
        
        try:
            with open(self.settings_file, 'w') as f:
                json.dump(self.settings, f, indent=2)
            self.logger.info("Settings saved to file")
        except Exception as e:
            self.logger.error(f"Error saving settings: {e}")
    
    def get(self, key, default=None):
        """Get setting value"""
        return self.settings.get(key, default)
    
    def set(self, key, value):
        """Set setting value"""
        self.settings[key] = value
        self.save_settings()

# Windows Auto-Start Manager
class WindowsStartupManager:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.app_name = "Evaders_HWID"
        self.script_path = os.path.abspath(__file__)
        
    def is_windows(self):
        """Check if running on Windows"""
        return platform.system() == 'Windows'
    
    def get_startup_registry_key(self):
        """Get Windows startup registry key path"""
        return r"HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Run"
    
    def is_auto_start_enabled(self):
        """Check if auto-start is currently enabled"""
        if not self.is_windows():
            return False
            
        try:
            result = subprocess.run([
                'reg', 'query', self.get_startup_registry_key(), 
                '/v', self.app_name
            ], capture_output=True, text=True, shell=True)
            
            return result.returncode == 0
        except Exception as e:
            self.logger.error(f"Error checking auto-start status: {e}")
            return False
    
    def enable_auto_start(self):
        """Enable auto-start with Windows"""
        if not self.is_windows():
            return False, "Auto-start is only available on Windows"
            
        try:
            # Create registry entry to start with Windows
            python_exe = sys.executable
            command = f'"{python_exe}" "{self.script_path}"'
            
            result = subprocess.run([
                'reg', 'add', self.get_startup_registry_key(),
                '/v', self.app_name,
                '/t', 'REG_SZ',
                '/d', command,
                '/f'
            ], capture_output=True, text=True, shell=True)
            
            if result.returncode == 0:
                self.logger.info("Auto-start enabled successfully")
                return True, "Auto-start with Windows enabled"
            else:
                self.logger.error(f"Failed to enable auto-start: {result.stderr}")
                return False, f"Failed to enable auto-start: {result.stderr}"
                
        except Exception as e:
            self.logger.error(f"Error enabling auto-start: {e}")
            return False, f"Error enabling auto-start: {e}"
    
    def disable_auto_start(self):
        """Disable auto-start with Windows"""
        if not self.is_windows():
            return False, "Auto-start is only available on Windows"
            
        try:
            result = subprocess.run([
                'reg', 'delete', self.get_startup_registry_key(),
                '/v', self.app_name,
                '/f'
            ], capture_output=True, text=True, shell=True)
            
            if result.returncode == 0:
                self.logger.info("Auto-start disabled successfully")
                return True, "Auto-start with Windows disabled"
            else:
                # If the key doesn't exist, that's also success
                if "cannot find" in result.stderr.lower():
                    return True, "Auto-start was already disabled"
                self.logger.error(f"Failed to disable auto-start: {result.stderr}")
                return False, f"Failed to disable auto-start: {result.stderr}"
                
        except Exception as e:
            self.logger.error(f"Error disabling auto-start: {e}")
            return False, f"Error disabling auto-start: {e}"

# Statistics Manager for HWID Change Tracking
class HWIDStatsManager:
    def __init__(self):
        self.data_dir = Path("data")
        self.data_dir.mkdir(exist_ok=True)
        self.stats_file = self.data_dir / "hwid_stats.json"
        self.logger = logging.getLogger(__name__)
        self.stats = self.load_stats()
    
    def load_stats(self):
        """Load statistics from JSON file"""
        default_stats = {
            "total_checks": 0,
            "total_changes": 0,
            "first_check": None,
            "last_check": None,
            "last_change": None,
            "change_history": [],  # List of change events with timestamps
            "monthly_stats": {},   # Monthly aggregated data
            "daily_checks": {},    # Daily check counts
            "hwid_hashes": []      # History of HWID hashes
        }
        
        try:
            if self.stats_file.exists():
                with open(self.stats_file, 'r') as f:
                    stats = json.load(f)
                    # Merge with defaults for any missing keys
                    for key, value in default_stats.items():
                        if key not in stats:
                            stats[key] = value
                    self.logger.info("HWID statistics loaded from file")
                    return stats
            else:
                self.logger.info("Creating default statistics file")
                self.save_stats(default_stats)
                return default_stats
        except Exception as e:
            self.logger.error(f"Error loading statistics: {e}")
            return default_stats
    
    def save_stats(self, stats=None):
        """Save statistics to JSON file"""
        if stats:
            self.stats = stats
        
        try:
            with open(self.stats_file, 'w') as f:
                json.dump(self.stats, f, indent=2)
            self.logger.info("HWID statistics saved to file")
        except Exception as e:
            self.logger.error(f"Error saving statistics: {e}")
    
    def record_check(self, hwid_hash, changed=False):
        """Record an HWID check and whether it changed"""
        now = datetime.now()
        timestamp = now.isoformat()
        date_key = now.strftime('%Y-%m-%d')
        month_key = now.strftime('%Y-%m')
        
        # Update basic counters
        self.stats['total_checks'] += 1
        self.stats['last_check'] = timestamp
        
        if self.stats['first_check'] is None:
            self.stats['first_check'] = timestamp
        
        # Update daily check count
        if date_key not in self.stats['daily_checks']:
            self.stats['daily_checks'][date_key] = 0
        self.stats['daily_checks'][date_key] += 1
        
        # Initialize monthly stats if needed
        if month_key not in self.stats['monthly_stats']:
            self.stats['monthly_stats'][month_key] = {
                'checks': 0,
                'changes': 0,
                'unique_hwids': set()
            }
        
        self.stats['monthly_stats'][month_key]['checks'] += 1
        self.stats['monthly_stats'][month_key]['unique_hwids'].add(hwid_hash)
        
        # Record HWID hash
        if hwid_hash not in self.stats['hwid_hashes']:
            self.stats['hwid_hashes'].append(hwid_hash)
        
        # Handle changes
        if changed:
            self.stats['total_changes'] += 1
            self.stats['last_change'] = timestamp
            self.stats['monthly_stats'][month_key]['changes'] += 1
            
            # Record change event
            change_event = {
                'timestamp': timestamp,
                'new_hwid_hash': hwid_hash,
                'check_number': self.stats['total_checks']
            }
            self.stats['change_history'].append(change_event)
            
            self.logger.warning(f"HWID change detected! Total changes: {self.stats['total_changes']}")
        
        # Convert sets to lists for JSON serialization
        for month_data in self.stats['monthly_stats'].values():
            if isinstance(month_data['unique_hwids'], set):
                month_data['unique_hwids'] = list(month_data['unique_hwids'])
        
        self.save_stats()
    
    def get_change_frequency(self):
        """Calculate average changes per month"""
        if not self.stats['first_check'] or self.stats['total_changes'] == 0:
            return 0
        
        first_check = datetime.fromisoformat(self.stats['first_check'])
        last_check = datetime.fromisoformat(self.stats['last_check'])
        
        # Calculate months between first and last check
        months_diff = (last_check.year - first_check.year) * 12 + (last_check.month - first_check.month)
        if months_diff == 0:
            months_diff = 1  # At least 1 month for calculation
        
        return round(self.stats['total_changes'] / months_diff, 2)
    
    def get_monthly_summary(self):
        """Get monthly statistics summary"""
        summary = {}
        for month, data in self.stats['monthly_stats'].items():
            summary[month] = {
                'checks': data['checks'],
                'changes': data['changes'],
                'unique_hwids': len(data['unique_hwids']),
                'change_rate': round((data['changes'] / data['checks']) * 100, 2) if data['checks'] > 0 else 0
            }
        return summary
    
    def display_statistics(self):
        """Display comprehensive HWID change statistics"""
        print("\n" + "="*70)
        print("           HWID CHANGE STATISTICS")
        print("="*70)
        
        if self.stats['total_checks'] == 0:
            print("No HWID checks recorded yet.")
            print("="*70)
            return
        
        # Basic stats
        print(f"\nOVERALL STATISTICS:")
        print(f"  Total HWID Checks: {self.stats['total_checks']}")
        print(f"  Total HWID Changes: {self.stats['total_changes']}")
        print(f"  Unique HWIDs Seen: {len(self.stats['hwid_hashes'])}")
        
        if self.stats['first_check']:
            first_check = datetime.fromisoformat(self.stats['first_check'])
            print(f"  First Check: {first_check.strftime('%Y-%m-%d %H:%M:%S')}")
        
        if self.stats['last_check']:
            last_check = datetime.fromisoformat(self.stats['last_check'])
            print(f"  Last Check: {last_check.strftime('%Y-%m-%d %H:%M:%S')}")
        
        if self.stats['last_change']:
            last_change = datetime.fromisoformat(self.stats['last_change'])
            print(f"  Last Change: {last_change.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Change frequency
        avg_changes = self.get_change_frequency()
        print(f"  Average Changes/Month: {avg_changes}")
        
        # Change rate
        if self.stats['total_checks'] > 0:
            change_rate = (self.stats['total_changes'] / self.stats['total_checks']) * 100
            print(f"  Change Rate: {change_rate:.2f}%")
        
        # Monthly breakdown
        monthly_summary = self.get_monthly_summary()
        if monthly_summary:
            print(f"\nMONTHLY BREAKDOWN:")
            for month in sorted(monthly_summary.keys(), reverse=True)[:6]:  # Last 6 months
                data = monthly_summary[month]
                print(f"  {month}: {data['checks']} checks, {data['changes']} changes ({data['change_rate']}%), {data['unique_hwids']} unique HWIDs")
        
        # Recent changes
        if self.stats['change_history']:
            print(f"\nRECENT CHANGES (Last 5):")
            recent_changes = sorted(self.stats['change_history'], 
                                  key=lambda x: x['timestamp'], reverse=True)[:5]
            for change in recent_changes:
                timestamp = datetime.fromisoformat(change['timestamp'])
                print(f"  {timestamp.strftime('%Y-%m-%d %H:%M:%S')} - Check #{change['check_number']}")
        
        print("="*70)

def run_wmi_query(wmi_class, properties):
    """Execute WMI query using PowerShell Get-CimInstance and return results"""
    try:
        # Build PowerShell command using Get-CimInstance (modern replacement for wmic)
        ps_command = f"Get-CimInstance -ClassName {wmi_class} | Select-Object {properties} | Format-List"
        
        result = subprocess.run(
            ['powershell', '-Command', ps_command],
            capture_output=True,
            text=True,
            shell=False
        )
        
        if result.returncode == 0:
            return result.stdout.strip()
        else:
            return f"Error: {result.stderr.strip()}"
    except Exception as e:
        return f"Error: {str(e)}"

def parse_wmi_output(wmi_text):
    """Parse PowerShell Format-List output into clean key-value pairs, handling multiple objects"""
    if not wmi_text or "Error:" in wmi_text:
        return {}
    
    results = []
    current_object = {}
    lines = wmi_text.split('\n')
    
    for line in lines:
        line = line.strip()
        
        # Empty line indicates end of an object
        if not line:
            if current_object:
                results.append(current_object)
                current_object = {}
            continue
            
        # PowerShell Format-List uses ' : ' as separator
        if ' : ' in line:
            key, value = line.split(' : ', 1)
            key = key.strip()
            value = value.strip()
            if value and value != "" and value != "{}":
                current_object[key] = value
        # Also handle '=' format for compatibility
        elif '=' in line and not line.startswith('='):
            key, value = line.split('=', 1)
            key = key.strip()
            value = value.strip()
            if value and value != "":
                current_object[key] = value
    
    # Add the last object if it exists
    if current_object:
        results.append(current_object)
    
    # If only one object, return it directly for backward compatibility
    # If multiple objects, return the list
    if len(results) == 1:
        return results[0]
    elif len(results) > 1:
        return results
    else:
        return {}

def get_core_hwid_info():
    """Get core HWID information"""
    print("Gathering core HWID information...")
    hwid_info = {}
    
    # 1. Disk Drive (model, serialnumber)
    hwid_info['diskdrive'] = run_wmi_query("Win32_DiskDrive", "Model,SerialNumber")
    
    # 2. CPU (serialnumber)
    hwid_info['cpu_serial'] = run_wmi_query("Win32_Processor", "SerialNumber")
    
    # 3. BIOS (serialnumber)
    hwid_info['bios_serial'] = run_wmi_query("Win32_BIOS", "SerialNumber")
    
    # 4. Motherboard (serialnumber)
    hwid_info['motherboard_serial'] = run_wmi_query("Win32_BaseBoard", "SerialNumber")
    
    # 5. smBIOS UUID
    hwid_info['smbios_uuid'] = run_wmi_query("Win32_ComputerSystemProduct", "UUID")
    
    # 6. MAC Addresses (getmac equivalent)
    try:
        result = subprocess.run(
            ['powershell', '-Command', 'Get-NetAdapter | Where-Object {$_.Status -eq "Up"} | Select-Object Name, MacAddress | Format-List'],
            capture_output=True,
            text=True,
            shell=False
        )
        hwid_info['mac_addresses'] = result.stdout.strip() if result.returncode == 0 else "Error getting MAC addresses"
    except Exception as e:
        hwid_info['mac_addresses'] = f"Error: {str(e)}"
    
    return hwid_info

def get_system_info():
    """Get comprehensive system information"""
    print("Gathering system information...")
    system_info = {}
    
    # Basic system info
    system_info['hostname'] = socket.gethostname()
    system_info['platform'] = platform.platform()
    system_info['system'] = platform.system()
    system_info['release'] = platform.release()
    system_info['version'] = platform.version()
    system_info['machine_id'] = str(uuid.getnode())
    system_info['node'] = platform.node()
    
    # Windows version details
    wmi_os = run_wmi_query("Win32_OperatingSystem", "Caption,Version,BuildNumber,SerialNumber,InstallDate,RegisteredUser")
    system_info['operating_system'] = wmi_os
    
    return system_info

def get_cpu_info():
    """Get comprehensive CPU information and serial numbers"""
    print("Gathering CPU information...")
    cpu_info = {}
    
    # Basic CPU info
    cpu_info['name'] = platform.processor()
    cpu_info['architecture'] = platform.machine()
    
    if psutil:
        cpu_info['cores'] = psutil.cpu_count(logical=False)
        cpu_info['threads'] = psutil.cpu_count(logical=True)
    else:
        cpu_info['cores'] = "N/A (psutil not available)"
        cpu_info['threads'] = "N/A (psutil not available)"
    
    # Comprehensive CPU details via WMI
    wmi_cpu = run_wmi_query("Win32_Processor", "Name,ProcessorId,Manufacturer,MaxClockSpeed,Family,Model,Stepping,Description")
    cpu_info['wmi_details'] = wmi_cpu
    
    return cpu_info

def get_memory_info():
    """Get comprehensive RAM information and serial numbers"""
    print("Gathering RAM information...")
    memory_info = {}
    
    # Basic memory info
    if psutil:
        mem = psutil.virtual_memory()
        memory_info['total_gb'] = round(mem.total / (1024**3), 2)
    else:
        memory_info['total_gb'] = "N/A (psutil not available)"
    
    # Comprehensive RAM info via WMI
    wmi_ram = run_wmi_query("Win32_PhysicalMemory", "Capacity,Speed,Manufacturer,PartNumber,SerialNumber,DeviceLocator,BankLabel,MemoryType,TypeDetail")
    memory_info['modules'] = wmi_ram
    
    return memory_info

def get_storage_info():
    """Get comprehensive storage device information and serial numbers"""
    print("Gathering storage information...")
    storage_info = {}
    
    # Disk usage
    if psutil:
        partitions = psutil.disk_partitions()
        storage_info['partitions'] = []
        
        for partition in partitions:
            try:
                usage = psutil.disk_usage(partition.mountpoint)
                storage_info['partitions'].append({
                    'device': partition.device,
                    'mountpoint': partition.mountpoint,
                    'fstype': partition.fstype,
                    'total_gb': round(usage.total / (1024**3), 2),
                    'used_gb': round(usage.used / (1024**3), 2),
                    'free_gb': round(usage.free / (1024**3), 2)
                })
            except PermissionError:
                continue
    
    # Comprehensive physical drives via WMI
    wmi_drives = run_wmi_query("Win32_DiskDrive", "Model,SerialNumber,Size,MediaType,InterfaceType,Partitions,Manufacturer")
    storage_info['physical_drives'] = wmi_drives
    
    return storage_info

def get_network_info():
    """Get comprehensive network adapter information and MAC addresses"""
    print("Gathering network information...")
    network_info = {}
    
    # Network interfaces
    if psutil:
        interfaces = psutil.net_if_addrs()
        network_info['interfaces'] = {}
        
        for interface_name, addresses in interfaces.items():
            interface_info = []
            for addr in addresses:
                if hasattr(psutil, 'AF_LINK') and addr.family == psutil.AF_LINK:  # MAC address
                    interface_info.append({
                        'type': 'MAC',
                        'address': addr.address
                    })
                elif addr.family == socket.AF_INET:  # IPv4
                    interface_info.append({
                        'type': 'IPv4',
                        'address': addr.address,
                        'netmask': addr.netmask
                    })
            network_info['interfaces'][interface_name] = interface_info
    else:
        network_info['interfaces'] = "N/A (psutil not available)"
    
    # Comprehensive network adapters via WMI
    wmi_network = run_wmi_query("Win32_NetworkAdapter", "Name,MACAddress,PNPDeviceID,Manufacturer,ProductName")
    network_info['wmi_adapters'] = wmi_network
    
    return network_info

def get_motherboard_bios_info():
    """Get comprehensive motherboard and BIOS information with all serial numbers"""
    print("Gathering comprehensive motherboard and BIOS information...")
    mb_bios_info = {}
    
    # Comprehensive motherboard info via WMI
    wmi_mb = run_wmi_query("Win32_BaseBoard", "Manufacturer,Product,SerialNumber,Version,Model,PartNumber,Tag")
    mb_bios_info['motherboard'] = wmi_mb
    
    # Comprehensive BIOS info
    wmi_bios = run_wmi_query("Win32_BIOS", "Manufacturer,SMBIOSBIOSVersion,SerialNumber,Version,ReleaseDate,BIOSVersion,Name")
    mb_bios_info['bios'] = wmi_bios
    
    # Computer system product info (includes system serial)
    wmi_product = run_wmi_query("Win32_ComputerSystemProduct", "Name,Vendor,Version,SerialNumber,UUID,IdentifyingNumber")
    mb_bios_info['system_product'] = wmi_product
    
    return mb_bios_info

def get_gpu_info():
    """Get comprehensive GPU information"""
    print("Gathering GPU information...")
    gpu_info = {}
    
    # Comprehensive GPU via WMI
    wmi_gpu = run_wmi_query("Win32_VideoController", "Name,PNPDeviceID,AdapterRAM,DriverVersion,DriverDate,VideoProcessor")
    gpu_info['video_controllers'] = wmi_gpu
    
    return gpu_info

def get_usb_devices():
    """Get USB device information and serial numbers"""
    print("Gathering USB device information...")
    usb_info = {}
    
    # USB devices
    wmi_usb = run_wmi_query("Win32_USBHub", "Name,DeviceID,Description")
    usb_info['usb_hubs'] = wmi_usb
    
    return usb_info

def get_audio_devices():
    """Get audio device information"""
    print("Gathering audio device information...")
    audio_info = {}
    
    # Sound devices
    wmi_sound = run_wmi_query("Win32_SoundDevice", "Name,DeviceID,Manufacturer")
    audio_info['sound_devices'] = wmi_sound
    
    return audio_info

def get_system_slots():
    """Get system slot information"""
    print("Gathering system slot information...")
    slot_info = {}
    
    # System slots (PCI, PCIe, etc.)
    wmi_slots = run_wmi_query("Win32_SystemSlot", "SlotDesignation,CurrentUsage,SlotType,MaxDataWidth")
    slot_info['system_slots'] = wmi_slots
    
    return slot_info

def get_tpm_info():
    """Get TPM (Trusted Platform Module) information"""
    print("Gathering TPM information...")
    tpm_info = {}
    
    # TPM information
    wmi_tpm = run_wmi_query("Win32_Tpm", "SpecVersion,ManufacturerVersion,ManufacturerVersionInfo")
    tpm_info['tpm_details'] = wmi_tpm
    
    return tpm_info

def display_core_hwid(hwid_data):
    """Display core HWID information"""
    print("\n" + "="*70)
    print("           CORE HARDWARE ID INFORMATION")
    print("="*70)
    
    # Disk Drive
    print("\nDISK DRIVE:")
    if 'diskdrive' in hwid_data:
        disk_data = parse_wmi_output(hwid_data['diskdrive'])
        if isinstance(disk_data, list):
            for i, disk in enumerate(disk_data, 1):
                if 'Model' in disk:
                    print(f"  Drive {i} Model: {disk['Model']}")
                if 'SerialNumber' in disk:
                    print(f"  Drive {i} Serial: {disk['SerialNumber']}")
        elif isinstance(disk_data, dict):
            if 'Model' in disk_data:
                print(f"  Model: {disk_data['Model']}")
            if 'SerialNumber' in disk_data:
                print(f"  Serial: {disk_data['SerialNumber']}")
    
    # CPU Serial
    print("\nCPU:")
    if 'cpu_serial' in hwid_data:
        cpu_data = parse_wmi_output(hwid_data['cpu_serial'])
        if isinstance(cpu_data, dict) and 'SerialNumber' in cpu_data and cpu_data['SerialNumber'] != 'Unknown':
            print(f"  Serial: {cpu_data['SerialNumber']}")
        else:
            print("  Serial: Unknown (CPU serial numbers are often not exposed by modern processors)")
    else:
        print("  Serial: Unknown (CPU serial numbers are often not exposed by modern processors)")
    
    # BIOS Serial
    print("\nBIOS:")
    if 'bios_serial' in hwid_data:
        bios_data = parse_wmi_output(hwid_data['bios_serial'])
        if isinstance(bios_data, dict) and 'SerialNumber' in bios_data:
            print(f"  Serial: {bios_data['SerialNumber']}")
    
    # Motherboard Serial
    print("\nMOTHERBOARD:")
    if 'motherboard_serial' in hwid_data:
        mb_data = parse_wmi_output(hwid_data['motherboard_serial'])
        if isinstance(mb_data, dict) and 'SerialNumber' in mb_data:
            print(f"  Serial: {mb_data['SerialNumber']}")
    
    # smBIOS UUID
    print("\nsmBIOS UUID:")
    if 'smbios_uuid' in hwid_data:
        uuid_data = parse_wmi_output(hwid_data['smbios_uuid'])
        if isinstance(uuid_data, dict) and 'UUID' in uuid_data:
            print(f"  UUID: {uuid_data['UUID']}")
    
    # MAC Addresses
    print("\nMAC ADDRESSES:")
    if 'mac_addresses' in hwid_data:
        mac_data = parse_wmi_output(hwid_data['mac_addresses'])
        if isinstance(mac_data, list):
            for i, adapter in enumerate(mac_data, 1):
                if 'Name' in adapter and 'MacAddress' in adapter:
                    print(f"  {adapter['Name']}: {adapter['MacAddress']}")
        elif isinstance(mac_data, dict):
            if 'Name' in mac_data and 'MacAddress' in mac_data:
                print(f"  {mac_data['Name']}: {mac_data['MacAddress']}")
    
    print("="*70)

# HWID Report Manager
class HWIDReportManager:
    def __init__(self, settings_manager, stats_manager=None):
        self.data_dir = Path("data")
        self.reports_dir = self.data_dir / "reports"
        self.reports_dir.mkdir(exist_ok=True)
        self.settings = settings_manager
        self.stats_manager = stats_manager
        self.logger = logging.getLogger(__name__)
        self.current_report_file = self.data_dir / "current_hwid.json"
    
    def generate_hwid_hash(self, hwid_data):
        """Generate a unique hash from core HWID components"""
        import hashlib
        
        # Extract key identifiers for comparison
        key_components = []
        
        if 'core_hwid' in hwid_data:
            core = hwid_data['core_hwid']
            
            # Disk serial
            if 'diskdrive' in core:
                disk_data = parse_wmi_output(core['diskdrive'])
                if isinstance(disk_data, dict) and 'SerialNumber' in disk_data:
                    key_components.append(disk_data['SerialNumber'])
                elif isinstance(disk_data, list):
                    for disk in disk_data:
                        if 'SerialNumber' in disk:
                            key_components.append(disk['SerialNumber'])
            
            # BIOS serial
            if 'bios_serial' in core:
                bios_data = parse_wmi_output(core['bios_serial'])
                if isinstance(bios_data, dict) and 'SerialNumber' in bios_data:
                    key_components.append(bios_data['SerialNumber'])
            
            # Motherboard serial
            if 'motherboard_serial' in core:
                mb_data = parse_wmi_output(core['motherboard_serial'])
                if isinstance(mb_data, dict) and 'SerialNumber' in mb_data:
                    key_components.append(mb_data['SerialNumber'])
            
            # smBIOS UUID
            if 'smbios_uuid' in core:
                uuid_data = parse_wmi_output(core['smbios_uuid'])
                if isinstance(uuid_data, dict) and 'UUID' in uuid_data:
                    key_components.append(uuid_data['UUID'])
        
        # Create hash from components
        combined = '|'.join(sorted(key_components))
        return hashlib.md5(combined.encode()).hexdigest()
    
    def save_report(self, hwid_data):
        """Save HWID report to data folder"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            # Add metadata
            hwid_data['metadata'] = {
                'timestamp': timestamp,
                'generated_date': datetime.now().isoformat(),
                'hwid_hash': self.generate_hwid_hash(hwid_data)
            }
            
            # Save current report (overwrites previous)
            with open(self.current_report_file, 'w') as f:
                json.dump(hwid_data, f, indent=2, default=str)
            
            # Save timestamped report if backup is enabled
            if self.settings.get('backup_reports', True):
                report_file = self.reports_dir / f'hwid_report_{timestamp}.json'
                with open(report_file, 'w') as f:
                    json.dump(hwid_data, f, indent=2, default=str)
                
                # Clean old reports if max limit exceeded
                self.cleanup_old_reports()
            
            self.logger.info(f"HWID report saved: {timestamp}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error saving HWID report: {e}")
            return False
    
    def load_current_report(self):
        """Load the current HWID report"""
        try:
            if self.current_report_file.exists():
                with open(self.current_report_file, 'r') as f:
                    return json.load(f)
            return None
        except Exception as e:
            self.logger.error(f"Error loading current report: {e}")
            return None
    
    def compare_hwid(self, new_hwid_data):
        """Compare new HWID with stored report"""
        current_report = self.load_current_report()
        new_hash = self.generate_hwid_hash(new_hwid_data)
        
        if not current_report:
            self.logger.info("No previous HWID report found for comparison")
            # Record this as first check if stats tracking is enabled
            if self.stats_manager and self.settings.get('stats_tracking', True):
                self.stats_manager.record_check(new_hash, changed=False)
            return None, "No previous report found"
        
        old_hash = current_report.get('metadata', {}).get('hwid_hash', '')
        changed = new_hash != old_hash
        
        # Record the check in statistics
        if self.stats_manager and self.settings.get('stats_tracking', True):
            self.stats_manager.record_check(new_hash, changed=changed)
        
        if not changed:
            self.logger.info("HWID comparison: No changes detected")
            return True, "HWID matches previous report"
        else:
            self.logger.warning("HWID comparison: Changes detected!")
            return False, "HWID has changed from previous report"
    
    def cleanup_old_reports(self):
        """Remove old reports if exceeding max limit"""
        max_reports = self.settings.get('max_reports', 10)
        
        try:
            reports = list(self.reports_dir.glob('hwid_report_*.json'))
            reports.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            
            if len(reports) > max_reports:
                for old_report in reports[max_reports:]:
                    old_report.unlink()
                    self.logger.info(f"Removed old report: {old_report.name}")
        except Exception as e:
            self.logger.error(f"Error cleaning up old reports: {e}")

# Threaded Worker for Background Operations
class HWIDWorker:
    def __init__(self, settings_manager, report_manager, stats_manager=None):
        self.settings = settings_manager
        self.report_manager = report_manager
        self.stats_manager = stats_manager
        self.logger = logging.getLogger(__name__)
        self.task_queue = queue.Queue()
        self.result_queue = queue.Queue()
        self.worker_thread = None
        self.monitoring_thread = None
        self.running = False
        self.monitoring = False
        self.current_task = None
        self.task_progress = ""
        self.last_monitoring_check = None
    
    def start_worker(self):
        """Start the background worker thread"""
        if not self.running:
            self.running = True
            self.worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
            self.worker_thread.start()
            self.logger.info("Background worker started")
            
            # Start monitoring if enabled
            if self.settings.get('background_monitoring', False):
                self.start_monitoring()
    
    def start_monitoring(self):
        """Start background HWID monitoring"""
        if not self.monitoring:
            self.monitoring = True
            self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
            self.monitoring_thread.start()
            self.logger.info("Background HWID monitoring started")
    
    def stop_monitoring(self):
        """Stop background HWID monitoring"""
        self.monitoring = False
        if self.monitoring_thread and self.monitoring_thread.is_alive():
            self.monitoring_thread.join(timeout=2)
            self.logger.info("Background HWID monitoring stopped")
    
    def stop_worker(self):
        """Stop the background worker thread"""
        self.running = False
        self.monitoring = False
        
        if self.worker_thread and self.worker_thread.is_alive():
            self.worker_thread.join(timeout=2)
            self.logger.info("Background worker stopped")
        
        if self.monitoring_thread and self.monitoring_thread.is_alive():
            self.monitoring_thread.join(timeout=2)
            self.logger.info("Background monitoring stopped")
    
    def _worker_loop(self):
        """Main worker loop that processes tasks"""
        while self.running:
            try:
                # Check for new tasks
                task = self.task_queue.get(timeout=0.1)
                self.current_task = task
                
                task_type = task.get('type')
                task_id = task.get('id')
                
                if task_type == 'collect_hwid':
                    self._handle_collect_hwid(task_id)
                elif task_type == 'compare_hwid':
                    self._handle_compare_hwid(task_id)
                elif task_type == 'ban_current_hwid':
                    self._handle_ban_current_hwid(task_id)
                elif task_type == 'anticheat_test':
                    self._handle_anticheat_test(task_id)
                elif task_type == 'show_stats':
                    self._handle_show_stats(task_id)
                
                self.current_task = None
                self.task_progress = ""
                
            except queue.Empty:
                continue
            except Exception as e:
                self.logger.error(f"Worker error: {e}")
                self.result_queue.put({
                    'id': task_id if 'task_id' in locals() else 'unknown',
                    'status': 'error',
                    'error': str(e)
                })
    
    def _monitoring_loop(self):
        """Background monitoring loop that periodically checks HWID"""
        while self.monitoring and self.running:
            try:
                interval = self.settings.get('monitoring_interval', 300)  # Default 5 minutes
                
                # Wait for the interval
                for _ in range(interval):
                    if not self.monitoring or not self.running:
                        break
                    time.sleep(1)
                
                if not self.monitoring or not self.running:
                    break
                
                # Perform HWID check
                self.logger.info("Performing scheduled HWID check...")
                self.last_monitoring_check = datetime.now()
                
                hwid_data = collect_hwid_data()
                if hwid_data:
                    match, message = self.report_manager.compare_hwid(hwid_data)
                    
                    if match is False:  # HWID changed
                        self.logger.warning(f"Scheduled check detected HWID change: {message}")
                        # Save the new HWID report
                        self.report_manager.save_report(hwid_data)
                    elif match is True:  # No change
                        self.logger.info("Scheduled check: No HWID changes detected")
                    else:  # First check
                        self.logger.info("Scheduled check: First HWID recorded")
                        self.report_manager.save_report(hwid_data)
                
            except Exception as e:
                self.logger.error(f"Monitoring error: {e}")
                time.sleep(60)  # Wait 1 minute before retrying
    
    def _handle_collect_hwid(self, task_id):
        """Handle HWID collection in background"""
        try:
            self.task_progress = "Collecting HWID data..."
            hwid_data = collect_hwid_data()
            
            if hwid_data:
                self.task_progress = "Saving report..."
                success = self.report_manager.save_report(hwid_data)
                
                self.result_queue.put({
                    'id': task_id,
                    'status': 'success',
                    'data': hwid_data,
                    'saved': success
                })
            else:
                self.result_queue.put({
                    'id': task_id,
                    'status': 'error',
                    'error': 'Failed to collect HWID data'
                })
        except Exception as e:
            self.result_queue.put({
                'id': task_id,
                'status': 'error',
                'error': str(e)
            })
    
    def _handle_compare_hwid(self, task_id):
        """Handle HWID comparison in background"""
        try:
            self.task_progress = "Collecting current HWID..."
            hwid_data = collect_hwid_data()
            
            if hwid_data:
                self.task_progress = "Comparing with previous report..."
                match, message = self.report_manager.compare_hwid(hwid_data)
                
                self.result_queue.put({
                    'id': task_id,
                    'status': 'success',
                    'match': match,
                    'message': message
                })
            else:
                self.result_queue.put({
                    'id': task_id,
                    'status': 'error',
                    'error': 'Failed to collect HWID data for comparison'
                })
        except Exception as e:
            self.result_queue.put({
                'id': task_id,
                'status': 'error',
                'error': str(e)
            })
    
    def _handle_ban_current_hwid(self, task_id):
        """Handle banning current HWID in background - performs live scan"""
        try:
            # Always perform a live scan to get the current HWID
            self.task_progress = "Performing live scan to get current HWID..."
            hwid_data = collect_hwid_data()
            
            if not hwid_data:
                self.result_queue.put({
                    'id': task_id,
                    'status': 'error',
                    'error': 'Failed to collect current HWID data'
                })
                return
            
            self.task_progress = "Saving HWID report..."
            if not self.report_manager.save_report(hwid_data):
                self.result_queue.put({
                    'id': task_id,
                    'status': 'error',
                    'error': 'Failed to save HWID report'
                })
                return
            
            self.task_progress = "Adding HWID to ban list..."
            hwid_hash = self.report_manager.generate_hwid_hash(hwid_data)
            
            if not hwid_hash:
                self.result_queue.put({
                    'id': task_id,
                    'status': 'error',
                    'error': 'Failed to generate HWID hash from current data'
                })
                return
            
            banned_hwids = self.settings.get('banned_hwids', [])
            
            if hwid_hash in banned_hwids:
                self.result_queue.put({
                    'id': task_id,
                    'status': 'error',
                    'error': 'HWID is already banned'
                })
                return
            
            banned_hwids.append(hwid_hash)
            self.settings.set('banned_hwids', banned_hwids)
            
            self.result_queue.put({
                'id': task_id,
                'status': 'success',
                'message': f'Current HWID has been banned (Hash: {hwid_hash[:8]}...{hwid_hash[-8:]})',
                'hwid_hash': hwid_hash
            })
            
        except Exception as e:
            self.result_queue.put({
                'id': task_id,
                'status': 'error',
                'error': str(e)
            })
    
    def _handle_anticheat_test(self, task_id):
        """Handle anti-cheat test in background"""
        try:
            self.task_progress = "Performing anti-cheat scan..."
            hwid_data = collect_hwid_data()
            
            if not hwid_data:
                self.result_queue.put({
                    'id': task_id,
                    'status': 'error',
                    'error': 'Failed to collect HWID data for anti-cheat test'
                })
                return
            
            hwid_hash = self.report_manager.generate_hwid_hash(hwid_data)
            banned_hwids = self.settings.get('banned_hwids', [])
            is_banned = hwid_hash in banned_hwids
            
            self.result_queue.put({
                'id': task_id,
                'status': 'success',
                'is_banned': is_banned,
                'hwid_hash': hwid_hash,
                'scan_type': 'live'
            })
            
        except Exception as e:
            self.result_queue.put({
                'id': task_id,
                'status': 'error',
                'error': str(e)
            })
    
    def _handle_show_stats(self, task_id):
        """Handle showing HWID statistics"""
        try:
            if self.stats_manager:
                self.result_queue.put({
                    'id': task_id,
                    'status': 'success',
                    'stats': self.stats_manager.stats
                })
            else:
                self.result_queue.put({
                    'id': task_id,
                    'status': 'error',
                    'error': 'Statistics manager not available'
                })
        except Exception as e:
            self.result_queue.put({
                'id': task_id,
                'status': 'error',
                'error': str(e)
            })
            
            banned_hwids.append(hwid_hash)
            self.settings.set('banned_hwids', banned_hwids)
            
            self.result_queue.put({
                'id': task_id,
                'status': 'success',
                'message': f'HWID {hwid_hash[:8]}... has been banned'
            })
            
        except Exception as e:
            self.result_queue.put({
                'id': task_id,
                'status': 'error',
                'error': str(e)
            })
    
    def _handle_anticheat_test(self, task_id):
        """Handle anti-cheat test in background - Always performs fresh HWID scan"""
        try:
            self.task_progress = "Initializing anti-cheat system..."
            time.sleep(0.5)  # Simulate initialization
            
            self.task_progress = "Scanning hardware fingerprint..."
            time.sleep(1)  # Simulate scan time
            
            # ALWAYS perform fresh HWID scan (like real anti-cheat)
            hwid_data = collect_hwid_data()
            
            if not hwid_data:
                self.result_queue.put({
                    'id': task_id,
                    'status': 'error',
                    'error': 'Failed to collect HWID data for anti-cheat scan'
                })
                return
            
            self.task_progress = "Generating hardware fingerprint..."
            time.sleep(0.5)
            
            # Generate HWID hash for comparison
            hwid_hash = self.report_manager.generate_hwid_hash(hwid_data)
            
            self.task_progress = "Checking against ban database..."
            time.sleep(1)  # Simulate database check
            
            banned_hwids = self.settings.get('banned_hwids', [])
            is_banned = hwid_hash in banned_hwids
            
            self.task_progress = "Finalizing anti-cheat verification..."
            time.sleep(0.5)
            
            self.result_queue.put({
                'id': task_id,
                'status': 'success',
                'is_banned': is_banned,
                'hwid_hash': hwid_hash,
                'scan_type': 'fresh_scan'
            })
            
        except Exception as e:
            self.result_queue.put({
                'id': task_id,
                'status': 'error',
                'error': str(e)
            })
    

    def submit_task(self, task_type, task_id=None):
        """Submit a task to the worker queue"""
        if task_id is None:
            task_id = f"{task_type}_{int(time.time())}"
        
        task = {
            'type': task_type,
            'id': task_id,
            'timestamp': time.time()
        }
        
        self.task_queue.put(task)
        return task_id
    
    def get_result(self, task_id, timeout=0.1):
        """Get result for a specific task"""
        try:
            while True:
                result = self.result_queue.get(timeout=timeout)
                if result.get('id') == task_id:
                    return result
                # Put back results for other tasks
                self.result_queue.put(result)
        except queue.Empty:
            return None
    
    def is_working(self):
        """Check if worker is currently processing a task"""
        return self.current_task is not None
    
    def get_progress(self):
        """Get current task progress"""
        return self.task_progress

# HWID Ban Simulator
class HWIDBanManager:
    def __init__(self, settings_manager, report_manager):
        self.settings = settings_manager
        self.report_manager = report_manager
        self.logger = logging.getLogger(__name__)
    
    def is_hwid_banned(self, hwid_hash=None):
        """Check if current or specified HWID is banned"""
        if not self.settings.get('ban_simulator_enabled', True):
            return False, "Ban simulator is disabled"
        
        if hwid_hash is None:
            # Get current HWID hash
            current_report = self.report_manager.load_current_report()
            if not current_report:
                # Auto-generate report if none exists
                print("No HWID report found. Generating new report for check...")
                hwid_data = collect_hwid_data()
                
                if not hwid_data:
                    return False, "Failed to collect HWID data for check"
                
                # Save the new report
                if not self.report_manager.save_report(hwid_data):
                    return False, "Failed to save HWID report for check"
                
                # Load the newly saved report
                current_report = self.report_manager.load_current_report()
                if not current_report:
                    return False, "Failed to load newly generated report"
                
                print("New HWID report generated for check!")
            
            hwid_hash = current_report.get('metadata', {}).get('hwid_hash', '')
        
        banned_hwids = self.settings.get('banned_hwids', [])
        
        if hwid_hash in banned_hwids:
            return True, f"HWID {hwid_hash[:8]}... is BANNED"
        else:
            return False, f"HWID {hwid_hash[:8]}... is clean"
    

    def ban_current_hwid(self):
        """Ban the current HWID - performs live scan to get current HWID"""
        print("Performing live scan to get current HWID...")
        
        # Always perform a live scan to get the current HWID
        hwid_data = collect_hwid_data()
        
        if not hwid_data:
            return False, "Failed to collect current HWID data"
        
        # Save the new report (this will update the current report)
        if not self.report_manager.save_report(hwid_data):
            return False, "Failed to save HWID report"
        
        # Get the hash from the newly collected data
        hwid_hash = self.report_manager.generate_hwid_hash(hwid_data)
        if not hwid_hash:
            return False, "Failed to generate HWID hash from current data"
        
        print(f"Current HWID hash: {hwid_hash[:8]}...")
        
        banned_hwids = self.settings.get('banned_hwids', [])
        
        if hwid_hash in banned_hwids:
            return False, f"HWID {hwid_hash[:8]}... is already banned"
        
        banned_hwids.append(hwid_hash)
        self.settings.set('banned_hwids', banned_hwids)
        
        self.logger.info(f"HWID banned: {hwid_hash[:8]}...")
        return True, f"HWID {hwid_hash[:8]}... has been banned"
    
    def ban_hwid_by_hash(self, hwid_hash):
        """Ban a specific HWID by hash"""
        banned_hwids = self.settings.get('banned_hwids', [])
        
        if hwid_hash in banned_hwids:
            return False, f"HWID {hwid_hash[:8]}... is already banned"
        
        banned_hwids.append(hwid_hash)
        self.settings.set('banned_hwids', banned_hwids)
        
        self.logger.info(f"HWID banned manually: {hwid_hash[:8]}...")
        return True, f"HWID {hwid_hash[:8]}... has been banned"
    
    def unban_hwid(self, hwid_hash):
        """Unban a specific HWID"""
        banned_hwids = self.settings.get('banned_hwids', [])
        
        if hwid_hash not in banned_hwids:
            return False, f"HWID {hwid_hash[:8]}... is not banned"
        
        banned_hwids.remove(hwid_hash)
        self.settings.set('banned_hwids', banned_hwids)
        
        self.logger.info(f"HWID unbanned: {hwid_hash[:8]}...")
        return True, f"HWID {hwid_hash[:8]}... has been unbanned"
    
    def clear_all_bans(self):
        """Clear all banned HWIDs"""
        banned_count = len(self.settings.get('banned_hwids', []))
        self.settings.set('banned_hwids', [])
        
        self.logger.info("All HWID bans cleared")
        return True, f"Cleared {banned_count} banned HWIDs"
    
    def get_banned_hwids(self):
        """Get list of all banned HWIDs"""
        return self.settings.get('banned_hwids', [])
    
    def run_anticheat_test(self):
        """Simulate an anti-cheat check"""
        print("\n" + "="*60)
        print("           ANTI-CHEAT SIMULATOR")
        print("="*60)
        print()
        print("Initializing anti-cheat system...")
        print("Scanning hardware fingerprint...")
        print("Checking against ban database...")
        print()
        
        is_banned, message = self.is_hwid_banned()
        
        if is_banned:
            print("[!] ANTI-CHEAT DETECTION")
            print("="*40)
            print("STATUS: HARDWARE BAN DETECTED")
            print(f"REASON: {message}")
            print("ACTION: Access denied")
            print("="*40)
            print()
            print("Your hardware has been flagged by the anti-cheat system.")
            print("Contact support if you believe this is an error.")
        else:
            print("[OK] ANTI-CHEAT VERIFICATION")
            print("="*40)
            print("STATUS: Hardware verification passed")
            print(f"RESULT: {message}")
            print("ACTION: Access granted")
            print("="*40)
            print()
            print("Welcome! Your system is clean and ready to play.")
        
        print("="*60)
        return is_banned

def clear_screen():
    """Clear the console screen"""
    os.system('cls' if os.name == 'nt' else 'clear')

def show_main_menu(monitoring_active=False, stats_summary=None):
    """Display the main menu"""
    clear_screen()
    print("=" * 60)
    print("              EVADERS HWID")
    print("=" * 60)
    
    # Show monitoring status
    if monitoring_active:
        print("[ACTIVE] Background Monitoring")
        if stats_summary:
            print(f"   Total Checks: {stats_summary.get('total_checks', 0)} | Changes: {stats_summary.get('total_changes', 0)}")
    else:
        print("[INACTIVE] Background Monitoring")
    
    print()
    print("1. Generate New HWID Report")
    print("2. Compare Current HWID")
    print("3. View Current HWID Report")
    print("4. Anti-Cheat Simulator")
    print("5. HWID Change Statistics")
    print("6. Settings")
    print("7. View Logs")
    print("8. Exit")
    print()
    print("=" * 60)

def show_settings_menu(settings_manager, worker=None, startup_manager=None):
    """Display and handle settings menu"""
    while True:
        clear_screen()
        print("=" * 60)
        print("           SETTINGS")
        print("=" * 60)
        print()
        print(f"1. Auto-save reports: {settings_manager.get('auto_save_reports')}")
        print(f"2. Compare on startup: {settings_manager.get('compare_on_startup')}")
        print(f"3. Detailed logging: {settings_manager.get('detailed_logging')}")
        print(f"4. Backup reports: {settings_manager.get('backup_reports')}")
        print(f"5. Max reports to keep: {settings_manager.get('max_reports')}")
        print(f"6. Ban simulator enabled: {settings_manager.get('ban_simulator_enabled')}")
        print(f"7. Background monitoring: {settings_manager.get('background_monitoring')}")
        print(f"8. Monitoring interval: {settings_manager.get('monitoring_interval')} seconds")
        print(f"9. Statistics tracking: {settings_manager.get('stats_tracking')}")
        
        # Show auto-start status
        if startup_manager and startup_manager.is_windows():
            auto_start_status = startup_manager.is_auto_start_enabled()
            print(f"10. Auto-start with Windows: {auto_start_status}")
            print("11. Back to Main Menu")
            max_option = 11
        else:
            print("10. Auto-start with Windows: Not available (Windows only)")
            print("11. Back to Main Menu")
            max_option = 11
        
        print()
        print("=" * 60)
        
        choice = input(f"Select option (1-{max_option}): ").strip()
        
        if choice == '1':
            current = settings_manager.get('auto_save_reports')
            settings_manager.set('auto_save_reports', not current)
            print(f"Auto-save reports set to: {not current}")
            input("Press Enter to continue...")
        
        elif choice == '2':
            current = settings_manager.get('compare_on_startup')
            settings_manager.set('compare_on_startup', not current)
            print(f"Compare on startup set to: {not current}")
            input("Press Enter to continue...")
        
        elif choice == '3':
            current = settings_manager.get('detailed_logging')
            settings_manager.set('detailed_logging', not current)
            print(f"Detailed logging set to: {not current}")
            input("Press Enter to continue...")
        
        elif choice == '4':
            current = settings_manager.get('backup_reports')
            settings_manager.set('backup_reports', not current)
            print(f"Backup reports set to: {not current}")
            input("Press Enter to continue...")
        
        elif choice == '5':
            try:
                new_max = int(input(f"Enter max reports to keep (current: {settings_manager.get('max_reports')}): "))
                if new_max > 0:
                    settings_manager.set('max_reports', new_max)
                    print(f"Max reports set to: {new_max}")
                else:
                    print("Please enter a positive number")
                input("Press Enter to continue...")
            except ValueError:
                print("Please enter a valid number")
                input("Press Enter to continue...")
        
        elif choice == '6':
            current = settings_manager.get('ban_simulator_enabled')
            settings_manager.set('ban_simulator_enabled', not current)
            print(f"Ban simulator enabled set to: {not current}")
            input("Press Enter to continue...")
        
        elif choice == '7':
            current = settings_manager.get('background_monitoring')
            new_value = not current
            settings_manager.set('background_monitoring', new_value)
            
            if worker:
                if new_value:
                    worker.start_monitoring()
                    print("Background monitoring enabled and started")
                else:
                    worker.stop_monitoring()
                    print("Background monitoring disabled and stopped")
            else:
                print(f"Background monitoring set to: {new_value}")
            input("Press Enter to continue...")
        
        elif choice == '8':
            try:
                current_interval = settings_manager.get('monitoring_interval')
                new_interval = int(input(f"Enter monitoring interval in seconds (current: {current_interval}): "))
                if new_interval >= 60:  # Minimum 1 minute
                    settings_manager.set('monitoring_interval', new_interval)
                    print(f"Monitoring interval set to: {new_interval} seconds")
                else:
                    print("Minimum interval is 60 seconds")
                input("Press Enter to continue...")
            except ValueError:
                print("Please enter a valid number")
                input("Press Enter to continue...")
        
        elif choice == '9':
            current = settings_manager.get('stats_tracking')
            settings_manager.set('stats_tracking', not current)
            print(f"Statistics tracking set to: {not current}")
            input("Press Enter to continue...")
        
        elif choice == '10':
            # Auto-start with Windows
            if startup_manager and startup_manager.is_windows():
                current_status = startup_manager.is_auto_start_enabled()
                
                if current_status:
                    # Currently enabled, ask to disable
                    confirm = input("Auto-start is currently ENABLED. Disable it? (y/N): ").strip().lower()
                    if confirm == 'y':
                        success, message = startup_manager.disable_auto_start()
                        print(f"\n{message}")
                        if success:
                            settings_manager.set('auto_start_windows', False)
                else:
                    # Currently disabled, ask to enable
                    confirm = input("Auto-start is currently DISABLED. Enable it? (y/N): ").strip().lower()
                    if confirm == 'y':
                        success, message = startup_manager.enable_auto_start()
                        print(f"\n{message}")
                        if success:
                            settings_manager.set('auto_start_windows', True)
            else:
                print("\nAuto-start with Windows is only available on Windows systems.")
            
            input("Press Enter to continue...")
        
        elif choice == '11':
            break

def show_progress_and_wait(worker, task_id, operation_name):
    """Show progress while waiting for a background task to complete"""
    print(f"\n{operation_name}...")
    
    while True:
        if worker.is_working():
            progress = worker.get_progress()
            if progress:
                print(f"\r{progress}...", end="", flush=True)
        
        result = worker.get_result(task_id, timeout=0.5)
        if result:
            print()  # New line after progress
            return result
        
        time.sleep(0.1)

def threaded_collect_hwid(worker, settings_manager, report_manager):
    """Collect HWID data using background worker"""
    task_id = worker.submit_task('collect_hwid')
    result = show_progress_and_wait(worker, task_id, "Collecting hardware information")
    
    if result['status'] == 'success':
        hwid_data = result['data']
        
        # Display core HWID info
        display_core_hwid(hwid_data['core_hwid'])
        
        if result.get('saved'):
            print("\nReport saved to data folder!")
        else:
            print("\nReport collected but not saved!")
        
        return True
    else:
        print(f"\nError: {result.get('error', 'Unknown error')}")
        return False

def threaded_compare_hwid(worker):
    """Compare HWID using background worker"""
    task_id = worker.submit_task('compare_hwid')
    result = show_progress_and_wait(worker, task_id, "Comparing hardware information")
    
    if result['status'] == 'success':
        match = result['match']
        message = result['message']
        
        print("\n" + "="*50)
        print("           HWID COMPARISON RESULT")
        print("="*50)
        
        if match is None:
            print("Status: No previous report to compare")
        elif match:
            print("Status: HWID MATCHES - No changes detected")
        else:
            print("Status: HWID CHANGED - Hardware changes detected!")
        
        print(f"Details: {message}")
        print("="*50)
        return True
    else:
        print(f"\nError: {result.get('error', 'Unknown error')}")
        return False

def threaded_ban_current_hwid(worker):
    """Ban current HWID using background worker"""
    task_id = worker.submit_task('ban_current_hwid')
    result = show_progress_and_wait(worker, task_id, "Banning current HWID")
    
    if result['status'] == 'success':
        print(f"\n[SUCCESS] {result['message']}")
        return True
    else:
        print(f"\n[ERROR] {result.get('error', 'Unknown error')}")
        return False


def threaded_anticheat_test(worker):
    """Run anti-cheat test using background worker"""
    print("\n" + "="*60)
    print("           ANTI-CHEAT SIMULATOR")
    print("="*60)
    print()
    print(">> Starting anti-cheat verification process...")
    print(">> This will perform a fresh hardware scan")
    print(">> Checking against latest ban wave database")
    print()
    
    task_id = worker.submit_task('anticheat_test')
    result = show_progress_and_wait(worker, task_id, "Anti-cheat system")
    
    if result['status'] == 'success':
        is_banned = result['is_banned']
        hwid_hash = result['hwid_hash']
        scan_type = result.get('scan_type', 'unknown')
        
        print("\n" + "="*50)
        print("      ANTI-CHEAT VERIFICATION COMPLETE")
        print("="*50)
        
        if is_banned:
            print()
            print("[!] HARDWARE BAN DETECTED")
            print("-" * 30)
            print("STATUS: BANNED")
            print(f"HWID: {hwid_hash[:12]}...{hwid_hash[-12:]}")
            print("SCAN TYPE: Fresh hardware fingerprint")
            print("BAN WAVE: Hardware flagged in database")
            print("ACTION: Access denied")
            print("-" * 30)
            print()
            print("WARNING: Your hardware fingerprint has been detected")
            print("         in our anti-cheat ban database.")
            print()
            print("SUPPORT: If you believe this is an error, contact support")
            print("         with your HWID for manual review.")
            print()
            print("NOTE: Hardware bans are permanent and cannot")
            print("      be bypassed by reinstalling the game.")
        else:
            print()
            print("[OK] HARDWARE VERIFICATION PASSED")
            print("-" * 30)
            print("STATUS: CLEAN")
            print(f"HWID: {hwid_hash[:12]}...{hwid_hash[-12:]}")
            print("SCAN TYPE: Fresh hardware fingerprint")
            print("BAN WAVE: No matches found in database")
            print("ACTION: Access granted")
            print("-" * 30)
            print()
            print("SUCCESS: Welcome! Your system passed all anti-cheat checks.")
            print("VERIFIED: Hardware fingerprint verified as clean.")
            print("READY: You're ready to play!")
        
        print("\n" + "="*50)
        return True
    else:
        print(f"\n[ERROR] ANTI-CHEAT ERROR")
        print("="*30)
        print(f"Failed to complete verification: {result.get('error', 'Unknown error')}")
        print("Please try again or contact support.")
        print("="*30)
        return False

def show_ban_management_menu(ban_manager, worker):
    """Display and handle ban management menu"""
    while True:
        clear_screen()
        print("=" * 60)
        print("        ANTI-CHEAT SIMULATOR")
        print("=" * 60)
        print()
        
        banned_hwids = ban_manager.get_banned_hwids()
        print(f"Currently banned HWIDs: {len(banned_hwids)}")
        
        if banned_hwids:
            print("\nBanned HWIDs:")
            for i, hwid in enumerate(banned_hwids, 1):
                print(f"  {i}. {hwid[:8]}...{hwid[-8:]}")
        
        print()
        print("1. Run Anti-Cheat Test")
        print("2. Ban Current HWID")
        print("3. Ban HWID by Hash")
        print("4. Unban HWID")
        print("5. Clear All Bans")
        print("6. Back to Main Menu")
        print()
        print("=" * 60)
        
        choice = input("Select option (1-6): ").strip()
        
        if choice == '1':
            # Run anti-cheat test (threaded)
            threaded_anticheat_test(worker)
            input("\nPress Enter to continue...")
        
        elif choice == '2':
            # Ban current HWID (threaded)
            threaded_ban_current_hwid(worker)
            input("Press Enter to continue...")
        
        elif choice == '3':
            # Ban HWID by hash
            hwid_hash = input("Enter HWID hash to ban: ").strip()
            if hwid_hash:
                success, message = ban_manager.ban_hwid_by_hash(hwid_hash)
                print(f"\n{message}")
            else:
                print("\nNo HWID hash provided")
            input("Press Enter to continue...")
        
        elif choice == '4':
            # Unban HWID
            if not banned_hwids:
                print("\nNo HWIDs are currently banned")
                input("Press Enter to continue...")
                continue
            
            print("\nSelect HWID to unban:")
            for i, hwid in enumerate(banned_hwids, 1):
                print(f"{i}. {hwid[:8]}...{hwid[-8:]}")
            
            try:
                selection = int(input("Enter number: ")) - 1
                if 0 <= selection < len(banned_hwids):
                    hwid_to_unban = banned_hwids[selection]
                    success, message = ban_manager.unban_hwid(hwid_to_unban)
                    print(f"\n{message}")
                else:
                    print("\nInvalid selection")
            except ValueError:
                print("\nPlease enter a valid number")
            input("Press Enter to continue...")
        
        elif choice == '5':
            # Clear all bans
            if banned_hwids:
                confirm = input(f"Are you sure you want to clear all {len(banned_hwids)} bans? (y/N): ").strip().lower()
                if confirm == 'y':
                    success, message = ban_manager.clear_all_bans()
                    print(f"\n{message}")
                else:
                    print("\nOperation cancelled")
            else:
                print("\nNo HWIDs are currently banned")
            input("Press Enter to continue...")
        
        elif choice == '6':
            break

def view_logs():
    """Display recent log entries"""
    clear_screen()
    print("=" * 60)
    print("           RECENT LOGS")
    print("=" * 60)
    print()
    
    log_file = Path("data/evaders_hwid.log")
    
    try:
        if log_file.exists():
            with open(log_file, 'r') as f:
                lines = f.readlines()
                # Show last 20 lines
                for line in lines[-20:]:
                    print(line.strip())
        else:
            print("No log file found")
    except Exception as e:
        print(f"Error reading log file: {e}")
    
    print()
    input("Press Enter to continue...")

def collect_hwid_data():
    """Collect comprehensive HWID data"""
    logger = logging.getLogger(__name__)
    logger.info("Starting HWID data collection")
    
    print("Collecting hardware information...")
    print("This may take a few moments...")
    print()
    
    hardware_data = {}
    
    try:
        hardware_data['core_hwid'] = get_core_hwid_info()
        hardware_data['system'] = get_system_info()
        hardware_data['cpu'] = get_cpu_info()
        hardware_data['memory'] = get_memory_info()
        hardware_data['storage'] = get_storage_info()
        hardware_data['network'] = get_network_info()
        hardware_data['motherboard_bios'] = get_motherboard_bios_info()
        hardware_data['gpu'] = get_gpu_info()
        hardware_data['usb_devices'] = get_usb_devices()
        hardware_data['audio_devices'] = get_audio_devices()
        hardware_data['system_slots'] = get_system_slots()
        hardware_data['tpm'] = get_tpm_info()
        
        logger.info("HWID data collection completed successfully")
        return hardware_data
        
    except Exception as e:
        logger.error(f"Error during HWID data collection: {e}")
        return None

def main():
    """Main function with menu system"""
    # Setup logging
    logger = setup_logging()
    logger.info("Evaders HWID started")
    
    # Initialize managers
    settings_manager = SettingsManager()
    stats_manager = HWIDStatsManager()
    startup_manager = WindowsStartupManager()
    report_manager = HWIDReportManager(settings_manager, stats_manager)
    ban_manager = HWIDBanManager(settings_manager, report_manager)
    worker = HWIDWorker(settings_manager, report_manager, stats_manager)
    
    # Start background worker
    worker.start_worker()
    
    # Auto-start background monitoring if enabled
    if settings_manager.get('background_monitoring', True):
        logger.info("Auto-starting background HWID monitoring...")
        worker.start_monitoring()
        print("Background HWID monitoring started automatically.")
        print(f"Checking for changes every {settings_manager.get('monitoring_interval', 300)} seconds.")
        print()
    
    logger.info("Evaders HWID initialized with background worker and monitoring")
    
    # Check if running on Windows
    if platform.system() != 'Windows':
        print("Warning: This script is optimized for Windows.")
        print("Some features may not work on other platforms.")
        input("Press Enter to continue...")
    
    # Compare on startup if enabled
    if settings_manager.get('compare_on_startup'):
        print("Performing startup HWID comparison...")
        hwid_data = collect_hwid_data()
        if hwid_data:
            match, message = report_manager.compare_hwid(hwid_data)
            if match is False:
                print(f"WARNING: {message}")
                input("Press Enter to continue...")
    
    # Main menu loop
    while True:
        # Get current stats summary for display
        stats_summary = {
            'total_checks': stats_manager.stats.get('total_checks', 0),
            'total_changes': stats_manager.stats.get('total_changes', 0)
        }
        
        show_main_menu(monitoring_active=worker.monitoring, stats_summary=stats_summary)
        choice = input("Select option (1-8): ").strip()
        
        if choice == '1':
            # Generate new HWID report (threaded)
            logger.info("User requested new HWID report generation")
            
            if threaded_collect_hwid(worker, settings_manager, report_manager):
                # Ask to save if auto-save is disabled
                if not settings_manager.get('auto_save_reports'):
                    save_choice = input("\nSave this report? (y/n): ").lower().strip()
                    if save_choice == 'y':
                        current_report = report_manager.load_current_report()
                        if current_report:
                            print("Report already saved!")
                        else:
                            print("Error: Report not found to save!")
            
            input("\nPress Enter to continue...")
        
        elif choice == '2':
            # Compare current HWID (threaded)
            logger.info("User requested HWID comparison")
            threaded_compare_hwid(worker)
            input("\nPress Enter to continue...")
        
        elif choice == '3':
            # View current HWID report
            logger.info("User requested to view current HWID report")
            current_report = report_manager.load_current_report()
            
            if current_report:
                clear_screen()
                if 'core_hwid' in current_report:
                    display_core_hwid(current_report['core_hwid'])
                
                if 'metadata' in current_report:
                    print(f"\nReport generated: {current_report['metadata'].get('generated_date', 'Unknown')}")
                    print(f"HWID Hash: {current_report['metadata'].get('hwid_hash', 'Unknown')}")
                
                input("\nPress Enter to continue...")
            else:
                print("No current HWID report found!")
                print("Generate a new report first.")
                input("Press Enter to continue...")
        
        elif choice == '4':
            # Anti-Cheat Simulator
            logger.info("User accessed anti-cheat simulator menu")
            show_ban_management_menu(ban_manager, worker)
        
        elif choice == '5':
            # HWID Change Statistics
            logger.info("User requested HWID statistics")
            clear_screen()
            stats_manager.display_statistics()
            
            # Show monitoring status
            if worker.monitoring:
                print(f"\nBackground Monitoring: ACTIVE")
                print(f"Check Interval: {settings_manager.get('monitoring_interval', 300)} seconds")
                if worker.last_monitoring_check:
                    print(f"Last Check: {worker.last_monitoring_check.strftime('%Y-%m-%d %H:%M:%S')}")
            else:
                print(f"\nBackground Monitoring: INACTIVE")
                print("Enable in Settings > Background Monitoring")
            
            input("\nPress Enter to continue...")
        
        elif choice == '6':
            # Settings
            logger.info("User accessed settings menu")
            show_settings_menu(settings_manager, worker, startup_manager)
        
        elif choice == '7':
            # View logs
            logger.info("User requested to view logs")
            view_logs()
        
        elif choice == '8':
            # Exit
            logger.info("User exited Evaders HWID")
            print("Shutting down background worker...")
            worker.stop_worker()
            print("Goodbye!")
            break
        
        else:
            print("Invalid choice. Please try again.")
            input("Press Enter to continue...")

if __name__ == "__main__":
    main()