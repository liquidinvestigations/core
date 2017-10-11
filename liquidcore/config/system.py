import json
from . import models


def get_configuration():
    def map_table(model):
        return {item.name: item.data for item in model.objects.all()}

    db = {
        'services': map_table(models.Service),
        'nodes': map_table(models.Node),
    }

    settings = map_table(models.Setting)

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
