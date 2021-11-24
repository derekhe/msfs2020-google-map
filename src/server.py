import math

import io
import re

import requests
import traceback
import urllib3
from PIL import Image, ImageEnhance, ImageStat
from diskcache import Cache
from flask import Flask, make_response, Response, request

urllib3.disable_warnings()

__cache: Cache = None
__proxies = None
__google_server = "mt1.google.com"
__original_ips = None
app = Flask(__name__)


def quad_key_to_tile_xy(quad_key):
    tile_x = tile_y = 0
    level_of_detail = len(quad_key)
    for i in range(level_of_detail, 0, -1):
        mask = 1 << (i - 1)
        t = quad_key[level_of_detail - i]
        if t == '1':
            tile_x |= mask
        if t == '2':
            tile_y |= mask
        if t == '3':
            tile_x |= mask
            tile_y |= mask
    return tile_x, tile_y, level_of_detail


@app.route("/health")
def health():
    return "alive"


@app.route("/cache", methods=["DELETE"])
def clear_cache():
    __cache.clear()
    return Response(status=200)


def calc_brightness(im):
    stat = ImageStat.Stat(im.convert('L'))
    return stat.rms[0]


@app.route('/tiles/mtx<dummy>')
def mtx(dummy=None):
    print("Handing request to", request.url)
    request_header = {}
    for k, v in request.headers:
        request_header[k] = v

    print("Downloading from:", request.url)

    url = request.url.replace(request.host, "kh.ssl.ak.tiles.virtualearth.net.edgekey.net").replace("http://","https://")

    remote_response = requests.get(
        url, proxies=__proxies, timeout=30, verify=False, headers=request_header)

    response = make_response(remote_response.content)
    for k, v in remote_response.headers.items():
        response.headers[k] = v
    return response

def url_mapping(server, tile_x, tile_y, level_of_detail):
    if "mt" in server:
        return f"https://{server}/vt/lyrs=s&x={tile_x}&y={tile_y}&z={level_of_detail}"

    if "khms" in server:
        return f"https://{server}/kh/v=908?x={tile_x}&y={tile_y}&z={level_of_detail}"

@app.route("/tiles/akh<path>")
def tiles(path):
    quadkey = re.findall(r"(\d+).jpeg", path)[0]
    tile_x, tile_y, level_of_detail = quad_key_to_tile_xy(quadkey)

    url = url_mapping(__google_server, tile_x, tile_y, level_of_detail)

    cache_key = f"{level_of_detail}{tile_x}{tile_y}"
    content = __cache.get(cache_key)
    if content is None:
        print("Downloading from:", url, __proxies)
        resp = requests.get(
            url, proxies=__proxies, timeout=30)

        if resp.status_code != 200:
            return Response(status=404)

        content = resp.content
        __cache.set(cache_key, content)
    else:
        print("Use cached:", url)

    try:
        im = Image.open(io.BytesIO(content))

        enhancer = ImageEnhance.Brightness(im)
        im = enhancer.enhance(0.7)
        img_byte_arr = io.BytesIO()
        im.save(img_byte_arr, format='jpeg')
        output = img_byte_arr.getvalue()
    except:
        print("Image adjust failed, use original picture")
        output = content
        traceback.print_exc()

    response = make_response(output)
    headers = {"Content-Type": "image/jpeg", "Last-Modified": "Sat, 24 Oct 2020 06:48:56 GMT", "ETag": "9580",
               "Server": "Microsoft-IIS/10.0", "X-VE-TFE": "BN00004E85", "X-VE-AZTBE": "BN000033DA", "X-VE-AC": "5035",
               "X-VE-ID": "4862_136744347",
               "X-VE-TILEMETA-CaptureDatesRang": "1/1/1999-12/31/2003",
               "X-VE-TILEMETA-CaptureDateMaxYY": "0312",
               "X-VE-TILEMETA-Product-IDs": "209"}
    for k, v in headers.items():
        response.headers[k] = v

    return response


def run_server(cache_size, proxies, google_server, original_ips):
    global __cache, __proxies, __google_server, __original_ips
    __cache = Cache(
        "./cache", size_limit=int(cache_size) * 1024 * 1024 * 1024, shards=10)
    __proxies = {"https": proxies}
    __google_server = google_server
    __original_ips = original_ips

    app.run(port=39871, host="0.0.0.0", threaded=True)
