import urllib2, sys, base64, tempfile, subprocess, time

OPENVPN_PATH = "/Applications/Tunnelblick.app/Contents/Resources/openvpn/default"
VPNGATE_API_URL = "http://www.vpngate.net/api/iphone/"
DEFAULT_COUNTRY = "UA"
DEFAULT_SERVER = 0
YES = False

def getServers():
    servers = []
    server_strings = urllib2.urlopen(VPNGATE_API_URL).read()
    for server_string in server_strings.replace("\r", "").split('\n')[2:-2]:
        (HostName, IP, Score, Ping, Speed, CountryLong, CountryShort, NumVpnSessions, Uptime, TotalUsers, TotalTraffic, LogType, Operator, Message, OpenVPN_ConfigData_Base64) = server_string.split(',')
        server = {
            'HostName': HostName,
            'IP': IP,
            'Score': Score,
            'Ping': Ping,
            'Speed': Speed,
            'CountryLong': CountryLong,
            'CountryShort': CountryShort,
            'NumVpnSessions': NumVpnSessions,
            'Uptime': Uptime,
            'TotalUsers': TotalUsers,
            'TotalTraffic': TotalTraffic,
            'LogType': LogType,
            'Operator': Operator,
            'Message': Message,
            'OpenVPN_ConfigData_Base64': OpenVPN_ConfigData_Base64
        }
        servers.append(server)
    return servers

def getCountries(server):
    return set((server['CountryShort'], server['CountryLong']) for server in servers)

def printCountries(countries):
    print("    Connectable countries:")
    newline = False
    for country in countries:
        print("    %-2s) %-25s" % (country[0], country[1])),
        if newline:
            print('\n'),
        newline = not newline
    if newline:
        print('\n'),

def printServers(servers):
    print("  Connectable Servers:")
    for i in xrange(len(servers)):
        server = servers[i]
        print("    %2d) %-15s [%6.2f Mbps, ping:%3s ms]" % (i, server['IP'], float(server['Speed'])/10**6, server['Ping']))

def selectCountry(countries):
    selected = ""
    default_country = DEFAULT_COUNTRY
    short_countries = list(country[0] for country in countries)
    if not default_country in short_countries:
        default_country = short_countries[0]
    if YES:
        selected = default_country
    while not selected:
        try:
            selected = raw_input("[?] Select server's country to connect [%s]: " % (default_country, )).strip().upper()
        except:
            print("[!] Please enter short name of the country.")
            selected = ""
        if selected == "":
            selected = default_country
        elif not selected in short_countries:
            print("[!] Please enter short name of the country.")
            selected = ""
    return selected

def selectServer(servers):
    selected = -1
    default_server = DEFAULT_SERVER
    if YES:
        selected = default_server
    while selected == -1:
        try:
            selected = raw_input("[?] Select server's number to connect [%d]: " % (default_server, )).strip()
        except:
            print("[!] Please enter vaild server's number.")
            selected = -1
        if selected == "":
            selected = default_server
        elif not selected.isdigit() or int(selected) >= len(servers):
            print("[!] Please enter vaild server's number.")
            selected = -1
    return servers[int(selected)]

def saveOvpn(server):
    _, ovpn_path = tempfile.mkstemp()
    ovpn = open(ovpn_path, 'w')
    ovpn.write(base64.b64decode(server["OpenVPN_ConfigData_Base64"]))
    ovpn.close()
    return ovpn_path

def connect(ovpn_path):
    openvpn_process = subprocess.Popen(['sudo', OPENVPN_PATH, '--config', ovpn_path])
    try:
        while True:
            time.sleep(600)
    # termination with Ctrl+C
    except:
        try:
            openvpn_process.kill()
        except:
            pass
        while openvpn_process.poll() != 0:
            time.sleep(1)
        print("[=] Disconnected OpenVPN.")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "-y":
        YES = True

    servers = []
    try:
        print("[-] Trying to get server's informations...")
        servers = sorted(getServers(), key=lambda server: int(server["Score"]), reverse=True)
    except:
        print("[!] Failed to get server's informations from vpngate.")
        sys.exit(1)

    if not servers:
        print("[!] There is no running server on vpngate.")
        sys.exit(1)

    print("[-] Got server's informations.")

    countries = sorted(getCountries(servers))
    printCountries(countries)
    selected_country = selectCountry(countries)

    print("[-] Gethering %s servers..." % (selected_country, ))

    selected_servers = [server for server in servers if server['CountryShort'] == selected_country]
    printServers(selected_servers)
    selected_server = selectServer(selected_servers)

    print("[-] Generating .ovpn file of %s..." % (selected_server["IP"], ))

    ovpn_path = saveOvpn(selected_server)

    print("[-] Connecting to %s..." % (selected_server["IP"], ))

    connect(ovpn_path)
