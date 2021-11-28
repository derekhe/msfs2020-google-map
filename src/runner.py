import dns
import os
import stat
import subprocess
import dns.resolver
import traceback
import urllib3

urllib3.disable_warnings()

__domains = ['kh.ssl.ak.tiles.virtualearth.net', 'khstorelive.azureedge.net']
host_path = "C:\\Windows\\System32\\drivers\\etc\\hosts"
host_entries = [f"\n127.0.0.1 {domain}\n" for domain in __domains]


def add_cert():
    subprocess.run(["certutil", "-addstore", "-f", "root",
                    ".\\certs\\cert.crt"], shell=True, check=True)


def del_cert():
    subprocess.run(["certutil", "-delstore", "-f", "root",
                    ".\\certs\\cert.crt"], shell=True, check=True)


def override_hosts():
    print("Overriding hosts")
    os.chmod(host_path, stat.S_IWRITE)
    with open(host_path, "a") as f:
        f.writelines(host_entries)
    print("Hosts override")


def restore_hosts():
    print("Restoring hosts")
    os.chmod(host_path, stat.S_IWRITE)
    with open(host_path, "r+") as f:
        host = f.read()
        for line in host_entries:
            host = host.replace(line, "")
        f.seek(0)
        f.write(host)
        f.truncate()
    print("Restored hosts")
