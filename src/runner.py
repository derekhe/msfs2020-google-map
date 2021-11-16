import dns
import os
import stat
import subprocess
import dns.resolver
import traceback
import urllib3

urllib3.disable_warnings()

__domains = ['kh.ssl.ak.tiles.virtualearth.net', 'khstorelive.azureedge.net']
__default_ip = {
    'kh.ssl.ak.tiles.virtualearth.net': '104.85.242.213',
    'khstorelive.azureedge.net': '104.212.68.114'
}
host_path = "C:\\Windows\\System32\\drivers\\etc\\hosts"
host_entries = [f"\n127.0.0.1 {domain}\n" for domain in __domains]


def add_cert():
    subprocess.run(["certutil", "-addstore", "-f", "root",
                    ".\\certs\\cert.crt"], shell=True, check=True)


def get_hosts_origin_ips():
    try:
        origin_ips = {}
        dns_resolver = dns.resolver.Resolver()
        for d in __domains:
            origin_ips[d] = dns_resolver.resolve(d)[0].to_text()
        print(origin_ips)
        return origin_ips
    except dns.exception.Timeout:
        traceback.print_exc()
        return __default_ip


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