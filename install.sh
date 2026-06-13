#!/bin/bash
# Install Construct — agent lifecycle engine
set -euo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)"
echo "[construct] Installing..."
pip install -q pyyaml 2>/dev/null || true
sudo tee /etc/systemd/system/construct.service > /dev/null << SERVICE
[Unit]
Description=Construct — Agent Lifecycle Engine
Documentation=https://github.com/SuperInstance/construct
After=network.target
[Service]
Type=simple
User=${USER:-ubuntu}
ExecStart=/usr/bin/python3 $DIR/construct.py run
WorkingDirectory=$DIR
Restart=on-failure
RestartSec=5
[Install]
WantedBy=multi-user.target
SERVICE
sudo systemctl daemon-reload && sudo systemctl enable construct && sudo systemctl restart construct
echo "[construct] Running — python3 $DIR/construct.py"
