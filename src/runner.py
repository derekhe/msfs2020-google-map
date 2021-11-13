import dns
import subprocess
import dns.resolver
import traceback
import urllib3
from python_hosts import Hosts, HostsEntry

urllib3.disable_warnings()

__domains = ['kh.ssl.ak.tiles.virtualearth.net', 'khstorelive.azureedge.net']
__default_ip = {
    'kh.ssl.ak.tiles.virtualearth.net': '104.85.242.213',
    'khstorelive.azureedge.net': '104.212.68.114'
}


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
    hosts = Hosts()
    for domain in __domains:
        hosts.remove_all_matching(name=domain)
        new_entry = HostsEntry(
            entry_type='ipv4', address='127.0.0.1', names=[domain])
        hosts.add([new_entry])
    hosts.write()


def restore_hosts():
    print("Restoring hosts")
    hosts = Hosts()
    for domain in __domains:
        hosts.remove_all_matching(name=domain)
    hosts.write()
