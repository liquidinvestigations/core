from . import models
from . import agent


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


def reconfigure_system():
    target_configuration = get_configuration()
    job = agent.launch(target_configuration)
    print('Job {} launched'.format(job.id))
