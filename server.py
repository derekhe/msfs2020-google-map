from flask import Flask, make_response
import re
import os
import subprocess
import requests
from flask import request
from configparser import ConfigParser
from python_hosts import Hosts, HostsEntry
import ctypes, sys
import webbrowser
from diskcache import Cache

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

if not is_admin():
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, __file__, None, 1)

subprocess.run(["certutil", "-addstore","-f", "root", ".\certs\cert.crt"], shell=True, check=True)

my_hosts = Hosts()
domains = ['kh.ssl.ak.tiles.virtualearth.net', 'khstorelive.azureedge.net']
for domain in domains:
    my_hosts.remove_all_matching(name=domain)
    new_entry = HostsEntry(entry_type='ipv4', address='127.0.0.1', names=[domain])
    my_hosts.add([new_entry])
my_hosts.write()

cache = Cache("./cache", size_limit=10*1024*1024*1024, shards=10)
app = Flask(__name__)
conf = ConfigParser()
conf.read('config.ini')

proxy_url = conf['proxy']['url']
print("Proxy url", proxy_url)

proxies = {"https": proxy_url} if proxy_url is not None else None
regex = r"akh(\d+).jpeg"

def quad_key_to_tileXY(quadKey):
    tileX = tileY = 0
    levelOfDetail = len(quadKey)
    for i in range(levelOfDetail, 0, -1):
        mask = 1 << (i - 1)
        t = quadKey[levelOfDetail - i]
        if t == '1':
            tileX |= mask
        if t == '2':
            tileY |= mask
        if t == '3':
            tileX |= mask
            tileY |= mask
    return tileX, tileY, levelOfDetail


@app.route("/tiles/<path>")
def tiles(path):
    if "akh" not in path:
        content = requests.get(
            request.url, proxies=proxies, timeout=30).content
        return content

    quadkey = re.findall(regex, path)[0]
    tileX, tileY, levelOfDetail = quad_key_to_tileXY(quadkey)

    url = f"https://mt1.google.com/vt/lyrs=s&x={tileX}&y={tileY}&z={levelOfDetail}"

    content = cache.get(path)
    if content is None:
        print(url)
        content = requests.get(
            url, proxies=proxies, timeout=15).content
        
        cache.set(path, content)

    response = make_response(content)
    headers = {"Content-Type": "image/jpeg", "Last-Modified": "Sat, 24 Oct 2020 06:48:56 GMT", "ETag": "9580", "Server": "Microsoft-IIS/10.0", "X-VE-TFE": "BN00004E85", "X-VE-AZTBE": "BN000033DA", "X-VE-AC": "5035", "X-VE-ID": "4862_136744347",
               "X-VE-TILEMETA-CaptureDatesRang": "1/1/1999-12/31/2003",
               "X-VE-TILEMETA-CaptureDateMaxYY": "0312",
               "X-VE-TILEMETA-Product-IDs": "209"}
    for k, v in headers.items():
        response.headers[k] = v

    return response


if __name__ == "__main__":
    webbrowser.open("https://github.com/derekhe/msfs2020-google-map")
    app.run(ssl_context=('certs/cert.pem', 'certs/key.pem'),
            port=443, host="0.0.0.0", threaded=True)
