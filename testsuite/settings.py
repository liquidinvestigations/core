import os
import json

os.environ['LIQUID_DOMAIN'] = 'liquid.example.org'
os.environ['LIQUID_TITLE'] = 'Liquid Example Org'
os.environ['SECRET_KEY'] = 'sheap'
os.environ['LIQUID_2FA'] = 'true'
os.environ['LIQUID_APPS'] = json.dumps([
    {
        'id': 'example_non_admin',
        'title': 'example_user',
        'url': 'www.liquid.example.org',
        'enabled': True,
        'description': 'example user',
        'adminOnly': False,
    },

    {
        'id': 'example_admin',
        'title': 'example_admin',
        'url': 'www.liquid.example.org',
        'enabled': True,
        'description': 'example admin',
        'adminOnly': True,
    },
])

from liquidcore.site.settings import *  # noqa
