from django.shortcuts import render, get_object_or_404, redirect

from .models import Job, Application
from .forms import ApplicationForm
from django.contrib.auth.decorators import login_required


def home(request):
    return render(request, "jobs/home.html")


def job_list(request):

    jobs = Job.objects.all()

    return render(request, "jobs/job_list.html", {
        "jobs": jobs
    })

def job_detail(request, job_id):
    job = get_object_or_404(Job, pk=job_id)

    already_applied = False
    if request.user.is_authenticated:
        already_applied = Application.objects.filter(
            student=request.user,
            job=job
        ).exists()

    success = request.GET.get('success') == '1'
    duplicate = request.GET.get('duplicate') == '1'

    return render(request, 'jobs/job_detail.html', {
        'job': job,
        'already_applied': already_applied,
        'success': success,
        'duplicate': duplicate,
    })

@login_required
def apply_job(request, job_id):
    job = get_object_or_404(Job, pk=job_id)

    if Application.objects.filter(student=request.user, job=job).exists():
        return redirect(f'/jobs/{job.id}/?duplicate=1')

    if request.method == 'POST':
        form = ApplicationForm(request.POST)
        if form.is_valid():
            app = form.save(commit=False)
            app.student = request.user
            app.job = job
            app.save()
            return redirect(f'/jobs/{job.id}/?success=1')
    else:
        form = ApplicationForm()

    return render(request, 'jobs/apply.html', {
        'form': form,
        'job': job
    })