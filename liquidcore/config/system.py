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


def configure_system(target_configuration):
    job = agent.launch(target_configuration)

    print('Job {} launched, waiting for it to finish ...'.format(job.id))
    while not job.is_finished():
        import time
        time.sleep(.2)
    print('Job {} done!'.format(job.id))

    with job.open_logfile() as f:
        print('================')
        print(f.read())
        print('================')


def update_system():
    target_configuration = get_configuration()
    configure_system(target_configuration)
