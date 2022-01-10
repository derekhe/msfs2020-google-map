import os
from configparser import ConfigParser


class Settings:
    def __init__(self):
        self.conf = ConfigParser()
        self.conf.read('config.ini')

    @property
    def proxy_url(self) -> str:
        url = self.conf['proxy']['url']
        if len(url) == 0:
            return os.getenv("http_proxy") or ""
        return url

    @proxy_url.setter
    def proxy_url(self, proxy_url: str) -> None:
        if len(proxy_url) == 0:
            self.conf['proxy']['url'] = ""
        else:
            self.conf['proxy']['url'] = proxy_url

    @property
    def google_servers(self) -> list[str]:
        return ['mt.google.com','khm.google.com',"api.mapbox.com","services.arcgisonline.com"]

    @property
    def google_server(self):
        return self.conf['google']['server']

    @google_server.setter
    def google_server(self, url):
        self.conf['google']['server'] = url

    @property
    def google_server(self) -> str:
        return self.conf['google']['server']

    @google_server.setter
    def google_server(self, url: str) -> None:
        self.conf['google']['server'] = url

    @property
    def welcome_page_and_warning_enabled(self) -> str:
        return self.conf['general']['warning']

    @welcome_page_and_warning_enabled.setter
    def welcome_page_and_warning_enabled(self, enabled: str) -> None:
        self.conf['general']['warning'] = enabled

    def save(self) -> None:
        with open('config.ini', 'w') as configfile:
            self.conf.write(configfile)
