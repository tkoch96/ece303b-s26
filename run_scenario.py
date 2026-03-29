import time
import csv
import sys
from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import OVSController
from mininet.link import TCLink
from mininet.cli import CLI
from mininet.log import setLogLevel, info

class DynamicTopo(Topo):
	def __init__(self, topo_specs, **opts):
		self.topo_specs = topo_specs
		super(DynamicTopo, self).__init__(**opts)

	def build(self):
		hosts_added = set()

		for h1, h2, link_name in self.topo_specs:
			# Add hosts if they haven't been added yet
			if h1 not in hosts_added:
				self.addHost(h1)
				hosts_added.add(h1)
			if h2 not in hosts_added:
				self.addHost(h2)
				hosts_added.add(h2)
			
			# Add a direct link between the two hosts
			self.addLink(h1, h2)

def parse_topology(filepath):
	"""Reads topology.csv and returns a list of (host1, host2, link_name)."""
	specs = []
	link_map = {} # Maps 'link_name' -> ('host1', 'host2')
	
	with open(filepath, 'r') as f:
		reader = csv.reader(f)
		for row in reader:
			if not row or row[0].startswith('#'): continue
			h1, h2, link_name = [x.strip() for x in row]
			specs.append((h1, h2, link_name))
			link_map[link_name] = (h1, h2)
			
	return specs, link_map

def parse_scenario(filepath):
	"""Reads scenario.csv and returns a list of events sorted by time."""
	events = []
	with open(filepath, 'r') as f:
		reader = csv.reader(f)
		for row in reader:
			if not row or row[0].startswith('#'): continue
			link_name, t, lat, bw, loss = [x.strip() for x in row]
			events.append({
				'link_name': link_name,
				'time': float(t),
				'latency': f"{lat}ms",
				'bw_mbps': float(bw) / 1000.0, # Convert kbps to Mbps for Mininet
				'loss': float(loss)
			})
			
	# Ensure events are processed in chronological order
	events.sort(key=lambda x: x['time'])
	return events

def apply_network_change(net, link_map, event):
	"""Applies TCLink parameters to the specified link at runtime."""
	link_name = event['link_name']
	
	if link_name not in link_map:
		info(f"[!] Warning: link {link_name} not found in topology. Skipping.\n")
		return

	h1_name, h2_name = link_map[link_name]
	node1 = net.get(h1_name)
	node2 = net.get(h2_name)

	# Find the specific interface connecting node1 to node2
	intfs = node1.connectionsTo(node2)
	if not intfs:
		info(f"[!] Warning: No physical link found between {h1_name} and {h2_name}.\n")
		return
		
	intf1, intf2 = intfs[0] # Grab the first (and likely only) link between them

	info(f"[*] Time {event['time']}s -> Modifying {link_name} ({h1_name}<->{h2_name}): "
		 f"{event['latency']}, {event['bw_mbps']}Mbps, {event['loss']}% loss\n")

	# Apply configuration to both sides of the link to ensure bi-directional limits
	intf1.config(bw=event['bw_mbps'], delay=event['latency'], loss=event['loss'])
	intf2.config(bw=event['bw_mbps'], delay=event['latency'], loss=event['loss'])

def main(topo_file, scenario_file):
	topo_specs, link_map = parse_topology(topo_file)
	events = parse_scenario(scenario_file)

	topo = DynamicTopo(topo_specs)
	net = Mininet(topo=topo, controller=OVSController, link=TCLink)
	net.start()

	# Print out auto-assigned IPs so you know how to configure your commands
	info("\n[*] Auto-Assigned IP Addresses:\n")
	for host in net.hosts:
		info(f"    {host.name}: {host.IP()}\n")
	info("\n")

	info("[*] Network is up. Starting scenario timeline...\n")
	start_time = time.time()
	event_idx = 0

	# Monitor loop
	while event_idx < len(events):
		elapsed = time.time() - start_time
		next_event = events[event_idx]
		
		if elapsed >= next_event['time']:
			apply_network_change(net, link_map, next_event)
			event_idx += 1
		else:
			time.sleep(0.1) # Short sleep to prevent CPU pegging

	info("\n[*] Scenario complete. Dropping into CLI for testing.\n")
	CLI(net)

	info("[*] Shutting down...\n")
	net.stop()

if __name__ == '__main__':
	setLogLevel('info')
	if len(sys.argv) != 3:
		print("Usage: sudo /Users/tomkoch/Documents/venv/bin/python3.14 run_scenario.py <topology.csv> <scenario.csv>")
		sys.exit(1)
	
	main(sys.argv[1], sys.argv[2])