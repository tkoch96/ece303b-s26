import sys
import time
import urllib.request
import urllib.error
import threading
import os

def parse_query_profile(filepath):
    """
    Parses a CSV profile into a pre-computed schedule of request timestamps.
    Format expected: start_time_sec, end_time_sec, requests_per_sec
    """
    schedule = []
    with open(filepath, 'r') as f:
        for line in f:
            line = line.strip()
            # Skip comments and empty lines
            if not line or line.startswith('#'):
                continue
            
            parts = line.split(',')
            if len(parts) >= 3:
                start_sec = float(parts[0].strip())
                end_sec = float(parts[1].strip())
                rate = float(parts[2].strip())
                
                if rate > 0:
                    step = 1.0 / rate
                    t = start_sec
                    while t < end_sec:
                        schedule.append(t)
                        t += step
                        
    # Ensure the schedule is perfectly chronological
    schedule.sort()
    return schedule

def make_request(target_url, requested_domain, log_file, log_lock):
    """Executes a single HTTP GET request and safely writes to the shared log."""
    time_requested = time.time()
    response_str = ""
    
    try:
        # Include the Host header in case the proxy relies on it to resolve DNS
        req = urllib.request.Request(target_url, headers={'Host': requested_domain})
        with urllib.request.urlopen(req, timeout=5) as response:
            body = response.read().decode('utf-8', errors='ignore')
            response_str = body.replace('\n', ' ').strip()
    except urllib.error.URLError as e:
        response_str = f"ERROR: {str(e)}"
    except Exception as e:
        response_str = f"UNEXPECTED ERROR: {str(e)}"

    time_received_response = time.time()

    # requested_domain <tab> time_requested <tab> time_received_response <tab> response_string
    log_line = f"{requested_domain}\t{time_requested:.4f}\t{time_received_response:.4f}\t{response_str}\n"
    
    # Use a thread lock to prevent mangled log lines when requests fire concurrently
    with log_lock:
        log_file.write(log_line)
        log_file.flush()

def main():
    # Strictly enforce the 3 arguments specified in the assignment rubric
    if len(sys.argv) != 4:
        print("Usage: python advanced_client.py [query_profile_path] [destination_port] [log_path]")
        sys.exit(1)

    profile_path = sys.argv[1]
    dest_port = sys.argv[2]
    log_path = sys.argv[3]
    
    # =====================================================================
    # NETWORK CONFIGURATION
    # For Local Testing: Leave this as "127.0.0.1" (localhost)
    # For Mininet Simulation: Read the proxy's client-facing IP address 
    # from the simulation startup logs and update this variable! 
    # (e.g., target_ip = "10.0.1.2")
    # =====================================================================
    target_ip = "10.0.1.2" 
    
    target_url = f"http://{target_ip}:{dest_port}/"
    requested_domain = "myawesomewebserver.com"

    # Ensure log directory exists if the path includes one
    log_dir = os.path.dirname(log_path)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir)

    schedule = parse_query_profile(profile_path)
    if not schedule:
        print(f"No valid request schedule found in {profile_path}.")
        sys.exit(1)

    print(f"[*] Loaded profile: {len(schedule)} total requests scheduled.")
    print(f"[*] Target: {target_url} | Logging to: {log_path}")

    log_lock = threading.Lock()
    
    # Open log file and start the timeline
    with open(log_path, 'w') as log_file:
        start_time = time.time()
        
        for scheduled_time in schedule:
            now = time.time()
            elapsed = now - start_time
            wait_time = scheduled_time - elapsed
            
            # If we are ahead of schedule, sleep until it's time to fire
            if wait_time > 0:
                time.sleep(wait_time)
            
            # Fire the request in a separate thread so slow network responses don't block the next request
            threading.Thread(
                target=make_request, 
                args=(target_url, requested_domain, log_file, log_lock),
                daemon=True
            ).start()

        # Wait briefly for the final trailing requests to finish before exiting
        time.sleep(6)
        
    print("[*] All scheduled requests fired and logged.")

if __name__ == "__main__":
    main()