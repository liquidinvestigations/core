from django.http import HttpResponse
from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from . import agent


@staff_member_required
def reconfigure(request):
    jobs = sorted(agent.status().items())
    return render(request, 'liquidcore/config.html', {
        'jobs': jobs,
    })


@staff_member_required
def reconfigure_job_log(request, job_id):
    job = agent.status()[job_id]['job']
    with job.open_logfile() as f:
        return HttpResponse(f.read(), content_type='text/plain')
