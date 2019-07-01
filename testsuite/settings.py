import os
os.environ['LIQUID_DOMAIN'] = 'liquid.example.org'
os.environ['LIQUID_TITLE'] = 'Liquid Example Org'
os.environ['SECRET_KEY'] = 'sheap'
os.environ['LIQUID_2FA'] = 'true'

from liquidcore.site.settings import *  # noqa
