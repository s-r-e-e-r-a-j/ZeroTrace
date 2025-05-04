# Developer : Sreeraj
# GitHub : https://github.com/s-r-e-e-r-a-j

from subprocess import call, check_call, CalledProcessError
from os.path import isfile, basename
from os import devnull
from sys import exit, stdout, stderr
from atexit import register
from argparse import ArgumentParser
from json import load
from urllib.request import urlopen
from urllib.error import URLError
from time import sleep
import subprocess
import requests
import shutil

class ZeroTrace:
    def __init__(self):
        # Network configuration settings
        self.dns_port = "53"  # DNS port for Tor
        self.tor_network = "10.0.0.0/10"  # Virtual network for Tor
        self.localhost = "127.0.0.1"  # Local loopback address
        self.excluded_networks = ["192.168.0.0/16", "172.16.0.0/12"]  # Networks to exclude from Tor
        self.excluded_ips = ["127.0.0.0/9", "127.128.0.0/10", "127.0.0.0/8"]  # IPs to exclude
        self.tor_user = subprocess.getoutput("id -ur debian-tor")  # Tor user ID
        self.tor_port = "9040"  # Tor transparent proxy port
        self.tor_config = '/etc/tor/torrc'  # Tor configuration file path
        
        # Configuration to append to torrc file
        self.tor_config_content = f'''
## Added by {basename(__file__)} for ZeroTrace (Tor routing)
## Routes all traffic through Tor on port {self.tor_port}
VirtualAddrNetwork {self.tor_network}
AutomapHostsOnResolve 1
TransPort {self.tor_port}
DNSPort {self.dns_port}
'''

        self.log_file = "zerotrace.log"  # Log file path
        self.log_handle = open(self.log_file, "a")  # Open log file for writing

    def __del__(self):
        if self.log_handle:
            self.log_handle.close()  # Close log file when object is destroyed

    def log_message(self, message):
        if self.log_handle:
            self.log_handle.write(message + "\n")  # Write message to log

    def reset_network_rules(self):
        # Clear all existing iptables rules
        call(["iptables", "-F"])
        call(["iptables", "-t", "nat", "-F"])
        self.log_message("[+] Cleared all network rules")

    def setup_network_rules(self):
        # Set up iptables rules to route traffic through Tor
        self.reset_network_rules()
        self.excluded_ips.extend(self.excluded_networks)

        @register
        def restart_tor_service():
            # Function to restart Tor service when program exits
            with open(devnull, 'w') as null_device:
                try:
                    tor_restart = check_call(
                        ["service", "tor", "restart"],
                        stdout=null_device, stderr=null_device)
                    if tor_restart == 0:
                        print(" \033[92m[+]\033[0m ZeroTrace: Privacy mode \033[92m[ACTIVE]\033[0m")
                        self.show_current_ip()
                except CalledProcessError as error:
                    print(f"\033[91m[!]\033[0m Failed to restart Tor: {' '.join(error.cmd)}")

        # Security rules recommended by Tor project
        call(["iptables", "-I", "OUTPUT", "!", "-o", "lo", "!", "-d", self.localhost, "!", "-s", self.localhost, "-p", "tcp", "-m", "tcp", "--tcp-flags", "ACK,FIN", "ACK,FIN", "-j", "DROP"])
        call(["iptables", "-I", "OUTPUT", "!", "-o", "lo", "!", "-d", self.localhost, "!", "-s", self.localhost, "-p", "tcp", "-m", "tcp", "--tcp-flags", "ACK,RST", "ACK,RST", "-j", "DROP"])
        
        # Set up NAT rules for Tor routing
        call(["iptables", "-t", "nat", "-A", "OUTPUT", "-m", "owner", "--uid-owner", self.tor_user, "-j", "RETURN"])
        call(["iptables", "-t", "nat", "-A", "OUTPUT", "-p", "udp", "--dport", self.dns_port, "-j", "REDIRECT", "--to-ports", self.dns_port])

        # Exclude specified networks from Tor routing
        for network in self.excluded_ips:
            call(["iptables", "-t", "nat", "-A", "OUTPUT", "-d", network, "-j", "RETURN"])

        # Redirect all other TCP traffic through Tor
        call(["iptables", "-t", "nat", "-A", "OUTPUT", "-p", "tcp", "--syn", "-j", "REDIRECT", "--to-ports", self.tor_port])
        
        # Allow established connections and excluded networks
        call(["iptables", "-A", "OUTPUT", "-m", "state", "--state", "ESTABLISHED,RELATED", "-j", "ACCEPT"])
        for network in self.excluded_ips:
            call(["iptables", "-A", "OUTPUT", "-d", network, "-j", "ACCEPT"])

        # Allow Tor user traffic and reject all other traffic
        call(["iptables", "-A", "OUTPUT", "-m", "owner", "--uid-owner", self.tor_user, "-j", "ACCEPT"])
        call(["iptables", "-A", "OUTPUT", "-j", "REJECT"])

        self.log_message("[+] ZeroTrace: Network rules configured for Tor routing")

    def get_location_info(self, ip_address):
        # Get geographical location information for an IP address
        try:
            response = requests.get(f"http://ip-api.com/json/{ip_address}")
            data = response.json()
            return data["country"], data["city"]
        except Exception as error:
            print(f"\033[91m[!]\033[0m Error getting location: {error}")
            return None, None

    def show_current_ip(self):
        # Display the current public IP address and location
        print(" \033[93m[*]\033[0m ZeroTrace: Fetching public IP address...")
        attempts = 0
        public_ip = None
        
        # Try to get IP from Tor project API
        while attempts < 12 and not public_ip:
            attempts += 1
            try:
                public_ip = load(urlopen('https://check.torproject.org/api/ip'))['IP']
            except URLError:
                sleep(5)
                print(" \033[93m[?]\033[0m ZeroTrace: Waiting for IP address...")
            except ValueError:
                break
        
        # Fallback to alternative method if Tor project API fails
        if not public_ip:
            public_ip = subprocess.getoutput('wget -qO - ifconfig.me')
        if not public_ip:
            exit("\033[91m[!]\033[0m ZeroTrace: Could not determine public IP address!")

        # Display IP and location information
        country, city = self.get_location_info(public_ip)
        if country and city:
            print(f" \033[92m[+]\033[0m ZeroTrace: Your IP: \033[92m{public_ip}\033[0m")
            print(f" \033[92m[+]\033[0m ZeroTrace: Location: \033[92m{country}, {city}\033[0m")
            self.log_message(f"[+] ZeroTrace: Current IP: {public_ip}")
            self.log_message(f"[+] ZeroTrace: Location: {country}, {city}")
        else:
            print(f" \033[92m[+]\033[0m ZeroTrace: Your IP: \033[92m{public_ip}\033[0m")
            print(" \033[93m[!]\033[0m ZeroTrace: Could not determine location")
            self.log_message(f"[+] ZeroTrace: Current IP: {public_ip}")

    def change_ip_address(self):
        # Request a new Tor circuit (new IP address)
        call(['kill', '-HUP', '%s' % subprocess.getoutput('pidof tor')])
        self.show_current_ip()

def install_tor():
    if shutil.which("tor") is not None:
        print("\033[92m[+]\033[0m Tor is already installed.")
        return True

    print("[*] Tor is not installed. Attempting to install Tor...")

    try:
        subprocess.check_call(["sudo", "apt", "update"])
        subprocess.check_call(["sudo", "apt", "install", "-y", "tor"])
    except subprocess.CalledProcessError:
        print("[-] Failed to install Tor. Please install it manually.")
        return False

    if shutil.which("tor") is not None:
        print("[+] Tor installed successfully.")
        subprocess.check_call(["clear"])
        return True
    else:
        print("[-] Tor installation failed.")
        return False


def main():
    #check Tor is installed or not
    install_tor()
    subprocess.check_call(["clear"])
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
    parser.add_argument('-t', '--time', type=int, default=3600, 
                       help='Interval for automatic IP changes (seconds)')
    
    args = parser.parse_args()

    try:
        zerotrace = ZeroTrace()
        
        # Check if Tor configuration needs to be updated
        if isfile(zerotrace.tor_config):
            if 'VirtualAddrNetwork' not in open(zerotrace.tor_config).read():
                with open(zerotrace.tor_config, 'a+') as config_file:
                    config_file.write(zerotrace.tor_config_content)

        # Handle command line arguments
        if args.start:
            zerotrace.setup_network_rules()
        elif args.stop:
            zerotrace.reset_network_rules()
            print(" \033[93m[!]\033[0m ZeroTrace: Privacy mode \033[91m[INACTIVE]\033[0m")
            zerotrace.log_message("[!] ZeroTrace: Privacy mode deactivated")
        elif args.ip:
            zerotrace.show_current_ip()
        elif args.new_ip:
            zerotrace.change_ip_address()
        elif args.auto:
            interval = args.time
            try:
                while True:
                    zerotrace.change_ip_address()
                    print(" \033[92m[*]\033[0m ZeroTrace: Successfully changed IP address\n")
                    sleep(interval)
            except KeyboardInterrupt:
                print("\n\033[91m[!]\033[0m ZeroTrace: Stopped by user")
        else:
            parser.print_help()
    except Exception as error:
        print(f"\033[91m[!]\033[0m ZeroTrace: Run as administrator: {error}")
        zerotrace.log_message(f"[!] ZeroTrace: Error: {error}")


if __name__ == '__main__':
    main()
