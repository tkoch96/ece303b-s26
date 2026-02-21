import sys
import os

def main():
    if len(sys.argv) != 3:
        print("Usage: python client.py [num_queries] [destination_port]")
        sys.exit(1)

    num_queries = int(sys.argv[1])
    destination_port = sys.argv[2]
    url = f"http://localhost:{destination_port}"
    
    # Ensure logs directory exists
    os.makedirs("logs", exist_ok=True)
    log_filepath = os.path.join("logs", "client_requests.log")

    ## TODO -- implement your basic client

if __name__ == "__main__":
    main()