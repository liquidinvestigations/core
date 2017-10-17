from django.http import HttpResponse
from django.shortcuts import render
from . import agent


def reconfigure(request):
    jobs = sorted(agent.status().items())
    return render(request, 'liquidcore/config.html', {
        'jobs': jobs,
    })


def reconfigure_job_log(request, job_id):
    job = agent.status()[job_id]['job']
    with job.open_logfile() as f:
        return HttpResponse(f.read(), content_type='text/plain')
