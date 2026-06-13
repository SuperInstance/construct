#!/bin/bash
set -euo pipefail
sudo systemctl stop construct 2>/dev/null || true
sudo systemctl disable construct 2>/dev/null || true
sudo rm -f /etc/systemd/system/construct.service
sudo systemctl daemon-reload
echo "[construct] Stopped"
