import requests
from django.conf import settings
from requests.exceptions import ConnectionError
from json.decoder import JSONDecodeError

def get_status():
    if not settings.DISCOVERY_URL:
        raise RuntimeError("settings.DISCOVERY_URL was not configured")
    try:
        return {
            "running": True,
            "status": requests.get(settings.DISCOVERY_URL).json()
        }
    except (ConnectionError, JSONDecodeError):
        return {"running": False}

def get_node_list():
    return requests.get(settings.DISCOVERY_URL + "/nodes").json()
