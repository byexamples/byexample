import pexpect
cmd = '''/usr/bin/env pwsh -NoProfile -NoExit -Command 'Remove-Module psreadline ; function prompt { "XXXXXXXXXXXXXXXX " }' '''
#cmd = '''pwsh -NoProfile -NoExit '''

cmd = '''python'''
#cmd = '''bash -c 'pwsh -NoProfile -NoExit -Command "Remove-Module psreadline" ' '''
#cmd = '''stty --all'''

s = pexpect.spawn(cmd, use_poll=True, echo=False)
#s.expect("PS", timeout=20)
#s.expect(">>>", timeout=20)

#import time
#time.sleep(5)

for i in range(5):
    print(s.read_nonblocking(1024, timeout=20))
    print("------")

s.sendline("81 * 81")

for i in range(50):
    print(s.read_nonblocking(1024, timeout=20))
    print("------")

