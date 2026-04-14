echo "[*] Installing Mininet and Open vSwitch..."
sudo apt-get install -y mininet openvswitch-switch
sudo systemctl start openvswitch-switch
sudo ln -s /usr/bin/ovs-testcontroller /usr/bin/ovs-controller