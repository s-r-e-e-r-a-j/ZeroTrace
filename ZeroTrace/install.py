import os
choice = input('[+] to install press (Y) to uninstall press (N) >> ')
run = os.system
if str(choice) =='Y' or str(choice)=='y':

    run('chmod 777 zerotrace.py')
    run('mkdir /usr/share/zerotrace')
    run('cp zerotrace.py /usr/share/zerotrace/zerotrace.py')

    cmnd=(' #! /bin/sh \n exec python3 /usr/share/zerotrace/zerotrace.py "$@"')
    with open('/usr/bin/zerotrace','w')as file:
        file.write(cmnd)
    run('chmod +x /usr/bin/zerotrace & chmod +x /usr/share/zerotrace/zerotrace.py')
    print('''\n\ncongratulation ZeroTrace is installed successfully \nfrom now just type \x1b[6;30;42mzerotrace\x1b[0m in terminal ''')
if str(choice)=='N' or str(choice)=='n':
    run('rm -r /usr/share/zerotrace ')
    run('rm /usr/bin/zerotrace ')
    print('[!] now ZeroTrace  has been removed successfully')
