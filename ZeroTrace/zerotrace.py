#!/usr/bin/env python3
# Developer: Sreeraj
# GitHub: https://github.com/s-r-e-e-r-a-j

import subprocess
import os
import sys
from time import sleep
import requests
import shutil
from subprocess import call, check_call, CalledProcessError
from os.path import isfile, basename
from os import devnull, geteuid, system
from atexit import register
from argparse import ArgumentParser

# Global configuration variables
DNS_PORT = "53"  # DNS port for Tor
TOR_NETWORK = "10.0.0.0/10"  # Virtual network for Tor
LOCALHOST = "127.0.0.1"  # Local loopback address
EXCLUDED_NETWORKS = ("192.168.0.0/16", "172.16.0.0/12") # Networks to exclude from Tor
EXCLUDED_IPS = ("127.0.0.0/9", "127.128.0.0/10", "127.0.0.0/8")  # IPs to exclude
TOR_USER = subprocess.getoutput("id -ur debian-tor")  # Tor user ID
TOR_PORT = "9040"  # Tor transparent proxy port
TOR_CONFIG = '/etc/tor/torrc'  # Tor configuration file path
LOG_FILE = "zerotrace.log"  # Log file path

# Configuration to append to torrc file
TOR_CONFIG_CONTENT = f'''
## Added by {basename(__file__)} for ZeroTrace (Tor routing)
## Routes all traffic through Tor on port {TOR_PORT}
VirtualAddrNetwork {TOR_NETWORK}
AutomapHostsOnResolve 1
TransPort {TOR_PORT}
DNSPort {DNS_PORT}
'''

# Open log file for writing
log_handle = open(LOG_FILE, "a")

def log_message(message):
    """Write a message to the log file."""
    if log_handle:
        log_handle.write(message + "\n")

def cleanup():
    """Cleanup function to close log file when program exits."""
    if log_handle:
        log_handle.close()

def reset_network_rules():
    """Reset all iptables rules to default."""
    call(["iptables", "-F"])
    call(["iptables", "-t", "nat", "-F"])
    log_message("[+] Cleared all network rules")

def setup_network_rules():
    """Configure iptables rules to route traffic through Tor."""
    reset_network_rules()
    global EXCLUDED_IPS
    EXCLUDED_IPS.extend(EXCLUDED_NETWORKS)

    def restart_tor_service():
        """Restart Tor service when program exits."""
        with open(devnull, 'w') as null_device:
            try:
                tor_restart = check_call(
                    ["systemctl", "restart", "tor"],
                    stdout=null_device, stderr=null_device)
                if tor_restart == 0:
                    print(" \033[92m[+]\033[0m ZeroTrace: Privacy mode \033[92m[ACTIVE]\033[0m")
                    show_current_ip()
            except CalledProcessError as error:
                print(f"\033[91m[!]\033[0m Failed to restart Tor: {' '.join(error.cmd)}")

    register(restart_tor_service)  # Register cleanup function

    # Security rules recommended by Tor project
    call(["iptables", "-I", "OUTPUT", "!", "-o", "lo", "!", "-d", LOCALHOST, "!", "-s", LOCALHOST, "-p", "tcp", "-m", "tcp", "--tcp-flags", "ACK,FIN", "ACK,FIN", "-j", "DROP"])
    call(["iptables", "-I", "OUTPUT", "!", "-o", "lo", "!", "-d", LOCALHOST, "!", "-s", LOCALHOST, "-p", "tcp", "-m", "tcp", "--tcp-flags", "ACK,RST", "ACK,RST", "-j", "DROP"])
    
    # Set up NAT rules for Tor routing
    call(["iptables", "-t", "nat", "-A", "OUTPUT", "-m", "owner", "--uid-owner", TOR_USER, "-j", "RETURN"])
    call(["iptables", "-t", "nat", "-A", "OUTPUT", "-p", "udp", "--dport", DNS_PORT, "-j", "REDIRECT", "--to-ports", DNS_PORT])

    # Exclude specified networks from Tor routing
    for network in EXCLUDED_IPS:
        call(["iptables", "-t", "nat", "-A", "OUTPUT", "-d", network, "-j", "RETURN"])

    # Redirect all other TCP traffic through Tor
    call(["iptables", "-t", "nat", "-A", "OUTPUT", "-p", "tcp", "--syn", "-j", "REDIRECT", "--to-ports", TOR_PORT])
    
    # Allow established connections and excluded networks
    call(["iptables", "-A", "OUTPUT", "-m", "state", "--state", "ESTABLISHED,RELATED", "-j", "ACCEPT"])
    for network in EXCLUDED_IPS:
        call(["iptables", "-A", "OUTPUT", "-d", network, "-j", "ACCEPT"])

    # Allow Tor user traffic and reject all other traffic
    call(["iptables", "-A", "OUTPUT", "-m", "owner", "--uid-owner", TOR_USER, "-j", "ACCEPT"])
    call(["iptables", "-A", "OUTPUT", "-j", "REJECT"])

    log_message("[+] ZeroTrace: Network rules configured for Tor routing")

def get_location_info(ip_address):
    """Get geographical location information for an IP address."""
    try:
        response = requests.get(f"http://ip-api.com/json/{ip_address}")
        data = response.json()
        return data["country"], data["city"]
    except Exception as error:
        print(f"\033[91m[!]\033[0m Error getting location: {error}")
        return None, None

def show_current_ip():
    """Display the current public IP address and location."""
    print(" \033[93m[*]\033[0m ZeroTrace: Fetching public IP address...")
    attempts = 0
    public_ip = None
    
    # Try to get IP from Tor project API
    for attempts in range(9):
         try:
             re_s = requests.get('https://check.torproject.org/api/ip', timeout=5)
             re_s.raise_for_status()
             public_ip = re_s.json().get('IP')
             if public_ip:
                break  # Exit the loop if IP is successfully retrieved
         except requests.exceptions.RequestException:
                 print(" \033[93m[?]\033[0m ZeroTrace: Waiting for IP address...")
                 sleep(5)
         except ValueError:
                  break  # Invalid JSON response
    
    # Fallback to alternative method if Tor project API fails
    if not public_ip:
           res = requests.get('https://httpbin.org/ip')
           public_ip = res.json().get('origin')
    if not public_ip:
        exit("\033[91m[!]\033[0m ZeroTrace: Could not determine public IP address!")

    # Display IP and location information
    country, city = get_location_info(public_ip)
    if country and city:
        print(f" \033[92m[+]\033[0m ZeroTrace: Your IP: \033[92m{public_ip}\033[0m")
        print(f" \033[92m[+]\033[0m ZeroTrace: Location: \033[92m{country}, {city}\033[0m")
        log_message(f"[+] ZeroTrace: Current IP: {public_ip}")
        log_message(f"[+] ZeroTrace: Location: {country}, {city}")
    else:
        print(f" \033[92m[+]\033[0m ZeroTrace: Your IP: \033[92m{public_ip}\033[0m")
        print(" \033[93m[!]\033[0m ZeroTrace: Could not determine location")
        log_message(f"[+] ZeroTrace: Current IP: {public_ip}")

def change_ip_address():
    """Request a new Tor circuit (new IP address)."""
    call(['kill', '-HUP', '%s' % subprocess.getoutput('pidof tor')])
    show_current_ip()

def check_root():
    """Check if the script is running as root."""
    if geteuid() != 0:
        print(" \033[91m[!]\033[0m please run as root or with sudo.")
        exit(1)  

def install_tor():
    """Check if Tor is installed and install it if missing."""
    if shutil.which("tor") is not None:
        return True

    print(" [*] Tor is not installed. Attempting to install Tor...")

    try:
        check_call(["sudo", "apt-get", "update"])
        check_call(["sudo", "apt-get", "install", "-y", "tor"])
    except CalledProcessError:
        print(" [-] Failed to install Tor. Please install it manually.")
        return False

    if shutil.which("tor") is not None:
        print(" [+] Tor installed successfully.")
        system("clear")
        return True
    else:
        print(" [-] Tor installation failed.")
        return False

def main():
    """Main function to handle command line arguments and program flow."""
    # Check if running as root
    check_root()
    
    # Check if Tor is installed
    install_tor()
    
    # Set up command line interface
    parser = ArgumentParser(
        description='ZeroTrace - Route your internet traffic through Tor with automatic IP switching')
    
    # Command line options
    parser.add_argument('-s', '--start', action='store_true', 
                       help='Start ZeroTrace (route traffic through Tor)')
    parser.add_argument('-x', '--stop', action='store_true', 
                       help='Stop ZeroTrace and reset network rules')
    parser.add_argument('-n', '--new-ip', action='store_true', 
                       help='Get a new IP address through Tor')
    parser.add_argument('-i', '--ip', action='store_true', 
                       help='Show current public IP address')
    parser.add_argument('-a', '--auto', action='store_true', 
                       help='Automatically change IP at regular intervals')
    parser.add_argument('-t', '--time', type=int, default=500, 
                       help='Interval for automatic IP changes (seconds)')
    
    args = parser.parse_args()

    try:
        # Check if Tor configuration needs to be updated
        if isfile(TOR_CONFIG):
            if 'VirtualAddrNetwork' not in open(TOR_CONFIG).read():
                with open(TOR_CONFIG, 'a+') as config_file:
                    config_file.write(TOR_CONFIG_CONTENT)

        # Handle command line arguments
        if args.start:
            setup_network_rules()
        elif args.stop:
            reset_network_rules()
            print(" \033[93m[!]\033[0m ZeroTrace: Privacy mode \033[91m[INACTIVE]\033[0m")
            log_message("[!] ZeroTrace: Privacy mode deactivated")
        elif args.ip:
            show_current_ip()
        elif args.new_ip:
            change_ip_address()
        elif args.auto:
            interval = args.time
            print(f" \033[92m[+]\033[0m ZeroTrace: Auto IP switching enabled. Interval:{interval} seconds")
            try:
                while True:
                    change_ip_address()
                    print(" \033[92m[*]\033[0m ZeroTrace: Successfully changed IP address\n")
                    sleep(interval)
            except KeyboardInterrupt:
                print("\n\033[91m[!]\033[0m ZeroTrace: Stopped by user")
        else:
            parser.print_help()
    except Exception as error:
        print(f"\033[91m[!]\033[0m ZeroTrace: Run as administrator: {error}")
        log_message(f"[!] ZeroTrace: Error: {error}")

if __name__ == '__main__':
    # Register cleanup function
    register(cleanup)
    main()
