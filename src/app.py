import time

import os.path
import socket
import ctypes
import requests
import subprocess
import traceback
import webbrowser
from diskcache import Cache
from multiprocessing import Process
from runner import add_cert, override_hosts, restore_hosts, get_hosts_origin_ips
from server import run_server, clear_cache
from settings import Settings
from threading import Thread
from tkinter import *
from tkinter import messagebox
from tkinter import ttk


class MainWindow:
    def __init__(self, root):
        self.settings = Settings()

        root.title("MSFS 2020 Google Map")
        root.resizable(False, False)

        mainframe = ttk.Frame(root)
        mainframe.grid(column=0, row=0, )

        row = 0

        row += 1
        self.setting_tabs = ttk.Notebook(mainframe)
        self.setting_tabs.grid(column=1, row=row, columnspan=3)

        help = ttk.Frame(self.setting_tabs, padding=10)
        self.create_help(help)
        self.setting_tabs.add(help, text="Help")

        proxy_settings = ttk.Frame(self.setting_tabs, padding=10)
        self.create_proxy_settings(proxy_settings)
        self.setting_tabs.add(proxy_settings, text='Proxy')

        google_map_server_settings = ttk.Frame(self.setting_tabs, padding=10)
        self.create_google_map_settings(google_map_server_settings)
        self.setting_tabs.add(google_map_server_settings, text='Map Server')

        cache_settings = ttk.Frame(self.setting_tabs, padding=10)
        self.create_cache_settings(cache_settings)
        self.setting_tabs.add(cache_settings, text="Cache")

        row += 1
        self.status = StringVar(value="Stopped")
        ttk.Label(mainframe, textvariable=self.status).grid(column=1, row=row)
        ttk.Button(mainframe, text="Run", command=self.run).grid(column=2, row=row)
        ttk.Button(mainframe, text="Stop", command=self.stop).grid(column=3, row=row)

        row += 1
        ttk.Label(mainframe, text="If you like this mod, please help me improve it by donate",
                  background="#f1e740").grid(column=1, row=row,
                                             columnspan=2)
        ttk.Button(mainframe, text="Donate", command=self.donate).grid(column=3, row=row)

        for child in mainframe.winfo_children():
            child.grid_configure(padx=5, pady=5)

        root.protocol("WM_DELETE_WINDOW", self.quit)

        self.startup_checks()

        self.root = root
        self.server_process = None
        self.nginx_process = None

    def startup_checks(self):
        if not self.is_admin():
            messagebox.showerror(
                message='Please run in Administrator mode, application will close')
            exit(-1)

        if self.is_443_occupied():
            messagebox.showerror(
                message='You have application using 443 port, please close them, application will close')
            exit(-1)

        current_path = os.path.abspath(os.getcwd())
        if not current_path.isascii():
            messagebox.showerror(
                message=f"Your current path({current_path}) contains non-ascii characters, the mod won't run. \n"
                        f"Please move the entire folder into folder not contains non-ascii characters. \n"
                        f"If not sure, move to root folder of disk driver (D:\\ or E:\\)\n"
                        f"Application will close now"
            )
            exit(-1)

    def create_proxy_settings(self, parent):
        row = 1
        ttk.Label(parent,
                  text="Proxy format: http://ip:port or socks5h://ip:port"
                       "\nExample: http://192.168.10.1:8080 or socks5h://192.168.10.10:1080"
                       "\nNote: leave blank if you don't need proxy to access google").grid(
            column=1, row=row, sticky=W, columnspan=3)

        row += 1
        self.proxy_address = StringVar()
        proxy_address_entry = ttk.Entry(parent, width=30,
                                        textvariable=self.proxy_address)
        self.proxy_address.trace_add("write", self.proxy_address_updated)
        proxy_address_entry.grid(column=2, row=row, sticky=(W, E))
        self.proxy_address.set(self.settings.proxy_url)

        ttk.Label(parent, text="Proxy").grid(column=1, row=row, )
        ttk.Button(parent, text="Test Connection",
                   command=self.test_google_access).grid(column=3, row=row, )

        row += 1
        ttk.Label(parent, text="Try another server if loading speed is slow, you must stop and then run again").grid(
            column=1, row=row, columnspan=3,
            sticky=W)

    def create_google_map_settings(self, parent):
        row = 1
        ttk.Label(parent, text="Google server").grid(column=1, row=row, )

        self.selected_google_server = StringVar()
        google_server_combo = ttk.Combobox(parent, textvariable=self.selected_google_server)
        google_server_combo['values'] = self.settings.google_servers
        google_server_combo['state'] = 'readonly'
        google_server_combo.grid(column=2, row=row, )
        google_server_combo.bind('<<ComboboxSelected>>', self.google_server_selected)
        self.selected_google_server.set(self.settings.google_server)

    def create_cache_settings(self, parent):
        row = 1
        ttk.Button(parent, text="Clear cache", command=self.clear_cache
                   ).grid(column=4, row=row)

    def create_help(self, parent):
        row = 1
        ttk.Label(parent, text="First time intro (VERY IMPORTANT)").grid(column=1, row=row, sticky=(W, E))
        ttk.Button(parent, text="Open Introduction and Usage page",
                   command=lambda: webbrowser.open("https://www.youtube.com/watch?v=Lk7GK5XLTt8")).grid(column=2,
                                                                                                        row=row,
                                                                                                        sticky=(W, E))
        row += 1
        ttk.Label(parent, text="Discussion").grid(column=1, row=row, sticky=(W, E))
        ttk.Button(parent, text="Open FlightSim.to homepage",
                   command=lambda: webbrowser.open(
                       "https://zh.flightsim.to/file/19345/msfs-2020-google-map-replacement")).grid(
            column=2,
            row=row, sticky=(W, E))

        row += 1
        ttk.Label(parent, text="Please always check latest version").grid(column=1, row=row, sticky=(W, E))
        ttk.Button(parent, text="Open Latest release page",
                   command=lambda: webbrowser.open("https://github.com/derekhe/msfs2020-google-map/releases")).grid(
            column=2, row=row, sticky=(W, E))

        row += 1
        ttk.Label(parent, text="Please try disable your firewall\n and antivirus tools if you have trouble").grid(
            column=1, row=row, sticky=(W, E))
        ttk.Button(parent, text="Report issue",
                   command=lambda: webbrowser.open("https://github.com/derekhe/msfs2020-google-map/issues")).grid(
            column=2, row=row, sticky=(W, E))

        row += 1
        ttk.Label(parent, text="Please setup proxy if your access to google is blocked", background="#f1e740").grid(
            column=1, row=row, sticky=(W, E), columnspan=2)

        for child in parent.winfo_children():
            child.grid_configure(padx=5, pady=5)

    @staticmethod
    def is_admin():
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except:
            return False

    def proxy_address_updated(self, *args):
        self.settings.proxy_url = self.proxy_address.get()

    def google_server_selected(self, event):
        self.settings.google_server = self.selected_google_server.get()

    def test_google_access(self):
        try:
            begin = time.time()
            response = self.request_google()
            duration = time.time() - begin
            if response.status_code == 200:
                messagebox.showinfo(message=f'Proxy is good, response time is {duration:0.2}s')
            else:
                messagebox.showerror(message='Google access failed, please check')
        except:
            messagebox.showerror(message='Google access failed, please check')

    def request_google(self):
        return requests.get(
            f"https://{self.selected_google_server.get()}/vt/lyrs=s&x=1&y=1&z=1", timeout=3,
            proxies={"https": self.settings.proxy_url}, verify=False)

    @staticmethod
    def enable_features(template: str):
        features_disabled = {
            "tsom_cc_activation_masks": True,
            "coverage_maps": True,
            "texture_synthesis_online_map_high_res": True,
            "color_corrected_images": True,
            "bing_aerial": True
        }

        out = template
        for feature in features_disabled:
            if features_disabled[feature]:
                out = out.replace(f"#{feature}#", "")
        return out

    @staticmethod
    def config_dns(template: str):
        for k, v in get_hosts_origin_ips().items():
            template = template.replace(f"#{k}#", v)
        return template

    def run(self):
        if not self.is_google_accessible():
            messagebox.showerror(message="Google map access failed,\n"
                                         "please check your connection or setup proxy settings.")
            self.setting_tabs.select(1)
            return

        self.settings.save()
        self.stop()
        try:
            add_cert()
        except:
            traceback.print_exc()
            messagebox.showerror(message=f"Add certificate failed: {traceback.format_exc()}")
            return

        try:
            with open("./src/nginx.conf.template", "rt") as nginx:
                template = nginx.read()
                output = self.enable_features(template)
                output = self.config_dns(output)

            with open("./nginx/conf/nginx.conf", "wt") as out:
                out.write(output)
        except Exception as ex:
            traceback.print_exc()
            messagebox.showerror(message=f"Generate nginx file failed:\n {traceback.format_exc()}")
            return

        try:
            override_hosts()
        except:
            traceback.print_exc()
            messagebox.showerror(
                message=f"Override hosts failed, please try delete the C:\\Windows\\System32\\drivers\\etc\\hosts file, backup it first. Details:\n{traceback.format_exc()}")
            os.startfile("C:\\Windows\\System32\\drivers\\etc")
            return

        try:
            self.server_process = Process(
                target=run_server,
                args=(self.settings.cache_size, self.settings.proxy_url, self.settings.google_server))
            self.server_process.start()
            self.nginx_process = subprocess.Popen(
                "nginx.exe", shell=True, cwd="./nginx")
        except:
            traceback.print_exc()
            messagebox.showerror(message=f"Unable to start nginx:\n{traceback.format_exc()}")
            return

        Thread(target=self.health_check_thread).start()

        self.status.set("Running")

    def health_check_thread(self):
        err_msg = "Health check failed, the mod is not running properly"
        try:
            time.sleep(10)
            response = requests.get("https://kh.ssl.ak.tiles.virtualearth.net/health", timeout=60, verify=False)
            if response.text != "alive":
                messagebox.showerror(message=err_msg)
            print("Health check passed")
        except:
            messagebox.showerror(message=err_msg)

    def is_google_accessible(self):
        try:
            response = self.request_google()
            if response.status_code != 200:
                return False
            return True
        except:
            return False

    def stop(self):
        restore_hosts()

        if self.server_process is not None:
            self.server_process.kill()

        if self.nginx_process is not None:
            subprocess.run("taskkill /F /IM nginx.exe", shell=True, check=True)
            self.nginx_process.wait(1)
            self.nginx_process = None

        self.status.set("Stopped")

    @staticmethod
    def clear_cache():
        try:
            Cache("./cache").clear()
            messagebox.showinfo(message="Cache cleared")
        except:
            messagebox.showinfo(message="Cache clean failed")

    def quit(self):
        try:
            self.settings.save()
            self.stop()
        finally:
            self.root.destroy()

    def donate(self):
        webbrowser.open("https://www.paypal.com/paypalme/siconghe?country.x=C2&locale.x=en_US")

    @staticmethod
    def is_443_occupied():
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            result = sock.connect_ex(('127.0.0.1', 443))
            return result == 0


if __name__ == '__main__':
    root = Tk()
    MainWindow(root)
    root.mainloop()
