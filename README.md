# Evaders HWID

A comprehensive Hardware ID (HWID) collection, monitoring, and comparison tool for Windows systems. This tool gathers detailed hardware information, tracks changes over time, and provides extensive reporting capabilities.

## Features

- **Complete Hardware Profiling**: Collects detailed information from CPU, RAM, storage, motherboard, BIOS, network adapters, and more
- **HWID Change Detection**: Monitors and tracks hardware changes with statistical analysis
- **Background Monitoring**: Optional continuous monitoring with configurable intervals
- **Comprehensive Reporting**: Generates detailed reports with comparison capabilities
- **Ban Simulation**: Test HWID-based ban systems with simulated hardware changes
- **Windows Integration**: Auto-start with Windows support via registry entries
- **Data Persistence**: All data saved to organized JSON files with comprehensive logging

## Installation

### Prerequisites
- Windows operating system
- Python 3.6 or higher
- PowerShell (included with Windows)

### Quick Start
1. Clone or download this repository
2. Run the script - dependencies will be installed automatically:
```bash
python evaders_hwid.py
```

The tool will automatically install required dependencies (`psutil`) on first run.

## Usage

### Main Menu Options

1. **Collect Current HWID** - Gather complete hardware information
2. **Compare with Previous** - Compare current HWID with stored data
3. **View HWID Statistics** - Display change tracking and analytics
4. **Generate Report** - Create detailed hardware reports
5. **Settings** - Configure monitoring, auto-start, and other options
6. **Ban Simulator** - Test HWID-based detection systems
7. **Background Monitor** - Start/stop continuous monitoring

### Core Hardware Information Collected

- **Storage**: Disk drive models and serial numbers
- **CPU**: Processor details and serial numbers (when available)
- **BIOS**: BIOS version and serial numbers
- **Motherboard**: Board details and serial numbers
- **System UUID**: smBIOS UUID information
- **Network**: MAC addresses and adapter details
- **Memory**: RAM modules with serial numbers and specifications
- **Graphics**: GPU information and drivers

### Data Storage

All data is stored in the `data/` directory:
- `settings.json` - Configuration settings
- `hwid_stats.json` - Change tracking statistics
- `evaders_hwid.log` - Application logs
- `hwid_manager.log` - Background monitoring logs
- `reports/` - Generated hardware reports

## Configuration

### Settings Options

- **Auto-save reports**: Automatically save reports when generated
- **Compare on startup**: Run comparison check when starting
- **Detailed logging**: Enable verbose logging
- **Background monitoring**: Enable continuous HWID monitoring
- **Monitoring interval**: Set check frequency (seconds)
- **Auto-start with Windows**: Launch with system startup
- **Ban simulator**: Enable HWID ban testing features

### Windows Auto-Start

The tool can be configured to start automatically with Windows by:
1. Going to Settings menu
2. Selecting "Toggle Windows Auto-Start"
3. Confirming the registry modification

## Background Monitoring

Enable continuous monitoring to:
- Track hardware changes in real-time
- Generate alerts on HWID modifications
- Maintain detailed change history
- Collect usage statistics

## Statistics and Analytics

The tool provides comprehensive analytics including:
- Total HWID checks performed
- Number of hardware changes detected
- Change frequency analysis
- Monthly breakdown of activity
- Unique hardware configurations seen

## Security Features

- **HWID Hashing**: Hardware information is hashed for privacy
- **Change Detection**: Immediate alerts on hardware modifications
- **Ban Simulation**: Test evasion techniques safely
- **Logging**: Complete audit trail of all operations

## Technical Details

### Dependencies
- `psutil` - System and process utilities (auto-installed)
- `json` - Data serialization (built-in)
- `logging` - Application logging (built-in)
- `subprocess` - System command execution (built-in)

### WMI Integration
Uses PowerShell's `Get-CimInstance` for hardware queries:
- Modern replacement for deprecated `wmic`
- Comprehensive hardware information access
- Cross-compatible with Windows versions

### Data Format
All data stored in JSON format for:
- Easy parsing and analysis
- Cross-platform compatibility
- Human-readable configuration

## Use Cases

- **System Administration**: Track hardware changes across systems
- **Security Research**: Analyze HWID-based detection methods
- **Hardware Inventory**: Maintain detailed hardware databases
- **Change Monitoring**: Detect unauthorized hardware modifications
- **Compliance**: Document system configurations

## Troubleshooting

### Common Issues

**PowerShell Execution Policy**:
If you encounter PowerShell execution errors, run as administrator:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

**Missing Dependencies**:
The tool auto-installs dependencies, but if issues persist:
```bash
pip install psutil
```

**Permission Errors**:
Some hardware information requires administrator privileges. Run as administrator for complete data collection.
