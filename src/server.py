import re

import requests
import urllib3
from diskcache import Cache
from flask import Flask, make_response, Response

urllib3.disable_warnings()

_cache: Cache = None
_proxies = None
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


@app.route("/health")
def health():
    return "alive"


@app.route("/cache", methods=["DELETE"])
def clear_cache():
    _cache.clear()
    return Response(status=200)

@app.route("/tiles/akh<path>")
def tiles(path):
    quadkey = re.findall(r"(\d+).jpeg", path)[0]
    tileX, tileY, levelOfDetail = quad_key_to_tileXY(quadkey)

    url = f"https://mt1.google.com/vt/lyrs=s&x={tileX}&y={tileY}&z={levelOfDetail}"

    cache_key = f"{levelOfDetail}{tileX}{tileY}"
    content = _cache.get(cache_key)
    if content is None:
        print("Downloading from:", url, _proxies)
        content = requests.get(
            url, proxies=_proxies, timeout=30).content

        _cache.set(cache_key, content)
    else:
        print("Use cached:", url)

    response = make_response(content)
    headers = {"Content-Type": "image/jpeg", "Last-Modified": "Sat, 24 Oct 2020 06:48:56 GMT", "ETag": "9580",
               "Server": "Microsoft-IIS/10.0", "X-VE-TFE": "BN00004E85", "X-VE-AZTBE": "BN000033DA", "X-VE-AC": "5035",
               "X-VE-ID": "4862_136744347",
               "X-VE-TILEMETA-CaptureDatesRang": "1/1/1999-12/31/2003",
               "X-VE-TILEMETA-CaptureDateMaxYY": "0312",
               "X-VE-TILEMETA-Product-IDs": "209"}
    for k, v in headers.items():
        response.headers[k] = v

    return response


def run_server(cache_size, proxies):
    global _cache, _proxies
    _cache = Cache(
        "./cache", size_limit=int(cache_size) * 1024 * 1024 * 1024, shards=10)
    _proxies = proxies

    app.run(port=8000, host="0.0.0.0", threaded=True)
