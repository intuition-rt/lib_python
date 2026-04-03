import ipaddress
import psutil


def get_broadcast_ip():
    yield "<broadcast>"

    for iface_name, addrs in psutil.net_if_addrs().items():
        stats = psutil.net_if_stats().get(iface_name)
        if not stats or not stats.isup:
            continue

        for addr in addrs:
            if addr.family.name == "AF_INET":
                ip = addr.address
                netmask = addr.netmask

                if ip.startswith("127."):
                    continue

                iface = ipaddress.IPv4Interface(f"{ip}/{netmask}")
                broadcast = str(iface.network.broadcast_address)

                if ipaddress.ip_address(ip).is_private:
                    yield broadcast


__all__ = ('get_broadcast_ip',)
