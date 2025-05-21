#!/usr/bin/env bash

# Developer: Sreeraj
# GitHub: https://github.com/s-r-e-e-r-a-j

# Global configuration variables
DNS_PORT="53"  # DNS port for Tor
TOR_NETWORK="10.0.0.0/10"  # Virtual network for Tor
LOCALHOST="127.0.0.1"  # Local loopback address
EXCLUDED_NETWORKS=("192.168.0.0/16" "172.16.0.0/12") # Networks to exclude from Tor
EXCLUDED_IPS=("127.0.0.0/9" "127.128.0.0/10" "127.0.0.0/8")  # IPs to exclude
TOR_PORT="9040"  # Tor transparent proxy port
TOR_CONFIG='/etc/tor/torrc'  # Tor configuration file path
LOG_FILE="zerotrace.log"  # Log file path

# Detect Linux distribution
detect_distribution() {
    if [ -f /etc/os-release ]; then
        if grep -qi "debian" /etc/os-release || grep -qi "ubuntu" /etc/os-release; then
            echo "debian"
        elif grep -qi "fedora" /etc/os-release || grep -qi "centos" /etc/os-release || grep -qi "rhel" /etc/os-release; then
            echo "fedora"
        elif grep -qi "arch" /etc/os-release; then
            echo "arch"
        else
            echo "unknown"
        fi
    else
        echo "unknown"
    fi
}

DISTRO=$(detect_distribution)

# Set Tor user based on distribution
if [ "$DISTRO" = "debian" ]; then
    TOR_USER=$(id -ur debian-tor 2>/dev/null)
elif [ "$DISTRO" = "fedora" ]; then
    TOR_USER=$(id -ur toranon 2>/dev/null)
else
    TOR_USER=$(id -ur tor 2>/dev/null)  # Fallback for other distributions
fi

# Configuration to append to torrc file
TOR_CONFIG_CONTENT="
## Added by $(basename "$0") for ZeroTrace (Tor routing)
## Routes all traffic through Tor on port $TOR_PORT
VirtualAddrNetwork $TOR_NETWORK
AutomapHostsOnResolve 1
TransPort $TOR_PORT
DNSPort $DNS_PORT
"

# Open log file for writing
exec 3>>"$LOG_FILE"

log_message() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') $1" >&3
}

cleanup() {
    if [ -e /proc/$$/fd/3 ]; then
        exec 3>&-
    fi
}

reset_network_rules() {
    iptables -F
    iptables -t nat -F
    log_message "[+] Cleared all network rules"
}

setup_network_rules() {
    reset_network_rules
    EXCLUDED_IPS+=("${EXCLUDED_NETWORKS[@]}")

    restart_tor_service() {
        if [ "$DISTRO" = "debian" ] || [ "$DISTRO" = "fedora" ] || [ "$DISTRO" = "arch" ]; then
            if systemctl restart tor >/dev/null 2>&1; then
                echo -e " \033[92m[+]\033[0m ZeroTrace: Privacy mode \033[92m[ACTIVE]\033[0m"
                show_current_ip
            else
                echo -e "\033[91m[!]\033[0m Failed to restart Tor"
            fi
        fi
    }

    trap restart_tor_service EXIT

    # Security rules recommended by Tor project
    iptables -I OUTPUT ! -o lo ! -d "$LOCALHOST" ! -s "$LOCALHOST" -p tcp -m tcp --tcp-flags ACK,FIN ACK,FIN -j DROP
    iptables -I OUTPUT ! -o lo ! -d "$LOCALHOST" ! -s "$LOCALHOST" -p tcp -m tcp --tcp-flags ACK,RST ACK,RST -j DROP
    
    # Set up NAT rules for Tor routing
    iptables -t nat -A OUTPUT -m owner --uid-owner "$TOR_USER" -j RETURN
    iptables -t nat -A OUTPUT -p udp --dport "$DNS_PORT" -j REDIRECT --to-ports "$DNS_PORT"

    # Exclude specified networks from Tor routing
    for network in "${EXCLUDED_IPS[@]}"; do
        iptables -t nat -A OUTPUT -d "$network" -j RETURN
    done

    # Redirect all other TCP traffic through Tor
    iptables -t nat -A OUTPUT -p tcp --syn -j REDIRECT --to-ports "$TOR_PORT"
    
    # Allow established connections and excluded networks
    iptables -A OUTPUT -m state --state ESTABLISHED,RELATED -j ACCEPT
    for network in "${EXCLUDED_IPS[@]}"; do
        iptables -A OUTPUT -d "$network" -j ACCEPT
    done

    # Allow Tor user traffic and reject all other traffic
    iptables -A OUTPUT -m owner --uid-owner "$TOR_USER" -j ACCEPT
    iptables -A OUTPUT -j REJECT

    log_message "[+] ZeroTrace: Network rules configured for Tor routing"
}

get_location_info() {
    local ip_address=$1
    local country city
    if response=$(curl -s "http://ip-api.com/json/$ip_address"); then
        country=$(echo "$response" | jq -r '.country // empty')
        city=$(echo "$response" | jq -r '.city // empty')
        echo "$country,$city"
    else
        echo ","
    fi
}

show_current_ip() {
    echo -e " \033[93m[*]\033[0m ZeroTrace: Fetching public IP address..."
    public_ip=""
    
    # Try to get IP from Tor project API
    for attempt in {1..9}; do
        if response=$(curl -s https://check.torproject.org/api/ip --connect-timeout 5 2>/dev/null); then
            public_ip=$(echo "$response" | jq -r '.IP // empty')
            [ -n "$public_ip" ] && break
        fi
        echo -e " \033[93m[?]\033[0m ZeroTrace: Waiting for IP address..."
        sleep 5
    done
    
    # Fallback to alternative method if Tor project API fails
    if [ -z "$public_ip" ]; then
        if response=$(curl -s https://httpbin.org/ip); then
            public_ip=$(echo "$response" | jq -r '.origin // empty')
        fi
    fi
    
    if [ -z "$public_ip" ]; then
        echo -e "\033[91m[!]\033[0m ZeroTrace: Could not determine public IP address!"
        exit 1
    fi

    # Display IP and location information
    IFS=, read -r country city <<< "$(get_location_info "$public_ip")"
    if [ -n "$country" ] && [ -n "$city" ]; then
        echo -e " \033[92m[+]\033[0m ZeroTrace: Your IP: \033[92m$public_ip\033[0m"
        echo -e " \033[92m[+]\033[0m ZeroTrace: Location: \033[92m$country, $city\033[0m"
        log_message "[+] ZeroTrace: Current IP: $public_ip"
        log_message "[+] ZeroTrace: Location: $country, $city"
    else
        echo -e " \033[92m[+]\033[0m ZeroTrace: Your IP: \033[92m$public_ip\033[0m"
        echo -e " \033[93m[!]\033[0m ZeroTrace: Could not determine location"
        log_message "[+] ZeroTrace: Current IP: $public_ip"
    fi
}

change_ip_address() {
    kill -HUP "$(pidof tor)" >/dev/null 2>&1
    show_current_ip
}

check_root() {
    if [ "$(id -u)" -ne 0 ]; then
        echo -e " \033[91m[!]\033[0m please run as root or with sudo."
        exit 1
    fi
}

install_tor() {
    if command -v tor >/dev/null 2>&1; then
        return 0
    fi

    echo " [*] Tor is not installed. Attempting to install Tor..."

    case "$DISTRO" in
        debian)
            apt-get update && apt-get install -y tor || return 1
            ;;
        fedora)
            dnf install -y tor || return 1
            ;;
        arch)
            pacman -Sy --noconfirm tor || return 1
            ;;
        *)
            echo " [-] Unsupported distribution. Please install Tor manually."
            return 1
            ;;
    esac

    if command -v tor >/dev/null 2>&1; then
        echo " [+] Tor installed successfully."
        clear
        return 0
    else
        echo " [-] Tor installation failed."
        return 1
    fi
}

install_jq() {
    if command -v jq >/dev/null 2>&1; then
        return 0
    fi

    echo " [*] jq is not installed. Attempting to install jq..."

    case "$DISTRO" in
        debian)
            apt-get update && apt-get install -y jq || return 1
            ;;
        fedora)
            dnf install -y jq || return 1
            ;;
        arch)
            pacman -Sy --noconfirm jq || return 1
            ;;
        *)
            echo " [-] Unsupported distribution. Please install jq manually."
            return 1
            ;;
    esac

    if command -v jq >/dev/null 2>&1; then
        echo " [+] jq installed successfully."
        clear
        return 0
    else
        echo " [-] jq installation failed."
        return 1
    fi
}

main() {
    check_root
    
    if ! install_tor; then
        exit 1
    fi
    
    if ! install_jq; then
         exit 1
    fi
    
    # If no arguments provided, show usage
    if [ $# -eq 0 ]; then
        show_usage
        exit 1
    fi

    # Parse command line arguments
    while [ $# -gt 0 ]; do
        case "$1" in
            -s|--start)
                setup_network_rules
                shift
                ;;
            -x|--stop)
                reset_network_rules
                echo -e " \033[93m[!]\033[0m ZeroTrace: Privacy mode \033[91m[INACTIVE]\033[0m"
                log_message "[!] ZeroTrace: Privacy mode deactivated"
                shift
                ;;
            -n|--new-ip)
                change_ip_address
                shift
                ;;
            -i|--ip)
                show_current_ip
                shift
                ;;
            -a|--auto)
                interval=${2:-500}
                if ! [[ "$interval" =~ ^[0-9]+$ ]]; then
                    echo "Error: Interval must be a number"
                    show_usage
                    exit 1
                fi
                echo -e " \033[92m[+]\033[0m ZeroTrace: Auto IP switching enabled. Interval: $interval seconds"
                while true; do
                    change_ip_address
                    echo -e " \033[92m[*]\033[0m ZeroTrace: Successfully changed IP address\n"
                    sleep "$interval"
                done
                # We don't shift 2 here because we're in an infinite loop
                ;;
            -h|--help)
                show_usage
                exit 0
                ;;
            *)
                echo "Unknown option: $1"
                show_usage
                exit 1
                ;;
        esac
    done
}

show_usage() {
    echo "Usage: zerotrace [OPTION]"
    echo
    echo "Options:"
    echo "  -s, --start       Start ZeroTrace (route traffic through Tor)"
    echo "  -x, --stop        Stop ZeroTrace and reset network rules"
    echo "  -n, --new-ip      Get a new IP address through Tor"
    echo "  -i, --ip          Show current public IP address"
    echo "  -a, --auto [SEC]  Automatically change IP at regular intervals (default: 500)"
    echo "  -h, --help        Show this help message"
}


# Register cleanup function
trap cleanup EXIT

# Check if Tor configuration needs to be updated
if [ -f "$TOR_CONFIG" ] && ! grep -q "VirtualAddrNetwork" "$TOR_CONFIG"; then
    echo "$TOR_CONFIG_CONTENT" >> "$TOR_CONFIG"
fi

main "$@"
