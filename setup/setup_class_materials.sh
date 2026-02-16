#!/bin/bash

# ==========================================
# ECE303 Project Environment Setup Script
# ==========================================

# 1. Update System and Install Prerequisites
echo "[*] Updating package lists..."
sudo apt-get update -y
sudo apt-get install -y software-properties-common curl git ufw

# 2. Set up Apache Web Server (The Backend Target)
echo "[*] Installing Apache Web Server..."
sudo apt-get install -y apache2

# Adjust Firewall to allow web traffic (Standard HTTP/HTTPS)
echo "[*] Configuring Firewall..."
sudo ufw allow 'Apache'

# Create a custom "Hello World" page for testing
# This verifies the server is running and gives the proxy a specific string to fetch.
echo "[*] Creating dummy content..."
sudo bash -c 'echo "<html><body><h1>Hello World from the Backend!</h1><p>If you see this, your proxy worked.</p></body></html>" > /var/www/html/index.html'

# Restart Apache to ensure changes take effect
sudo systemctl restart apache2
echo "[+] Apache is running on port 80."

# 3. Set up Python 3.14 Environment
echo "[*] Setting up Python 3.14..."

# Add the deadsnakes PPA (standard source for specific Python versions on Ubuntu)
sudo add-apt-repository -y ppa:deadsnakes/ppa
sudo apt-get update -y

# Install Python 3.14 and the venv module
sudo apt-get install -y python3.14 python3.14-venv python3.14-dev

# Create a virtual environment in the current directory
# This isolates the project dependencies from the system python.
echo "[*] Creating virtual environment 'venv' in current directory..."
python3.14 -m venv venv

echo "=========================================="
echo "[+] Setup Complete!"
echo "------------------------------------------"
echo "1. Apache is serving content at: http://$(curl -s ifconfig.me) (Public IP) or http://localhost"
echo "2. To activate the Python environment, run: source venv/bin/activate"
echo "=========================================="
