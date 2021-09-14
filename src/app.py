import time
from tkinter import *
from tkinter import ttk
from tkinter import messagebox
import ctypes
import requests
from configparser import ConfigParser
import os
import subprocess

from runner import add_cert, override_hosts, restore_hosts
from server import run_server
from multiprocessing import Process


class MSFS2020:

    def __init__(self, root):
        root.title("MSFS 2020 Google Map")

        mainframe = ttk.Frame(root, padding="3 3 12 12")
        mainframe.grid(column=0, row=0, sticky=(N, W, E, S))

        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)

        self.proxy_address = StringVar()
        feet_entry = ttk.Entry(mainframe, width=20,
                               textvariable=self.proxy_address)
        feet_entry.grid(column=2, row=2, sticky=(W, E))

        ttk.Label(mainframe,
                  text="Proxy format: http://ip or socks5h://ip\nleave blank if no proxy is needed to access google").grid(
            column=1, row=1, sticky=(W), columnspan=2)
        ttk.Label(mainframe, text="Proxy").grid(column=1, row=2, sticky=(W, E))
        ttk.Button(mainframe, text="Test Connection",
                   command=self.test_proxy).grid(column=3, row=2, sticky=W)

        self.status = StringVar(value="Not running")
        ttk.Label(mainframe, textvariable=self.status).grid(column=1, row=3)

        ttk.Button(mainframe, text="Run", command=self.run
                   ).grid(column=2, row=3)

        ttk.Button(mainframe, text="Stop", command=self.stop
                   ).grid(column=3, row=3)

        for child in mainframe.winfo_children():
            child.grid_configure(padx=5, pady=5)

        if not self.is_admin():
            messagebox.showerror(
                message='Please run in Administrator mode, application will close')
            root.destory()

        root.protocol("WM_DELETE_WINDOW", self.quit)

        self.root = root
        self.conf = ConfigParser()
        self.conf.read('config.ini')
        self.proxy = self.read_proxy_setting()
        self.cache_size = self.conf['offline']['max_cache_size_G']
        self.server_process = None
        self.nginx_process = None

    def read_proxy_setting(self):
        proxy_url = None
        if self.conf['proxy']:
            proxy_url = self.conf['proxy']['url']
            self.proxy_address.set(proxy_url)

        if proxy_url is None:
            proxy_url = os.getenv("http_proxy")

        return {"https": proxy_url} if proxy_url is not None else None

    @staticmethod
    def is_admin():
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except:
            return False

    def test_proxy(self):
        try:
            proxy = self.proxy_address.get()
            if proxy is None or len(proxy) == 0:
                proxies = None
            else:
                proxies = {"https": self.proxy_address.get()}

            response = requests.get(
                "https://mt1.google.com/vt/lyrs=s&x=1&y=1&z=1", timeout=3, proxies=proxies)
            if response.status_code == 200:
                messagebox.showinfo(message='Proxy is good')
            else:
                messagebox.showerror(message='Connection failed, please check')
        except:
            messagebox.showerror(message='Connection failed, please check')

    def run(self):
        self.save_setting()
        self.stop()
        try:
            add_cert()
        except:
            messagebox.showerror(message="Add certificate failed")

        try:
            override_hosts()
        except:
            messagebox.showerror(message="Override hosts failed")

        try:
            self.server_process = Process(
                target=run_server, args=(self.cache_size, self.proxy))
            self.server_process.start()
            self.nginx_process = subprocess.Popen(
                "nginx.exe", shell=True, cwd="./nginx")
        except:
            messagebox.showerror(message="Unable to start")
        self.status.set("Running")

    def stop(self):
        if self.server_process is not None:
            self.server_process.kill()

        if self.nginx_process is not None:
            subprocess.run("nginx.exe -s quit", shell=True, check=True, cwd="./nginx")
            self.nginx_process.wait(1)
            self.nginx_process = None

        self.status.set("Stopped")

    def save_setting(self):
        with open('config.ini', 'w') as configfile:
            self.conf.write(configfile)

    def quit(self):
        try:
            self.save_setting()
            self.stop()
            restore_hosts()
        finally:
            self.root.destroy()


if __name__ == '__main__':
    root = Tk()
    MSFS2020(root)
    root.mainloop()
