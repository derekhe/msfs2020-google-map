import io
import itertools
import re
import traceback

import requests
import urllib3
from PIL import Image, ImageEnhance, ImageStat, UnidentifiedImageError
from diskcache import Cache
from flask import Flask, make_response, Response, request

# See coment in tiles() on how this is used to round-robin through all Google Maps servers
from google_servers import GOOGLE_SERVERS
_google_server_loop = itertools.cycle(GOOGLE_SERVERS)

urllib3.disable_warnings()

__cache: Cache
__proxies: None = None
# __google_server: str = "mt1.google.com"

EDGEKEY_NET = "kh.ssl.ak.tiles.virtualearth.net.edgekey.net"
# every bit of optimisation helps: Python isn't known to be a super-fast language
_TENTWENTYFOURCUBED = 1024 * 1024 * 1024

app: Flask = Flask(__name__)


@app.route("/health")
def health() -> str:
    return "alive"


@app.route("/cache", methods=["DELETE"])
def clear_cache() -> Response:
    __cache.clear()
    return Response(status=200)


@app.route('/tiles/mtx<dummy>')
def mtx(dummy: str = None) -> Response:
    print("Handing request to", request.url)
    request_header = {}
    for k, v in request.headers:
        request_header[k] = v

    print("Downloading from:", request.url)

    url = request.url.replace(request.host, EDGEKEY_NET).replace("http://", "https://")

    remote_response = requests.get(
        url, proxies=__proxies, timeout=30, verify=False, headers=request_header)

    response = make_response(remote_response.content)
    for k, v in remote_response.headers.items():
        response.headers[k] = v
    return response


@app.route("/tiles/akh<path>")
def tiles(path: str) -> Response:
    quadkey = re.findall(r"(\d+).jpeg", path)[0]
    tile_x, tile_y, level_of_detail = _quad_key_to_tile_xy(quadkey)

    # url = url_mapping(__google_server, tile_x, tile_y, level_of_detail)
    # There seem to be issues where Google Maps is throttling download attempts from a single IP, especially
    # when it's the first flight and a LOT of queries are fired off to fill the cache.
    # This attempts to round-robin the queries from the entire list of Google Maps servers in the list
    # (replacing the ability to choose one)
    next_server = next(_google_server_loop)
    url = url_mapping(next_server, tile_x, tile_y, level_of_detail)

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

    return image_adjust(content)


def image_adjust(content):
    try:
        im = Image.open(io.BytesIO(content))

        enhancer = ImageEnhance.Brightness(im)
        im = enhancer.enhance(0.7)
        img_byte_arr = io.BytesIO()
        im.save(img_byte_arr, format='jpeg')
        output = img_byte_arr.getvalue()
    except FileNotFoundError or UnidentifiedImageError or ValueError or TypeError:
        print("Image adjust failed, use original picture")
        output = content
        traceback.print_exc()
    response = make_response(output)
    headers = {"Content-Type": "image/jpeg",
               "Last-Modified": "Sat, 24 Oct 2020 06:48:56 GMT",
               "ETag": "9580",
               "Server": "Microsoft-IIS/10.0",
               "X-VE-TFE": "BN00004E85",
               "X-VE-AZTBE": "BN000033DA",
               "X-VE-AC": "5035",
               "X-VE-ID": "4862_136744347",
               "X-VE-TILEMETA-CaptureDatesRang": "1/1/1999-12/31/2003",
               "X-VE-TILEMETA-CaptureDateMaxYY": "0312",
               "X-VE-TILEMETA-Product-IDs": "209"}
    for k, v in headers.items():
        response.headers[k] = v
    return response


def url_mapping(server: str, tile_x: int, tile_y: int, level_of_detail: int) -> str:
    # TODO: check that last character: should it really be '?' in one and '&' in the other case?
    qualifier = "kh/v=908?" if "khms" in server else "vt/lyrs=s&"
    return f"https://{server}/vt/{qualifier}x={tile_x}&y={tile_y}&z={level_of_detail}"


def run_server(cache_size, proxies, google_server) -> None:
    # global __cache, __proxies, __google_server
    global __cache, __proxies
    __cache = Cache("./cache", size_limit=int(cache_size) * _TENTWENTYFOURCUBED, shards=10)
    __proxies = {"https": proxies}
    # __google_server = google_server

    app.run(port=39871, host="0.0.0.0", threaded=True)


def _quad_key_to_tile_xy(quad_key: str) -> tuple[int, int, int]:
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
