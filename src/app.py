import atexit
import time

import ctypes
import os.path
import requests
import socket
import subprocess
import traceback
import webbrowser
from multiprocessing import Process
from requests import Response
from runner import add_cert, override_hosts, restore_hosts, del_cert
from server import run_server, url_mapping
from settings import Settings
from threading import Thread
from tkinter import *
from tkinter import messagebox
from tkinter import ttk


class MainWindow:
    def __init__(self, root: any) -> None:
        self.settings = Settings()

        if self.is_warning_enabled():
            webbrowser.open_new("https://github.com/derekhe/msfs2020-google-map/wiki/Welcome")

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

        row += 1
        ttk.Label(mainframe,
                  text="Important:\n• Click run before you start MSFS2020\n• Setup proxy if your access to google is blocked\n• Press Stop button before you close otherwise MSFS2020 will not load",
                  background="#f1e740").grid(
            column=1, row=row, sticky=(W, E), columnspan=2)

        row += 1
        self.warning_status = StringVar(value=self.settings.welcome_page_and_warning_enabled)
        ttk.Checkbutton(mainframe,
                        text="I read the welcome and FAQ page\nI know what will happen, don't show me again",
                        command=self.warning_status_changed, variable=self.warning_status, onvalue='disabled',
                        offvalue='enabled').grid(column=1, row=row, sticky=(W, E), columnspan=2)

        row += 1

        self.status = StringVar(value="Stopped")
        ttk.Label(mainframe, textvariable=self.status).grid(column=1, row=row)
        ttk.Button(mainframe, text="Run", command=self.run).grid(column=2, row=row)
        ttk.Button(mainframe, text="Stop", command=self.stop).grid(column=3, row=row)

        row += 1
        ttk.Label(mainframe, text="If you like this mod, please help me improve it by donating",
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

    def warning_status_changed(self) -> None:
        self.settings.welcome_page_and_warning_enabled = self.warning_status.get()

    def startup_checks(self) -> None:
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

    def create_proxy_settings(self, parent: any) -> None:
        row = 1
        ttk.Label(parent,
                  text="Proxy format: http://ip:port or socks5h://ip:port"
                       "\nExample: http://192.168.10.1:8080 or socks5h://192.168.10.10:1080"
                       "\n\nNote: Leave blank if you don't need proxy to access google").grid(
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

    def create_google_map_settings(self, parent: any) -> None:
        row = 1
        ttk.Label(parent, text="Google Maps Server").grid(column=1, row=row, )

        self.selected_google_server = StringVar()
        google_server_combo = ttk.Combobox(parent, textvariable=self.selected_google_server)
        google_server_combo['values'] = self.settings.google_servers
        google_server_combo['state'] = 'readonly'
        google_server_combo.grid(column=2, row=row, )
        google_server_combo.bind('<<ComboboxSelected>>', self.google_server_selected)
        self.selected_google_server.set(self.settings.google_server)

    @staticmethod
    def create_help(parent: any) -> None:
        row = 1
        ttk.Label(parent, text="First time info (VERY IMPORTANT)").grid(column=1, row=row, sticky=(W, E))
        ttk.Button(parent, text="Open Introduction and Usage page",
                   command=lambda: webbrowser.open("https://www.youtube.com/watch?v=Lk7GK5XLTt8")).grid(column=2,
                                                                                                        row=row,
                                                                                                        sticky=(W, E))
        row += 1
        ttk.Label(parent, text="Discussion").grid(column=1, row=row, sticky=(W, E))
        ttk.Button(parent, text="Open Flightsim.to homepage",
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
        ttk.Label(parent, text="Please try disabling your firewall\nand antivirus tools if you have trouble").grid(
            column=1, row=row, sticky=(W, E))
        ttk.Button(parent, text="Report issue",
                   command=lambda: webbrowser.open("https://github.com/derekhe/msfs2020-google-map/issues")).grid(
            column=2, row=row, sticky=(W, E))

        for child in parent.winfo_children():
            child.grid_configure(padx=5, pady=5)

    @staticmethod
    def is_admin() -> bool:
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except Exception:
            return False

    def proxy_address_updated(self, *args: list[str]) -> None:
        self.settings.proxy_url = self.proxy_address.get()

    def google_server_selected(self, event: str) -> None:
        self.settings.google_server = self.selected_google_server.get()

    def test_google_access(self) -> None:
        try:
            begin = time.time()
            response = self.request_google()
            duration = time.time() - begin
            if response.status_code == 200:
                messagebox.showinfo(message=f'Proxy is good, response time is {duration:0.2}s')
            else:
                messagebox.showerror(message='Google access failed, please check')
        except Exception:
            messagebox.showerror(message='Google access failed, please check')

    def request_google(self) -> Response:
        return requests.get(
            url_mapping(self.selected_google_server.get(), 1, 1, 1), timeout=3,
            proxies={"https": self.settings.proxy_url}, verify=False)

    @staticmethod
    def enable_features(template: str) -> str:
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

    def run(self) -> None:
        if self.is_warning_enabled():
            messagebox.showwarning(title="IMPORTANT",
                                   message="Press the STOP button before you close this mod otherwise MSFS2020 won't work next time!")

        if not self.is_google_accessible():
            messagebox.showerror(message="Google map access failed,\n"
                                         "please check your connection or setup proxy settings.")
            self.setting_tabs.select(1)
            return

        self.settings.save()
        self.stop()
        try:
            add_cert()
        except Exception:
            traceback.print_exc()
            messagebox.showerror(message=f"Add certificate failed: {traceback.format_exc()}")
            return

        try:
            override_hosts()
        except Exception:
            traceback.print_exc()
            messagebox.showerror(
                message=f"Override hosts failed, please try delete the C:\\Windows\\System32\\drivers\\etc\\hosts "
                        f"file, backup it first.\n "
                        f"If problem still comes, please make sure this file has write permission. Disable your "
                        f"antivirus or add exception to this file. "
                        f" Details:\n{traceback.format_exc()}")
            os.startfile("C:\\Windows\\System32\\drivers\\etc")
            return

        try:
            self.server_process = Process(
                target=run_server,
                args=(
                    self.settings.proxy_url, self.settings.google_server))
            self.server_process.start()
            self.nginx_process = subprocess.Popen(
                "nginx.exe", shell=True, cwd="./nginx")
        except Exception:
            traceback.print_exc()
            messagebox.showerror(message=f"Unable to start nginx:\n{traceback.format_exc()}")
            return

        Thread(target=self.health_check_thread).start()

        self.status.set("Running")

    @staticmethod
    def health_check_thread() -> None:
        err_msg = "Health check failed, the mod is not running properly"
        try:
            time.sleep(10)
            print("Checking mock server health")
            no_proxy = {"http": None, "https": None, }
            response = requests.get("https://kh.ssl.ak.tiles.virtualearth.net/health", timeout=60, verify=False,
                                    proxies=no_proxy)
            if response.text != "alive":
                messagebox.showerror(message=err_msg)
            print("Mock server health passed")

            print("Checking nginx server health")
            response = requests.get(
                "https://khstorelive.azureedge.net/results/v1.20.0/coverage_maps/lod_8/12202100.cov?version=3",
                timeout=10, verify=False, proxies=no_proxy)
            if response.status_code != 404:
                messagebox.showerror(message="Nginx not running properly, please try restart the app")
            print("Health check passed")
        except Exception:
            traceback.print_exc()
            messagebox.showerror(message=err_msg)

    def is_google_accessible(self) -> bool:
        try:
            response = self.request_google()
            if response.status_code != 200:
                return False
            return True
        except Exception:
            return False

    def stop(self) -> None:
        restore_hosts()
        del_cert()

        if self.server_process is not None:
            self.server_process.kill()

        if self.nginx_process is not None:
            stop_nginx()
            self.nginx_process.wait(1)
            self.nginx_process = None

        self.status.set("Stopped")

    def quit(self) -> None:
        try:
            self.settings.save()
            self.stop()
        finally:
            self.root.destroy()

    @staticmethod
    def donate() -> None:
        webbrowser.open("https://www.paypal.com/paypalme/siconghe?country.x=C2&locale.x=en_US")

    @staticmethod
    def is_443_occupied() -> bool:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            result = sock.connect_ex(('127.0.0.1', 443))
            return result == 0

    def is_warning_enabled(self) -> bool:
        return self.settings.welcome_page_and_warning_enabled == "enabled"


def stop_nginx() -> None:
    subprocess.run("taskkill /F /IM nginx.exe", shell=True, check=False, stdout=subprocess.DEVNULL,
                   stderr=subprocess.DEVNULL)


def restore_system() -> None:
    restore_hosts()
    stop_nginx()


if __name__ == '__main__':
    try:
        restore_system()
    except Exception:
        pass

    atexit.register(restore_system)
    root = Tk()
    MainWindow(root)
    root.mainloop()
