import os
import sys

# Require root
if os.geteuid() != 0:
    print("[!] Please run this script as root.")
    sys.exit(1)

choice = input('[+] To install press (Y) | To uninstall press (N) >> ').strip().lower()
run = os.system

if choice == 'y':
    run('chmod 755 zerotrace.py')
    run('mkdir -p /usr/share/zerotrace')
    run('cp zerotrace.py /usr/share/zerotrace/zerotrace.py')

    # Shell wrapper to call the script
    cmnd = '#!/bin/sh\nexec python3 /usr/share/zerotrace/zerotrace.py "$@"\n'
    with open('/usr/bin/zerotrace', 'w') as file:
        file.write(cmnd)

    run('chmod +x /usr/bin/zerotrace')
    run('chmod +x /usr/share/zerotrace/zerotrace.py')

    print('''\n\n[✔] ZeroTrace installed successfully!
[→] Now you can run it by typing: \x1b[6;30;42mzerotrace\x1b[0m\n''')

elif choice == 'n':
    run('rm -rf /usr/share/zerotrace')
    run('rm -f /usr/bin/zerotrace')
    print('[✔] ZeroTrace has been removed successfully.')
else:
    print('[!] Invalid choice. Please enter Y or N.')
