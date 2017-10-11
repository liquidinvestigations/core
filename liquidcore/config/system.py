import json
from . import models


def get_configuration():
    settings = {
        item.name: item.data
        for item in models.Setting.objects.all()
    }

    return {
        'domain': settings['domain'],
        'lan': settings['lan'],
        'wan': settings['wan'],
        'ssh': settings['ssh'],
        'services': {
            s.name: {'enabled': s.is_enabled}
            for s in models.Service.objects.all()
        },
    }


def update_system():
    configuration = get_configuration()
    print('TODO update system', json.dumps(configuration, indent=2))
