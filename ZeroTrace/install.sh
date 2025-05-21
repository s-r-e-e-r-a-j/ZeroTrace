#!/usr/bin/env bash

if [ -z "$BASH_VERSION" ]; then
    printf "\e[31m[!]\e[0m Error: This script must be run with Bash.\n"
    exit 1
fi

# Require root
if [[ "$EUID" -ne 0 ]]; then
    echo -e "\e[31m[!]\e[0m Please run this script as root."
    exit 1
fi

read -p "[+] To install press (Y) | To uninstall press (N) >> " choice
choice=$(echo "$choice" | tr '[:upper:]' '[:lower:]')

if [[ "$choice" == "y" ]]; then
    chmod 755 zerotrace.sh
    mkdir -p /usr/share/zerotrace
    cp zerotrace.sh /usr/share/zerotrace/zerotrace.sh

    # Shell wrapper
    echo -e "#!/usr/bin/env bash\nexec /usr/share/zerotrace/zerotrace.sh \"\$@\"" > /usr/bin/zerotrace

    chmod +x /usr/bin/zerotrace
    chmod +x /usr/share/zerotrace/zerotrace.sh

    echo -e "\n\n[✔] ZeroTrace installed successfully!"
    echo -e "[→] Now you can run it by typing: \e[6;30;42mzerotrace\e[0m\n"

elif [[ "$choice" == "n" ]]; then
    rm -rf /usr/share/zerotrace
    rm -f /usr/bin/zerotrace
    echo "[✔] ZeroTrace has been removed successfully."

else
    echo "[!] Invalid choice. Please enter Y or N."
fi
