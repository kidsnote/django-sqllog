from subprocess import Popen, PIPE

try:
    default_handler = Popen(['pt-fingerprint'], stdin=PIPE, stdout=PIPE)
except FileNotFoundError:
    default_handler = None


def fingerprint(sql, handler=default_handler):
    if not default_handler:
        return
    handler.stdin.write(sql.encode('utf-8'))
    handler.stdin.write(b';\n')
    handler.stdin.flush()
    return handler.stdout.readline().decode('utf-8').strip()
