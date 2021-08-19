from pygeotile.tile import Tile
from diskcache import Cache
import requests
from configparser import ConfigParser
from retrying import retry
from concurrent.futures.thread import ThreadPoolExecutor
import os

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

proxies = config_proxy()
cache = Cache("./cache", size_limit=int(conf['offline']['max_cache_size_G'])*1024*1024*1024, shards=10)

north_west = [float(i) for i in conf['offline']['north_west'].split(",")]
south_east = [float(i) for i in conf['offline']['south_east'].split(",")]

levels = [int(i) for i in conf['offline']['range'].split(",")]

@retry(stop_max_attempt_number=5)
def download_image(tile_x, tile_y, level_of_detail, i, total):
    print(f"Downloading x: {tile_x} y: {tile_y} zoom: {level_of_detail} total: {total} progress: {int(i/total* 100)}%")
    url = f"https://mt1.google.com/vt/lyrs=s&x={tile_x}&y={tile_y}&z={level_of_detail}"

    cache_key = f"{level_of_detail}{tile_x}{tile_y}"
    content = cache.get(cache_key)
    if content is None:
        print(url)
        content = requests.get(
            url, proxies=proxies, timeout=15).content

        cache.set(cache_key, content)

print(f"Start from {north_west} to {south_east}")
with ThreadPoolExecutor(max_workers=10) as exec:
    for level_of_detail in range(levels[0], levels[1]+1):
        nw_tiles = Tile.for_latitude_longitude(north_west[0], north_west[1], level_of_detail).google
        se_tiles = Tile.for_latitude_longitude(south_east[0], south_east[1], level_of_detail).google

        xrange = range(nw_tiles[0], se_tiles[0])
        yrange = range(nw_tiles[1], se_tiles[1])
        total = len(xrange) * len(yrange)
        i = 0
        for tile_x in xrange:        
            for tile_y in yrange:
                i+=1
                exec.submit(download_image, tile_x, tile_y, level_of_detail, i, total)