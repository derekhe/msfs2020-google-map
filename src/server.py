import concurrent.futures
import io
import re
import requests
import urllib3
from PIL import Image
from concurrent.futures.thread import ThreadPoolExecutor
from diskcache import Cache
from flask import Flask, make_response, Response

urllib3.disable_warnings()

__cache: Cache = None
__proxies = None
__google_server = "mt1.google.com"
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


def download_image(url):
    print("Downloading", url)
    cached = __cache.get(url)

    if cached is not None:
        content = cached
    else:
        content = requests.get(url, proxies=__proxies, timeout=30).content
        __cache.set(url, content)

    return content


@app.route("/tiles/akh<path>")
def tiles(path):
    quadkey = re.findall(r"(\d+).jpeg", path)[0]
    tile_x, tile_y, level_of_detail = quad_key_to_tile_xy(quadkey)

    url = f"https://{__google_server}/vt/lyrs=s&x={tile_x}&y={tile_y}&z={level_of_detail}"
    print(url)

    next_zoom_level = level_of_detail + 1
    url1 = f"https://{__google_server}/vt/lyrs=s&x={tile_x * 2}&y={tile_y * 2}&z={next_zoom_level}"
    url2 = f"https://{__google_server}/vt/lyrs=s&x={tile_x * 2 + 1}&y={tile_y * 2}&z={next_zoom_level}"
    url3 = f"https://{__google_server}/vt/lyrs=s&x={tile_x * 2}&y={tile_y * 2 + 1}&z={next_zoom_level}"
    url4 = f"https://{__google_server}/vt/lyrs=s&x={tile_x * 2 + 1}&y={tile_y * 2 + 1}&z={next_zoom_level}"

    images = {}
    with ThreadPoolExecutor() as executor:
        future_to_url = {executor.submit(download_image, url): url for url in [url1, url2, url3, url4]}

        for future in concurrent.futures.as_completed(future_to_url):
            url = future_to_url[future]
            try:
                images[url] = Image.open(io.BytesIO(future.result()))
            except Exception as exc:
                print('%r generated an exception: %s' % (url, exc))

    output = Image.new('RGB', (256 * 2, 256 * 2))
    output.paste(images[url1], (0, 0))
    output.paste(images[url2], (256, 0))
    output.paste(images[url3], (0, 256))
    output.paste(images[url4], (256, 256))

    img_byte_arr = io.BytesIO()
    output.save(img_byte_arr, format='jpeg')
    img_byte_arr = img_byte_arr.getvalue()

    response = make_response(img_byte_arr)
    headers = {"Content-Type": "image/jpeg", "Last-Modified": "Sat, 24 Oct 2020 06:48:56 GMT", "ETag": "9580",
               "Server": "Microsoft-IIS/10.0", "X-VE-TFE": "BN00004E85", "X-VE-AZTBE": "BN000033DA", "X-VE-AC": "5035",
               "X-VE-ID": "4862_136744347",
               "X-VE-TILEMETA-CaptureDatesRang": "1/1/1999-12/31/2003",
               "X-VE-TILEMETA-CaptureDateMaxYY": "0312",
               "X-VE-TILEMETA-Product-IDs": "209"}
    for k, v in headers.items():
        response.headers[k] = v

    return response


def run_server(cache_size, proxies, google_server):
    global __cache, __proxies, __google_server
    __cache = Cache(
        "./cache", size_limit=int(cache_size) * 1024 * 1024 * 1024, shards=10)
    __proxies = {"https": proxies}
    __google_server = google_server

    app.run(port=8000, host="0.0.0.0", threaded=True)
