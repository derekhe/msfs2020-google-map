import time

import ctypes
import requests
import subprocess
import traceback
import webbrowser
from multiprocessing import Process
from runner import add_cert, override_hosts, restore_hosts, get_hosts_origin_ips
from server import run_server
from settings import Settings
from tkinter import *
from tkinter import messagebox
from tkinter import ttk


class MainWindow:
    def __init__(self, root):
        self.settings = Settings()

        root.title("MSFS 2020 Google Map")

        mainframe = ttk.Frame(root, padding="3 3 12 12")
        mainframe.grid(column=0, row=0, sticky=(N, W, E, S))

        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)

        row = 1
        ttk.Label(mainframe,
                  text="Proxy format: http://ip:port or socks5h://ip:port"
                       "\nExample: http://192.168.10.1:8080 or socks5h://192.168.10.10:1080"
                       "\nNote: leave blank if you don't need proxy to access google").grid(
            column=1, row=row, sticky=W, columnspan=3)

        row += 1
        self.proxy_address = StringVar()
        proxy_address_entry = ttk.Entry(mainframe, width=30,
                                        textvariable=self.proxy_address)
        self.proxy_address.trace_add("write", self.proxy_address_updated)
        proxy_address_entry.grid(column=2, row=row, sticky=(W, E))
        self.proxy_address.set(self.settings.proxy_url)

        ttk.Label(mainframe, text="Proxy").grid(column=1, row=row, )
        ttk.Button(mainframe, text="Test Connection",
                   command=self.test_proxy).grid(column=3, row=row, )

        row += 1
        ttk.Label(mainframe, text="Try another server if loading speed is slow, you must stop and then run again").grid(
            column=1, row=row, columnspan=3,
            sticky=W)

        row += 1
        ttk.Label(mainframe, text="Google server").grid(column=1, row=row, )

        self.selected_google_server = StringVar()
        google_server_combo = ttk.Combobox(mainframe, textvariable=self.selected_google_server)
        google_server_combo['values'] = self.settings.google_servers
        google_server_combo['state'] = 'readonly'
        google_server_combo.grid(column=2, row=row, )
        google_server_combo.bind('<<ComboboxSelected>>', self.google_server_selected)
        self.selected_google_server.set(self.settings.google_server)

        row += 1
        self.status = StringVar(value="Stopped")
        ttk.Label(mainframe, textvariable=self.status).grid(column=1, row=row)

        ttk.Button(mainframe, text="Run", command=self.run
                   ).grid(column=2, row=row)

        ttk.Button(mainframe, text="Stop", command=self.stop
                   ).grid(column=3, row=row)

        ttk.Button(mainframe, text="Clear cache", command=self.clear_cache
                   ).grid(column=4, row=row)

        for child in mainframe.winfo_children():
            child.grid_configure(padx=5, pady=5)

        if not self.is_admin():
            messagebox.showerror(
                message='Please run in Administrator mode, application will close')
            root.destory()

        root.protocol("WM_DELETE_WINDOW", self.quit)

        self.root = root
        self.server_process = None
        self.nginx_process = None

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

    def test_proxy(self):
        try:
            begin = time.time()
            response = requests.get(
                f"https://{self.selected_google_server.get()}/vt/lyrs=s&x=1&y=1&z=1", timeout=3,
                proxies={"https": self.settings.proxy_url})
            duration = time.time() - begin
            if response.status_code == 200:
                messagebox.showinfo(message=f'Proxy is good, response time is {duration:0.2}s')
            else:
                messagebox.showerror(message='Connection failed, please check')
        except:
            messagebox.showerror(message='Connection failed, please check')

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
        self.settings.save()
        self.stop()
        try:
            add_cert()
        except:
            messagebox.showerror(message="Add certificate failed")

        try:
            with open("./src/nginx.conf.template", "rt") as nginx:
                template = nginx.read()
                output = self.enable_features(template)
                output = self.config_dns(output)

            with open("./nginx/conf/nginx.conf", "wt") as out:
                out.write(output)
        except:
            traceback.print_exc()
            messagebox.showerror(message="Generate nginx file failed")

        try:
            override_hosts()
        except:
            messagebox.showerror(message="Override hosts failed")

        try:
            self.server_process = Process(
                target=run_server, args=(self.settings.cache_size, self.settings.proxy_url, self.settings.google_server))
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
            subprocess.run("taskkill /F /IM nginx.exe", shell=True, check=True)
            self.nginx_process.wait(1)
            self.nginx_process = None

        self.status.set("Stopped")

    @staticmethod
    def clear_cache():
        if requests.delete("http://localhost:8000/cache", timeout=15).status_code == 200:
            messagebox.showinfo("Cache cleared")

    def quit(self):
        try:
            self.settings.save()
            self.stop()
            restore_hosts()
        finally:
            self.root.destroy()


if __name__ == '__main__':
    webbrowser.open("https://github.com/derekhe/msfs2020-google-map/releases")
    root = Tk()
    MainWindow(root)
    root.mainloop()
