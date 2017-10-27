from . import models
from . import agent


def get_configuration():
    settings = {
        item.name: item.data
        for item in models.Setting.objects.all()
    }

    client_keys = [
        {'id': str(key.id), 'revoked': key.revoked}
        for key in models.VPNClientKey.objects.all()
    ]

    vpn_client_config_file = settings['vpn_client_config_file']
    if vpn_client_config_file:
        vpn_client = {'config_file': vpn_client_config_file}
    else:
        vpn_client = None

    return {
        'domain': settings['domain'],
        'lan': settings['lan'],
        'wan': settings['wan'],
        'ssh': settings['ssh'],
        'services': {
            s.name: {'enabled': s.is_enabled}
            for s in models.Service.objects.all()
        },
        'vpn': {
            'server': {
                'client_keys': client_keys,
            },
            'client': vpn_client,
        },
    }


def reconfigure_system(repair=False):
    options = {
        'vars': get_configuration(),
    }
    job = agent.launch(options, repair)
    print('Job {} launched'.format(job.id))
    return job


def get_config(key):
    value = get_configuration()

    if key:
        for item in key.split('.'):
            value = value[item]

    return value


def put_config(key_str, value):
    def handle_service(name, value):
        assert isinstance(value, bool)
        service = models.Service.objects.get(name=name)
        service.is_enabled = value
        service.save()
        return reconfigure_system()

    def handle_setting(name, value):
        # TODO perform some kind of validation
        setting = models.Setting.objects.get(name=name)
        setting.data = value
        setting.save()
        return reconfigure_system()

    key = key_str.split('.')

    if key[0] == 'services':
        assert key[2:] == []
        return handle_service(key[1], value)

    elif key[0] in ['domain', 'lan', 'wan', 'ssh']:
        assert key[1:] == []
        return handle_setting(key[0], value)

    else:
        raise ValueError('Unknown key[0] = {!r}'.format(key[0]))
