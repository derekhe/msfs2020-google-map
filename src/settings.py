import os
from configparser import ConfigParser


class Settings:
    def __init__(self):
        self.conf = ConfigParser()
        self.conf.read('config.ini')

    @property
    def proxy_url(self):
        url = self.conf['proxy']['url']
        if len(url) == 0:
            return os.getenv("http_proxy") or ""

        return url

    @proxy_url.setter
    def proxy_url(self, proxy_url):
        if len(proxy_url) == 0:
            self.conf['proxy']['url'] = ""
        else:
            self.conf['proxy']['url'] = proxy_url

    @property
    def cache_size(self):
        return self.conf['offline']['max_cache_size_G']

    @property
    def google_servers(self):
        return ['mt1.google.com', 'mt2.google.com', 'mt3.google.com']

    @property
    def google_server(self):
        return self.conf['google']['server']

    @google_server.setter
    def google_server(self, url):
        self.conf['google']['server'] = url

    def save(self):
        with open('config.ini', 'w') as configfile:
            self.conf.write(configfile)
