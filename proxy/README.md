# PrinterMonitor Pro - Proxy Device

The proxy device software that runs on your local network to monitor printers and send data to storage (local or cloud).

## 📋 Overview

The proxy is a Python application that:
- Discovers printers on your network via SNMP
- Collects metrics (toner levels, page counts, drum status)
- Stores data locally in SQLite OR sends to cloud API
- Runs continuously in the background

## 🚀 Quick Start

### 1. Installation
```bash
cd ~/projects/printermonitor-pro/proxy

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration
```bash
# Copy example config
cp .env.example .env

# Edit configuration
nano .env
```

**For Local Mode** (same as Community Edition):
```env
MONITOR_MODE=local
SNMP_COMMUNITY=public
DATABASE_FILE=printer_monitoring.db
```

**For Cloud Mode** (PrinterMonitor Pro):
```env
MONITOR_MODE=cloud
CLOUD_API_URL=https://api.printermonitor.pro
CLOUD_API_KEY=your-api-key-here
SNMP_COMMUNITY=public
CLOUD_ENABLE_BUFFER=true
```

### 3. Test Configuration
```bash
# Test that everything is set up correctly
python test_config.py
```

### 4. Add Printers

For now, manually add a printer to test:
```bash
python3 << 'PYTHON'
import sys
sys.path.insert(0, 'src')
from storage import get_storage

storage = get_storage()
storage.get_or_create_printer(
    ip="192.168.1.100",  # Replace with your printer IP
    name="Test Printer",
    location="Office",
    model="Unknown"
)
print("Printer added!")
PYTHON
```

### 5. Test Monitoring
```bash
# Single run (test)
python src/main.py once

# Continuous monitoring (1 hour intervals)
python src/main.py loop

# Custom interval (15 minutes)
python src/main.py loop 900
```

## 📁 Project Structure
```
proxy/
├── src/
│   ├── config/
│   │   └── settings.py          # Configuration management
│   ├── discovery/
│   │   └── __init__.py          # (Ready for scanner.py)
│   ├── monitoring/
│   │   └── collector.py         # Metrics collection
│   ├── storage/
│   │   ├── interface.py         # Storage interface
│   │   ├── local.py             # SQLite storage
│   │   ├── cloud.py             # Cloud API client
│   │   └── factory.py           # Storage factory
│   ├── utils/
│   │   └── snmp.py              # SNMP utilities
│   └── main.py                  # Entry point
├── .env.example                 # Configuration template
├── requirements.txt             # Python dependencies
├── test_config.py               # Configuration test
└── README.md                    # This file
```

## ⚙️ Configuration Options

### Mode Selection

| Mode | Description | Use Case |
|------|-------------|----------|
| `local` | Store in SQLite database locally | Testing, single-site, no cloud needed |
| `cloud` | Send to PrinterMonitor Pro API | Multi-site, remote access, cloud dashboard |

### SNMP Settings
```env
SNMP_COMMUNITY=public       # SNMP community string
SNMP_TIMEOUT=2             # Timeout in seconds
SNMP_PORT=161              # SNMP port (usually 161)
```

### Monitoring Settings
```env
MONITOR_INTERVAL=3600      # How often to check printers (seconds)
                           # 3600 = 1 hour
                           # 1800 = 30 minutes
                           # 900 = 15 minutes
```

## 📊 Collected Metrics

The proxy collects the following metrics from each printer:

- **Total Pages**: Lifetime page count
- **Toner Level**: Percentage or status
- **Drum Level**: Percentage remaining
- **Device Status**: Online/offline/error
- **Model**: Printer model information

## 🔧 Troubleshooting

### Printers not discovered

1. Check SNMP is enabled on printers
2. Verify community string matches
3. Check firewall allows UDP port 161
4. Test manually:
```bash
   snmpwalk -v2c -c public 192.168.1.100
```

### Import errors

Make sure you're running from the proxy directory:
```bash
cd ~/projects/printermonitor-pro/proxy
python src/main.py once
```

### Configuration not loading

Create the .env file:
```bash
cp .env.example .env
nano .env
```

## 🧪 Testing

Run configuration test:
```bash
python test_config.py
```

Expected output:
```
Test 1: Configuration Display - ✓
Test 2: Configuration Validation - ✓
Test 3: Storage Initialization - ✓
Test 4: Storage Health Check - ✓
ALL TESTS PASSED!
```

## 📝 Next Steps

1. ✅ Test configuration: `python test_config.py`
2. ✅ Add your printers (manually or via discovery)
3. ✅ Test monitoring: `python src/main.py once`
4. ✅ Set up continuous monitoring: `python src/main.py loop`
5. Copy your discovery script from `C:\utilities\printer_discovery.py` to `src/discovery/scanner.py`

## 🆘 Support

For issues:
- Check logs in `proxy.log`
- Review configuration in `.env`
- Run `python test_config.py`

---

**Version:** 1.0.0-alpha  
**Status:** Development  
**License:** Proprietary
