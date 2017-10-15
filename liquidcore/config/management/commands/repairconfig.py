import json
from django.core.management.base import BaseCommand
from ... import system


class Command(BaseCommand):

    help = "Repair a broken system configuration"

    def handle(self, **options):
        job = system.reconfigure_system(repair=True)
        try:
            job.wait()
        except:
            with job.open_logfile() as f:
                print(f.read())
            raise
