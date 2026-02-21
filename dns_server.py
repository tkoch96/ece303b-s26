

import sys

def main():
    if len(sys.argv) != 3:
        print("Usage: python dns_server.py [dns_server_ip_address] [web_server_address]")
        sys.exit(1)

    dns_ip = sys.argv[1]
    web_ip = sys.argv[2]
    port = 5353

    ## TODO -- implement your dns server

if __name__ == "__main__":
    main()