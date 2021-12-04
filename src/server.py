import PIL
import io
import re
import requests
import traceback
import urllib3
from PIL import Image, ImageEnhance
from flask import Flask, make_response, Response, request

urllib3.disable_warnings()

__proxies: None = None
__google_server: str = "mt1.google.com"
app: Flask = Flask(__name__)


def quad_key_to_tile_xy(quad_key: str) -> tuple[int, int, int]:
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
def health() -> str:
    return "alive"


@app.route('/tiles/mtx<dummy>')
def mtx(dummy: str = None) -> Response:
    print("Handing request to", request.url)
    request_header = {}
    for k, v in request.headers:
        request_header[k] = v

    print("Downloading from:", request.url)

    url = request.url.replace(request.host, "kh.ssl.ak.tiles.virtualearth.net.edgekey.net").replace("http://",
                                                                                                    "https://")

    remote_response = requests.get(
        url, proxies=__proxies, timeout=30, verify=False, headers=request_header)

    response = make_response(remote_response.content)
    for k, v in remote_response.headers.items():
        response.headers[k] = v
    return response


def url_mapping(server: str, tile_x: int, tile_y: int, level_of_detail: int) -> str:
    if "mt" in server:
        return f"https://{server}/vt/lyrs=s&x={tile_x}&y={tile_y}&z={level_of_detail}"

    if "khm" in server:
        return f"https://{server}/kh/v=908?x={tile_x}&y={tile_y}&z={level_of_detail}"


@app.route("/tiles/akh<path>")
def tiles(path: str) -> Response:
    quadkey = re.findall(r"(\d+).jpeg", path)[0]
    tile_x, tile_y, level_of_detail = quad_key_to_tile_xy(quadkey)

    url = url_mapping(__google_server, tile_x, tile_y, level_of_detail)

    print("Downloading from:", url, __proxies)
    resp = requests.get(
        url, proxies=__proxies, timeout=30)

    if resp.status_code != 200:
        return Response(status=404)

    content = resp.content

    try:
        im = Image.open(io.BytesIO(content))

        enhancer = ImageEnhance.Brightness(im)
        im = enhancer.enhance(0.7)
        img_byte_arr = io.BytesIO()
        im.save(img_byte_arr, format='jpeg')
        output = img_byte_arr.getvalue()
    except FileNotFoundError or PIL.UnidentifiedImageError or ValueError or TypeError:
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


def run_server(proxies, google_server) -> None:
    global __proxies, __google_server
    __proxies = {"https": proxies}
    __google_server = google_server

    app.run(port=39871, host="0.0.0.0", threaded=True)
