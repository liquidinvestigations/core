import socket
from datetime import datetime
from zeroconf import ServiceBrowser, Zeroconf, ServiceInfo, NonUniqueNameException
from django.conf import settings

nodes = {}

def update_dns():
    with open(settings.DNSMASQ_OVERWRITE_CONF, 'w') as conf:
        for node in nodes.values():
            conf.write('address=/{}/{}\n'.format(node['hostname'], node['address']))

def dict_decode(data):
    def decode(data):
        if isinstance(data, bytes):
            return data.decode("latin-1")
        elif isinstance(data, str):
            return data
        return str(data)

    return {
            decode(key): decode(data[key])
            for key in data
    }

def get_data_from_info(info, properties):
    hostname = properties['liquid_hostname']
    return {
        "type": info.type,
        "server": info.server,
        "hostname": hostname,
        "local": hostname == settings.LIQUID_DOMAIN,
        "name": info.name,
        "address": ".".join(str(x) for x in info.address),
        "name": info.name,
        "port": info.port,
        "properties": properties,
        "discovered_at": datetime.now().isoformat()
    }

class WorkstationListener(object):
    def add_service(self, zeroconf, type_, name):
        info = zeroconf.get_service_info(type_, name, 10000)
        if not info:
            return
        properties = dict_decode(info.properties)
        if 'liquid_hostname' in properties:
            nodes[name] = get_data_from_info(info, properties)
            update_dns()

    def remove_service(self, zeroconf, type_, name):
        if name in nodes:
            del nodes[name]
            update_dns()

zeroconf = None

SERVICE_TYPE = "_liquid._tcp.local."

def start():
    global zeroconf

    if nodes:
        # this has been run before
        return

    # initially, wipe the dns config
    update_dns()

    zeroconf = Zeroconf()
    listener = WorkstationListener()

    # start a browser that listens for our service type
    browser = ServiceBrowser(zeroconf, SERVICE_TYPE, listener)
