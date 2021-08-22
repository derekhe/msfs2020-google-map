import urllib3
urllib3.disable_warnings()

from flask import Flask, make_response
import re
import os
import subprocess
import requests
from flask import request
from configparser import ConfigParser
from python_hosts import Hosts, HostsEntry
import ctypes
import sys
import webbrowser
from diskcache import Cache
import atexit
import dns.resolver

def run_as_admin():
    def is_admin():
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except:
            return False

    if not is_admin():
        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, __file__, None, 1)


def add_cert():
    print("Adding certificate to root")
    subprocess.run(["certutil", "-addstore", "-f", "root",
                    ".\certs\cert.crt"], shell=True, check=True)
    print("Successfully added certificate to root")

my_hosts = Hosts()
domains = ['kh.ssl.ak.tiles.virtualearth.net', 'khstorelive.azureedge.net']

origin_ips = {}
dns_resolver = dns.resolver.Resolver()
dns_resolver.nameservers = ['8.8.8.8']
for d in domains:    
    origin_ips[d] = dns_resolver.query(d)[0].to_text()

def override_hosts():
    print("Overriding hosts")
    for domain in domains:
        my_hosts.remove_all_matching(name=domain)
        new_entry = HostsEntry(
            entry_type='ipv4', address='127.0.0.1', names=[domain])
        my_hosts.add([new_entry])
    my_hosts.write()
    print("Done override hosts")

def restore_hosts():
    print("Restoring hosts")
    for domain in domains:
        my_hosts.remove_all_matching(name=domain)
    my_hosts.write()

atexit.register(restore_hosts)

conf = ConfigParser()
conf.read('config.ini')

def config_proxy():
    proxy_url = None
    if conf['proxy']:
        proxy_url = conf['proxy']['url']

    if proxy_url is None:
        proxy_url = os.getenv("http_proxy")

    print("Proxy url is", proxy_url)

    return {"https": proxy_url} if proxy_url is not None else None


run_as_admin()
add_cert()
override_hosts()

cache = Cache("./cache", size_limit=int(conf['offline']['max_cache_size_G'])*1024*1024*1024, shards=10)
proxies = config_proxy()
app = Flask(__name__)


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


@app.route("/tiles/akh<path>")
def tiles(path):
    quadkey = re.findall(r"(\d+).jpeg", path)[0]
    tileX, tileY, levelOfDetail = quad_key_to_tileXY(quadkey)

    url = f"https://mt1.google.com/vt/lyrs=s&x={tileX}&y={tileY}&z={levelOfDetail}"
    
    cache_key = f"{levelOfDetail}{tileX}{tileY}"
    content = cache.get(cache_key)
    if content is None:
        print("Downloading from:", url)
        content = requests.get(
            url, proxies=proxies, timeout=30).content

        cache.set(cache_key, content)
    else:
        print("Use cached:", url)

    response = make_response(content)
    headers = {"Content-Type": "image/jpeg", "Last-Modified": "Sat, 24 Oct 2020 06:48:56 GMT", "ETag": "9580", "Server": "Microsoft-IIS/10.0", "X-VE-TFE": "BN00004E85", "X-VE-AZTBE": "BN000033DA", "X-VE-AC": "5035", "X-VE-ID": "4862_136744347",
               "X-VE-TILEMETA-CaptureDatesRang": "1/1/1999-12/31/2003",
               "X-VE-TILEMETA-CaptureDateMaxYY": "0312",
               "X-VE-TILEMETA-Product-IDs": "209"}
    for k, v in headers.items():
        response.headers[k] = v

    return response


@app.route('/')
@app.route('/<path:dummy>')
def fallback(dummy=None):
    print("Handing request to", request.url)

    disabled_links = [
         #'tsom_cc_activation_masks',
         'coverage_maps', 
         'texture_synthesis_online_map_high_res',
         'color_corrected_images'
          ]

    for disabled_link in disabled_links:
        if disabled_link in request.url:
            print("Skipped", request.url)
            return make_response("", 404)

    request_header = {}

    for k,v in request.headers:
        request_header[k] = v

    if request.host in origin_ips.keys():
        request.url = request.url.replace(request.host, origin_ips[request.host])
        

    print("Downloading from:", request.url)

    remote_response = requests.get(
        request.url, proxies=proxies, timeout=30, verify=False, headers = request_header )

    response = make_response(remote_response.content)
    for k,v in remote_response.headers.items():
        response.headers[k]=v
    return response

if __name__ == "__main__":
    webbrowser.open("https://github.com/derekhe/msfs2020-google-map/releases")
    app.run(ssl_context=('certs/cert.pem', 'certs/key.pem'),
            port=443, host="0.0.0.0", threaded=True)