import socket
from datetime import datetime
from zeroconf import ServiceBrowser, Zeroconf, ServiceInfo
from django.conf import settings

nodes = {}

def get_data_from_info(info):
    return {
        "type": info.type,
        "server": info.server,
        "hostname": info.properties['liquid_hostname'],
        "name": info.name,
        "address": ".".join(str(x) for x in info.address),
        "name": info.name,
        "port": info.port,
        "properties": info.properties,
        "discovered_at": datetime.now().isoformat()
    }

class WorkstationListener(object):
    def add_service(self, zeroconf, type_, name):
        info = zeroconf.get_service_info(type_, name, 10000)
        print("added: ", name, type_, info)
        if info and 'liquid_hostname' in info.properties:
            nodes[name] = get_data_from_info(info)

    def update_record(self, zeroconf, type_, record):
        print("updated: ", record)

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
    print("registering:", service_hostname, service_name, service_local_hostname, sep="\n")
    liquid_service = ServiceInfo(
            type_=SERVICE_TYPE,
            name=service_name,
            address=service_ip,
            port=service_port,
            properties=service_desc,
            server=service_local_hostname
    )
    print("registering ", liquid_service)
    zeroconf.register_service(liquid_service)
