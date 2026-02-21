import sys

def main():
    if len(sys.argv) != 3:
        print("Usage: python reverse_proxy.py [listen_port] [dns_server_address]")
        sys.exit(1)

    listen_port = int(sys.argv[1])
    dns_server_ip = sys.argv[2]
    domain_to_resolve = "myawesomewebserver.com"

    ## TODO -- implement your reverse proxy


if __name__ == "__main__":
    main()