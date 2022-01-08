import os
import stat
import subprocess

import urllib3

urllib3.disable_warnings()

host_path: str = "C:\\Windows\\System32\\drivers\\etc\\hosts"
__domains: list[str] = ['kh.ssl.ak.tiles.virtualearth.net', 'khstorelive.azureedge.net']
host_entries: list[str] = [f"\n127.0.0.1 {domain}\n" for domain in __domains]


def run_sub(*, isadd: bool) -> None:
    cert_cmd = ["certutil", "-addstore" if isadd is True else "-delstore", "-f", "root", ".\\certs\\cert.crt"]
    subprocess.run(cert_cmd, shell=True, check=True)


def add_cert() -> None:
    run_sub(isadd=True)


def del_cert() -> None:
    run_sub(isadd=False)


def override_hosts() -> None:
    print("Overriding hosts")
    os.chmod(host_path, stat.S_IWRITE)
    with open(host_path, "a") as f:
        f.writelines(host_entries)
    print("Overrode hosts")


def restore_hosts() -> None:
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
