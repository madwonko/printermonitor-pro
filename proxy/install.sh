#!/bin/bash
# PrinterMonitor Pro - Proxy Device Installer
# Usage: curl -fsSL https://install.prntr.org | sudo bash

set -e

echo "=================================="
echo "PrinterMonitor Pro - Proxy Installer"
echo "=================================="
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
  echo "❌ Please run with sudo:"
  echo "   curl -fsSL https://install.prntr.org | sudo bash"
  exit 1
fi

# Detect OS
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$ID
else
    echo "❌ Cannot detect OS"
    exit 1
fi

echo "✓ Detected OS: $OS"
echo ""

# Install dependencies
echo "📦 Installing dependencies..."
if [ "$OS" = "ubuntu" ] || [ "$OS" = "debian" ]; then
    apt-get update -qq
    apt-get install -y python3 python3-pip python3-venv git curl >/dev/null 2>&1
elif [ "$OS" = "centos" ] || [ "$OS" = "rhel" ] || [ "$OS" = "fedora" ]; then
    yum install -y python3 python3-pip git curl >/dev/null 2>&1
else
    echo "⚠️  Unsupported OS. Trying to continue anyway..."
fi

echo "✓ Dependencies installed"
echo ""

# Create installation directory
INSTALL_DIR="/opt/printermonitor"
echo "📂 Installing to $INSTALL_DIR..."

# Check if already installed
if [ -d "$INSTALL_DIR" ]; then
    echo "⚠️  Existing installation found. Backing up..."
    mv "$INSTALL_DIR" "$INSTALL_DIR.backup.$(date +%s)"
fi

# Clone repository
git clone -q https://github.com/madwonko/printermonitor-pro.git "$INSTALL_DIR"
cd "$INSTALL_DIR/proxy"

echo "✓ Code downloaded"
echo ""

# Create virtual environment
echo "🐍 Setting up Python environment..."
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip >/dev/null 2>&1
pip install -r requirements.txt >/dev/null 2>&1

echo "✓ Python environment ready"
echo ""

# Get API key from user
echo "🔑 Configuration"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "1. Go to: https://app.prntr.org/dashboard/devices"
echo "2. Click 'Add Device'"
echo "3. Copy the API key shown"
echo ""
echo -n "Paste your API key here: "
read -r API_KEY

if [ -z "$API_KEY" ]; then
    echo "❌ No API key provided. Installation cancelled."
    exit 1
fi

# Ask for SNMP community string
echo ""
echo -n "SNMP community string (default: public): "
read -r SNMP_COMMUNITY
SNMP_COMMUNITY=${SNMP_COMMUNITY:-public}

# Create .env file
cat > .env << ENVEOF
# PrinterMonitor Pro - Proxy Configuration
MONITOR_MODE=cloud
CLOUD_API_URL=https://api.prntr.org
CLOUD_API_KEY=$API_KEY
CLOUD_ENABLE_BUFFER=true

# SNMP Configuration
SNMP_COMMUNITY=$SNMP_COMMUNITY
SNMP_TIMEOUT=2
SNMP_PORT=161

# Monitoring
MONITOR_INTERVAL=300
DISCOVERY_ENABLED=false
ENVEOF

echo "✓ Configuration saved"
echo ""

# Create systemd service
echo "⚙️  Setting up system service..."

cat > /etc/systemd/system/printermonitor-proxy.service << SERVICEEOF
[Unit]
Description=PrinterMonitor Pro Proxy Device
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=root
WorkingDirectory=$INSTALL_DIR/proxy
Environment="PATH=$INSTALL_DIR/proxy/venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
ExecStart=$INSTALL_DIR/proxy/venv/bin/python src/main.py loop
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
SERVICEEOF

# Reload systemd and start service
systemctl daemon-reload
systemctl enable printermonitor-proxy >/dev/null 2>&1
systemctl start printermonitor-proxy

echo "✓ Service installed and started"
echo ""

# Wait a moment for service to start
sleep 2

# Check service status
if systemctl is-active --quiet printermonitor-proxy; then
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "✅ Installation Complete!"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "🎉 PrinterMonitor Pro Proxy is now running!"
    echo ""
    echo "📊 View status:"
    echo "   sudo systemctl status printermonitor-proxy"
    echo ""
    echo "📋 View logs:"
    echo "   sudo journalctl -u printermonitor-proxy -f"
    echo ""
    echo "🔄 Restart service:"
    echo "   sudo systemctl restart printermonitor-proxy"
    echo ""
    echo "🛑 Stop service:"
    echo "   sudo systemctl stop printermonitor-proxy"
    echo ""
    echo "📍 Installation location: $INSTALL_DIR/proxy"
    echo ""
    echo "Go to https://app.prntr.org/dashboard to see your printers!"
    echo ""
else
    echo "❌ Service failed to start. Check logs:"
    echo "   sudo journalctl -u printermonitor-proxy -xe"
    exit 1
fi
