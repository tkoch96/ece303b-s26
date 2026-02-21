#!/bin/bash

# ==========================================
# ECE303 Project: Apache Rescue & Restart
# ==========================================

echo "[*] Initiating Apache Web Server recovery..."

# 1. Stop Apache gracefully in case it is in a hung state
sudo systemctl stop apache2

# 2. Check for port 80 conflicts (Classic student mistake: running their proxy on port 80)
# This grabs the PID of whatever is currently listening on port 80
PORT_PID=$(sudo ss -lptn 'sport = :80' | grep pid | sed -r 's/.*pid=([0-9]+).*/\1/' | head -n 1)

if [ ! -z "$PORT_PID" ]; then
    echo "[!] Warning: Process $PORT_PID is currently hogging port 80."
    echo "[!] Killing the rogue process so Apache can bind to it..."
    sudo kill -9 $PORT_PID
    sleep 1
fi

# 3. Restore the original dummy content
# This ensures your end-to-end tests will always see the expected string
echo "[*] Restoring the original 'Hello World' index.html..."
sudo mkdir -p /var/www/html
sudo bash -c 'echo "<html><body><h1>Hello World from the Backend!</h1><p>If you see this, your proxy worked.</p></body></html>" > /var/www/html/index.html'
sudo chmod 644 /var/www/html/index.html

# 4. Start Apache
echo "[*] Starting the Apache service..."
sudo systemctl start apache2

# 5. Verify the service started successfully
if systemctl is-active --quiet apache2; then
    echo "=========================================="
    echo "[+] Success! Apache is up and running."
    echo "[+] You can test it directly by running: curl http://localhost"
    echo "=========================================="
else
    echo "=========================================="
    echo "[-] Error: Apache failed to start."
    echo "[-] Check what went wrong by typing: sudo journalctl -u apache2 --no-pager | tail -n 20"
    echo "=========================================="
fi