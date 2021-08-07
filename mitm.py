import requests
from mitmproxy import http
import re
from mitmproxy.script import concurrent
import os

proxy_url = None

# 将下面这个地址换成你的代理地址，如果不需要代理的话，直接删除这一行
# Change below url to your proxy, if you don't need the proxy, delete below line
proxy_url = "http://192.168.3.191:8118"

proxies = {"https": proxy_url} if proxy_url is not None else None
regex = r"/tiles/akh(\d+).jpeg"


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


@concurrent
def request(flow: http.HTTPFlow) -> None:
    if ("tsom_cc_activation_masks" in flow.request.path) or ("texture_synthesis_online_map_high_res" in flow.request.path) or ("color_corrected_images" in flow.request.path):
        flow.response = http.Response.make(404)
        return

    if (flow.request.pretty_host == "kh.ssl.ak.tiles.virtualearth.net") and ("/tiles/akh" in flow.request.path):
        # print(flow.request.path)
        quadkey = re.findall(regex, flow.request.path)[0]
        tileX, tileY, levelOfDetail = quad_key_to_tileXY(quadkey)

        dir = f"./cache/{tileX}/{tileY}"
        os.makedirs(dir, exist_ok=True)

        cache_file = f"{dir}/{levelOfDetail}.jpeg"

        url = f"https://khms0.google.com/kh/v=908?x={tileX}&y={tileY}&z={levelOfDetail}"

        if os.path.exists(cache_file):
            with open(cache_file, "rb") as f:
                content = f.read()
        else:
            # print(url)
            content = requests.get(
                url, proxies=proxies, timeout=5).content

            with open(cache_file, "wb") as f:
                f.write(content)

        flow.response = http.Response.make(200, content,
                                           {"Content-Type": "image/jpeg",
                                            "Last-Modified": "Sat, 24 Oct 2020 06:48:56 GMT",
                                            "ETag": "9580",
                                            "Server": "Microsoft-IIS/10.0",
                                            "X-VE-TFE": "BN00004E85",
                                            "X-VE-AZTBE": "BN000033DA",
                                            "X-VE-AC": "5035",
                                            "X-VE-ID": "4862_136744347",
                                            "X-VE-TILEMETA-CaptureDatesRang": "1/1/1999-12/31/2003",
                                            "X-VE-TILEMETA-CaptureDateMaxYY": "0312",
                                            "X-VE-TILEMETA-Product-IDs": "209"
                                            }
                                           )
