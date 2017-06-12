from datetime import datetime
from zeroconf import ServiceBrowser, Zeroconf

nodes = {}

def get_data_from_info(info):
    return {
        "type": info.type,
        "server": info.server,
        "hostname": info.server[:-1],
        "name": info.name,
        "address": ".".join(str(x) for x in info.address),
        "name": info.name,
        "port": info.port,
        "properties": info.properties,
        "discovered_at": datetime.now().isoformat()
    }

class WorkstationListener(object):
    def add_service(self, zeroconf, type, name):
        info = zeroconf.get_service_info(type, name)
        nodes[name] = get_data_from_info(info)

    def remove_service(self, zeroconf, type, name):
        info = zeroconf.get_service_info(type, name)
        del nodes[name]

zeroconf = Zeroconf()
listener = WorkstationListener()
browser = ServiceBrowser(zeroconf, "_workstation._tcp.local.", listener)
