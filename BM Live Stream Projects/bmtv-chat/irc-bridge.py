"""
BlackMarker.TV chat  ->  vMix Social (via IRC)

WHAT THIS IS
    vMix Social pulls from Facebook, Twitch, YouTube Live Chat, Bluesky, Zoom
    and IRC. There is no "custom feed" option, but the IRC source takes a plain
    Server / Port / Nickname / Channel, so it will talk to anything that speaks
    IRC. This script is that something: it speaks IRC and relays the site chat,
    so BlackMarker.TV messages land in the SAME vMix Social list as YouTube,
    Facebook and Twitch. One screen, one workflow.

RUNNING IT
    python irc-bridge.py

    In vMix Social add an IRC source:
        Server    127.0.0.1
        Port      6667
        Nickname  vmix          (anything)
        Channel   #bmtv

    Leave the window open while you broadcast. Ctrl-C stops it.
    Every line in and out is printed, so the window is a full transcript.

WHY IT IS BUILT THIS CAREFULLY
    vMix Social's IRC client is written for Twitch, and Twitch IRC uses
    capability negotiation. A client that sends "CAP LS" and never hears back
    will sit waiting and then drop the connection -- which looks exactly like
    "IRC keeps shutting off". So this implements the full registration
    handshake a strict client expects:

        CAP LS / CAP REQ / CAP END      capability negotiation
        001-004                          welcome block
        005                              ISUPPORT
        375 / 372 / 376                  MOTD, including the terminator that
                                         many clients wait for before joining
        PING every 45s                   so the client does not consider the
                                         link dead
        JOIN announced per author        clients ignore messages from users
                                         they were never told are present
"""

import json
import re
import socket
import sys
import threading
import time
import urllib.request

# --------------------------------------------------------------------------
SUPABASE_URL = 'https://eyqtvdwchwfomhkfjimv.supabase.co'
SUPABASE_ANON = (
    'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6'
    'ImV5cXR2ZHdjaHdmb21oa2ZqaW12Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODY4MTgyNzEs'
    'ImV4cCI6MjEwMjM5NDI3MX0.8J_Mi9sOt4-BP8NOF2NHkkPcHnN4fXL8p0bUzbn8qu0'
)

HOST = '127.0.0.1'      # '0.0.0.0' if vMix runs on another machine
PORT = 6667
CHANNEL = '#bmtv'
POLL_SECONDS = 1.5
BACKFILL = 15
WIRE_LOG = True         # print every protocol line, in and out
# --------------------------------------------------------------------------

clients = []
clients_lock = threading.Lock()
last_id = 0


def log(msg):
    sys.stdout.write(msg + '\n')
    sys.stdout.flush()


class Client(object):
    def __init__(self, sock, addr):
        self.sock = sock
        self.addr = addr
        self.nick = 'vmix'
        self.nicks = set()
        self.registered = False
        self.joined = False
        self.cap_pending = False    # client asked for CAP and hasn't sent CAP END
        self.alive = True

    def raw(self, line):
        if not self.alive:
            return False
        try:
            self.sock.sendall((line + '\r\n').encode('utf-8', 'replace'))
            if WIRE_LOG:
                log('    >> ' + line)
            return True
        except Exception:
            self.alive = False
            return False

    def say(self, nick, text):
        if nick not in self.nicks:
            if not self.raw(':%s!%s@bmtv JOIN %s' % (nick, nick, CHANNEL)):
                return False
            self.nicks.add(nick)
        return self.raw(':%s!%s@bmtv PRIVMSG %s :%s' % (nick, nick, CHANNEL, text))


def irc_nick(name):
    n = re.sub(r'[^A-Za-z0-9_\[\]{}\\`|-]', '_', (name or '').strip())
    n = re.sub(r'_+', '_', n).strip('_')
    if not n or n[0].isdigit():
        n = 'v' + n
    return n[:28] or 'guest'


def one_line(t):
    return re.sub(r'[\r\n]+', ' ', t or '').strip()


def _get(path):
    req = urllib.request.Request(SUPABASE_URL + path)
    req.add_header('apikey', SUPABASE_ANON)
    req.add_header('Authorization', 'Bearer ' + SUPABASE_ANON)
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read().decode())


def fetch_after(i):
    return _get('/rest/v1/messages?select=id,display_name,body&status=neq.hidden'
                '&id=gt.%d&order=id.asc&limit=100' % i)


def fetch_recent(n):
    return list(reversed(_get(
        '/rest/v1/messages?select=id,display_name,body&status=neq.hidden'
        '&order=id.desc&limit=%d' % n)))


def broadcast(nick, text):
    with clients_lock:
        for c in list(clients):
            if not c.say(nick, text):
                clients.remove(c)


# --------------------------------------------------------------------------
def register(c):
    """The full welcome a strict client waits for before it will JOIN."""
    if c.registered:
        return
    c.registered = True
    n = c.nick
    c.raw(':bmtv 001 %s :Welcome to the BlackMarker.TV chat relay' % n)
    c.raw(':bmtv 002 %s :Your host is bmtv-bridge, running version 1.0' % n)
    c.raw(':bmtv 003 %s :This server relays the BlackMarker.TV site chat' % n)
    c.raw(':bmtv 004 %s bmtv 1.0 o o' % n)
    c.raw(':bmtv 005 %s CHANTYPES=# NETWORK=BlackMarkerTV NICKLEN=30 '
          'CASEMAPPING=rfc1459 :are supported by this server' % n)
    # MOTD -- 376 is the line many clients treat as "registration finished"
    c.raw(':bmtv 375 %s :- bmtv Message of the Day -' % n)
    c.raw(':bmtv 372 %s :- BlackMarker.TV site chat relay for vMix Social' % n)
    c.raw(':bmtv 376 %s :End of /MOTD command.' % n)


def do_join(c, chan):
    if c.joined:
        return
    c.joined = True
    c.raw(':%s!%s@bmtv JOIN %s' % (c.nick, c.nick, CHANNEL))
    c.raw(':bmtv 332 %s %s :BlackMarker.TV live chat' % (c.nick, CHANNEL))
    c.raw(':bmtv 333 %s %s bmtv %d' % (c.nick, CHANNEL, int(time.time())))
    c.raw(':bmtv 353 %s = %s :@%s' % (c.nick, CHANNEL, c.nick))
    c.raw(':bmtv 366 %s %s :End of /NAMES list.' % (c.nick, CHANNEL))
    with clients_lock:
        clients.append(c)
    log('  >>> vMix joined %s -- now relaying <<<' % CHANNEL)
    try:
        rows = fetch_recent(BACKFILL)
        for m in rows:
            t = one_line(m['body'])
            if t:
                c.say(irc_nick(m['display_name']), t)
        log('  replayed %d recent message(s)' % len(rows))
    except Exception as e:
        log('  [warn] could not replay history: %s' % e)


def handle_client(sock, addr):
    c = Client(sock, addr)
    sock.settimeout(45)
    buf = ''
    log('')
    log('  === vMix connected from %s:%s ===' % addr)

    def keepalive():
        while c.alive:
            time.sleep(45)
            if c.alive:
                c.raw('PING :bmtv')
    threading.Thread(target=keepalive, daemon=True).start()

    try:
        while c.alive:
            try:
                data = sock.recv(4096)
            except socket.timeout:
                continue
            except Exception:
                break
            if not data:
                log('  vMix closed the connection')
                break
            buf += data.decode('utf-8', 'replace')

            while '\n' in buf:
                raw_line, buf = buf.split('\n', 1)
                line = raw_line.strip()
                if not line:
                    continue
                if WIRE_LOG:
                    log('    << ' + line)

                parts = line.split(' ')
                cmd = parts[0].upper()
                args = parts[1:]

                if cmd == 'CAP':
                    sub = (args[0].upper() if args else '')
                    if sub == 'LS':
                        c.cap_pending = True
                        c.raw(':bmtv CAP * LS :')          # we offer nothing
                    elif sub == 'REQ':
                        want = line.split(':', 1)[1] if ':' in line else ''
                        c.raw(':bmtv CAP * NAK :' + want)  # politely decline
                    elif sub == 'END':
                        c.cap_pending = False
                        register(c)
                    elif sub == 'LIST':
                        c.raw(':bmtv CAP * LIST :')

                elif cmd == 'NICK' and args:
                    c.nick = args[0].lstrip(':')

                elif cmd == 'USER':
                    if not c.cap_pending:
                        register(c)

                elif cmd == 'PING':
                    c.raw('PONG bmtv :' + (args[0].lstrip(':') if args else 'bmtv'))

                elif cmd == 'PONG':
                    pass

                elif cmd == 'JOIN':
                    if not c.registered:
                        register(c)
                    do_join(c, args[0] if args else CHANNEL)

                elif cmd == 'QUIT':
                    c.alive = False

                elif cmd in ('MODE', 'WHO', 'WHOIS', 'USERHOST', 'LIST'):
                    # answer harmlessly so nothing is left waiting on a reply
                    if cmd == 'MODE' and args:
                        c.raw(':bmtv 324 %s %s +nt' % (c.nick, args[0]))
                    elif cmd == 'WHO' and args:
                        c.raw(':bmtv 315 %s %s :End of /WHO list.' % (c.nick, args[0]))
                    elif cmd == 'LIST':
                        c.raw(':bmtv 323 %s :End of /LIST' % c.nick)
    except Exception as e:
        log('  [client error] %s' % e)
    finally:
        c.alive = False
        with clients_lock:
            if c in clients:
                clients.remove(c)
        try:
            sock.close()
        except Exception:
            pass
        log('  === vMix disconnected ===')


def poller():
    global last_id
    try:
        rows = _get('/rest/v1/messages?select=id&status=neq.hidden&order=id.desc&limit=1')
        last_id = rows[0]['id'] if rows else 0
    except Exception:
        last_id = 0
    log('  watching the site chat (live from message id %d)' % last_id)
    misses = 0
    while True:
        try:
            for m in fetch_after(last_id):
                last_id = max(last_id, m['id'])
                nick, text = irc_nick(m['display_name']), one_line(m['body'])
                if text:
                    log('  NEW MESSAGE  <%s> %s' % (nick, text[:70]))
                    broadcast(nick, text)
            misses = 0
        except Exception as e:
            misses += 1
            if misses in (1, 5, 20):
                log('  [warn] could not reach Supabase: %s' % e)
        time.sleep(POLL_SECONDS)


def main():
    log('')
    log('BlackMarker.TV  ->  vMix Social bridge')
    log('=' * 56)
    log('  vMix Social -> add IRC source:')
    log('      Server    %s' % ("this machine's LAN IP" if HOST == '0.0.0.0' else HOST))
    log('      Port      %d' % PORT)
    log('      Nickname  vmix')
    log('      Channel   %s' % CHANNEL)
    log('=' * 56)

    threading.Thread(target=poller, daemon=True).start()

    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        srv.bind((HOST, PORT))
    except OSError as e:
        log('  [error] cannot listen on %s:%d -- %s' % (HOST, PORT, e))
        return
    srv.listen(5)
    log('  listening on %s:%d -- leave this window open' % (HOST, PORT))

    try:
        while True:
            sock, addr = srv.accept()
            threading.Thread(target=handle_client, args=(sock, addr), daemon=True).start()
    except KeyboardInterrupt:
        log('\n  stopped.')
    finally:
        srv.close()


if __name__ == '__main__':
    main()
