#!/usr/bin/env bash
set -euo pipefail

echo "=== AgentBoss Relay Setup ==="

# Check if strfry is installed
if ! command -v strfry &> /dev/null; then
    echo "strfry not found. Please install strfry first:"
    echo "  git clone https://github.com/hoytech/strfry.git && cd strfry && git submodule update --init && make setup-golpe && make -j$(nproc)"
    exit 1
fi

# Create directories
sudo mkdir -p /etc/agentboss
sudo mkdir -p /opt/agentboss

# Install write policy
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
sudo cp "$SCRIPT_DIR/write_policy.py" /opt/agentboss/write_policy.py
sudo chmod +x /opt/agentboss/write_policy.py

# Initialize empty whitelist if not exists
if [ ! -f /etc/agentboss/whitelist.txt ]; then
    sudo touch /etc/agentboss/whitelist.txt
    sudo chmod 666 /etc/agentboss/whitelist.txt
fi

# Copy config
sudo cp "$SCRIPT_DIR/strfry.conf" /etc/strfry.conf

echo "Setup complete. Start relay with:"
echo "  strfry --config=/etc/strfry.conf relay"
