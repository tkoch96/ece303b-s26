import time
import csv
import threading
import sys
from mininet.topo import Topo
from mininet.net import Mininet
from mininet.link import TCLink
from mininet.cli import CLI
from mininet.log import setLogLevel, info

class DynamicTopo(Topo):
	def __init__(self, topo_specs, **opts):
		self.topo_specs = topo_specs
		super(DynamicTopo, self).__init__(**opts)

	def build(self):
		hosts_added = set()
		subnet_counter = 1 # Start at 10.0.1.x

		for h1, h2, link_name in self.topo_specs:
			# Add hosts if they haven't been added yet
			if h1 not in hosts_added:
				# ip=None prevents Mininet from auto-assigning a default global IP
				self.addHost(h1, ip=None) 
				hosts_added.add(h1)
			if h2 not in hosts_added:
				self.addHost(h2, ip=None)
				hosts_added.add(h2)
			
			# Define isolated IP addresses for this specific link
			# E.g., Link 1 gets 10.0.1.1 and 10.0.1.2
			# E.g., Link 2 gets 10.0.2.1 and 10.0.2.2
			ip1 = f'10.0.{subnet_counter}.1/24'
			ip2 = f'10.0.{subnet_counter}.2/24'
			
			# Add the link and explicitly assign the IPs to the interfaces on each end
			self.addLink(h1, h2, params1={'ip': ip1}, params2={'ip': ip2})
			
			subnet_counter += 1

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
			link_name, t, bw, lat, loss = [x.strip() for x in row]
			events.append({
				'link_name': link_name,
				'time': float(t),
				'latency': f"{lat}ms",
				'bw_mbps': float(bw), # Convert kbps to Mbps for Mininet
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

def run_scenario_loop(net, link_map, events):
	"""Runs the scenario events in a continuous background loop."""
	while True:
		info("\n[*] Starting scenario cycle...\n")
		start_time = time.time()
		event_idx = 0
		
		while event_idx < len(events):
			elapsed = time.time() - start_time
			next_event = events[event_idx]
			
			if elapsed >= next_event['time']:
				apply_network_change(net, link_map, next_event)
				event_idx += 1
			else:
				time.sleep(0.1)
		
		info("\n[*] Scenario cycle finished. Restarting in 1 second...\n")
		time.sleep(1)

def main(topo_file, scenario_file):
	topo_specs, link_map = parse_topology(topo_file)
	events = parse_scenario(scenario_file)

	topo = DynamicTopo(topo_specs)
	net = Mininet(topo=topo, link=TCLink)
	net.start()

	# Print Network Info (same as your original code)
	info("\n" + "="*40 + "\n")
	for host in net.hosts:
		info(f"Node: {host.name}\n")
		for intf in host.intfList():
			if intf.name != 'lo':
				info(f"  └─ Interface {intf.name} -> IP: {intf.IP()}\n")
	info("="*40 + "\n\n")

	# 1. Start the background thread
	# Setting daemon=True ensures the thread dies when the main program exits
	background_thread = threading.Thread(
		target=run_scenario_loop, 
		args=(net, link_map, events),
		daemon=True 
	)
	background_thread.start()

	# 2. Drop to CLI immediately
	info("[*] Background scenario running. Dropping into CLI...\n")
	CLI(net)

	# 3. Cleanup after exiting CLI
	info("[*] Shutting down...\n")
	net.stop()

if __name__ == '__main__':
	setLogLevel('info')
	if len(sys.argv) != 3:
		print("Usage: sudo python3 run_scenario.py <topology.csv> <scenario.csv>")
		sys.exit(1)
	
	main(sys.argv[1], sys.argv[2])