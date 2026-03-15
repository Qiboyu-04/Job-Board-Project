from django.shortcuts import render

from .models import Job


def home(request):
    return render(request, "jobs/home.html")


def job_list(request):

    jobs = Job.objects.all()

    return render(request, "jobs/job_list.html", {
        "jobs": jobs
    })