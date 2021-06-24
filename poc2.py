import pty, os, select
def waitfor(fd, str):
    poll = select.poll()
    poll.register(fd, select.POLLIN)
    while True:
        evt = poll.poll()
        r = os.read(fd, 1024)
        print(r.decode())
        if str in r:
            return
pid, fd = pty.fork()
# executed in child
if pid == 0:
    os.execvp("pwsh", ["pwsh"])
# executed in parent
elif pid > 0:
    waitfor(fd, b"> ")
