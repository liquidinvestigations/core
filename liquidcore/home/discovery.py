import socket
from datetime import datetime
from zeroconf import ServiceBrowser, Zeroconf, ServiceInfo
from django.conf import settings

nodes = {}

def get_data_from_info(info):
    properties = {
            str(key): str(info.properties[key])
            for key in info.properties
    }
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
        if info and b'liquid_hostname' in info.properties:
            nodes[name] = get_data_from_info(info)

    def remove_service(self, zeroconf, type_, name):
        info = zeroconf.get_service_info(type_, name)
        if name in nodes:
            del nodes[name]

zeroconf = None

def start():
    global zeroconf

    zeroconf = Zeroconf()
    listener = WorkstationListener()

    SERVICE_TYPE = "_http._tcp.local."

    # start a browser that listens for our service type
    browser = ServiceBrowser(zeroconf, SERVICE_TYPE, listener)

    # broadcast our service type
    service_hostname = settings.LIQUID_DOMAIN
    service_name = "LI_" + service_hostname.replace(".", "-") + '.' + SERVICE_TYPE
    service_local_hostname = service_hostname.replace(".", "-") + ".local."
    service_desc = { "liquid_hostname" : service_hostname }
    service_ip = socket.inet_aton("127.0.0.1")
    service_port = 80
    liquid_service = ServiceInfo(
            type_=SERVICE_TYPE,
            name=service_name,
            address=service_ip,
            port=service_port,
            properties=service_desc,
            server=service_local_hostname
    )
    zeroconf.register_service(liquid_service)
