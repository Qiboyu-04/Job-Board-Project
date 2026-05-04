from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden, JsonResponse
from django.contrib.auth.models import Group, Permission,User
from django.db.models import Count
from .models import Job, Application, Profile, SavedJob, Company, Resume, JOB_CATEGORY_CHOICES, Notification
from .forms import ApplicationForm, UserRegisterForm, UserLoginForm


def redirect_by_user_type(user):
    profile, _ = Profile.objects.get_or_create(user=user)
    if profile.user_type == 'employer':
        return redirect('company_dashboard')
    return redirect('job_list')


def home(request):
    return render(request, "jobs/home.html")


def register_view(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)

        if form.is_valid():
            user = form.save()
            user_type = form.cleaned_data.get('user_type')

            profile = Profile.objects.get(user=user)
            profile.user_type = user_type
            profile.save()

            if user_type in ['employer', 'admin']:
                user.is_staff = True
                user.save()
                group, _ = Group.objects.get_or_create(name='Qualified Company')
                user.groups.add(group)

            if user_type == 'employer':
                company_name = f"{user.username}'s Company"
                Company.objects.get_or_create(
                    name=company_name,
                    defaults={'created_by': user},
                )

            login(request, user)
            return redirect_by_user_type(user)

    else:
        form = UserRegisterForm()

    return render(request, 'jobs/register.html', {'form': form})


def login_view(request):
    if request.method == 'POST':
        form = UserLoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            next_url = request.GET.get('next')
            return redirect(next_url if next_url else redirect_by_user_type(user).url)
    else:
        form = UserLoginForm()
    return render(request, 'jobs/login.html', {'form': form})


@login_required
def logout_view(request):
    logout(request)
    return redirect('home')


def job_list(request):
    jobs = Job.objects.all()

    query = request.GET.get('q', '')
    selected_location = request.GET.get('location', '')
    selected_type = request.GET.get('type', '')
    selected_category = request.GET.get('category', '')

    if query:
        jobs = jobs.filter(title__icontains=query)

    if selected_location:
        jobs = jobs.filter(location__icontains=selected_location)

    if selected_type:
        jobs = jobs.filter(job_type=selected_type)

    if selected_category:
        jobs = jobs.filter(category=selected_category)

    return render(request, "jobs/job_list.html", {
        "jobs": jobs,
        "query": query,
        "selected_location": selected_location,
        "selected_type": selected_type,
        "selected_category": selected_category,
        "categories": JOB_CATEGORY_CHOICES,
    })

def job_detail(request, job_id):
    job = get_object_or_404(Job, pk=job_id)

    already_applied = False
    if request.user.is_authenticated:
        already_applied = Application.objects.filter(
            student=request.user,
            job=job
        ).exists()

    is_saved = False
    if request.user.is_authenticated:
        is_saved = SavedJob.objects.filter(user=request.user, job=job).exists()

    success = request.GET.get('success') == '1'
    duplicate = request.GET.get('duplicate') == '1'

    return render(request, 'jobs/job_detail.html', {
        'job': job,
        'already_applied': already_applied,
        'success': success,
        'duplicate': duplicate,
        'is_saved': is_saved,
    })

@login_required
def apply_job(request, job_id):
    job = get_object_or_404(Job, pk=job_id)

    profile, _ = Profile.objects.get_or_create(user=request.user)
    if profile.user_type != 'student':
        return HttpResponseForbidden("Only job seekers can apply for jobs.")

    if Application.objects.filter(student=request.user, job=job).exists():
        return redirect(f'/jobs/{job.id}/?duplicate=1')

    if request.method == 'POST':
        form = ApplicationForm(request.POST, request.FILES)
        if form.is_valid():
            app = form.save(commit=False)
            app.student = request.user
            app.job = job

            resume_file = form.cleaned_data.get('resume_file')
            resume_title = form.cleaned_data.get('resume_title') or f"{request.user.username} Resume"
            if resume_file:
                resume = Resume.objects.create(
                    student=request.user,
                    title=resume_title,
                    file=resume_file
                )
                app.resume = resume

            app.save()
            return redirect(f'/jobs/{job.id}/?success=1')
    else:
        form = ApplicationForm()

    return render(request, 'jobs/apply.html', {
        'form': form,
        'job': job
    })


@login_required(login_url='login')
def company_dashboard(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)
    if profile.user_type != 'employer':
        return HttpResponseForbidden("Only company users can access this page.")

    jobs = Job.objects.filter(posted_by=request.user).order_by('-id')
    return render(request, 'jobs/company_dashboard.html', {'jobs': jobs})


# Toggle save/unsave job for user
@login_required(login_url='login')
def toggle_save_job(request, job_id):
    job = get_object_or_404(Job, pk=job_id)

    saved = SavedJob.objects.filter(user=request.user, job=job)

    if saved.exists():
        saved.delete()
    else:
        SavedJob.objects.create(user=request.user, job=job)

    return redirect('job_detail', job_id=job.id)


# View for user's saved jobs
@login_required(login_url='login')
def saved_jobs(request):
    saved_jobs = SavedJob.objects.filter(user=request.user)
    return render(request, 'jobs/saved_jobs.html', {
        'saved_jobs': saved_jobs
    })


# View for notifications/messages
@login_required(login_url='login')
def notifications(request):
    """Display all notifications for the logged-in user"""
    profile, _ = Profile.objects.get_or_create(user=request.user)
    
    # Get all notifications for the user
    all_notifications = Notification.objects.filter(recipient=request.user).order_by('-created_at')
    
    # Count unread notifications
    unread_count = Notification.objects.filter(recipient=request.user, is_read=False).count()
    
    # Get new applications for employers
    new_applications_count = 0
    if profile.user_type == 'employer':
        new_applications = Notification.objects.filter(
            recipient=request.user,
            notification_type='application_received',
            is_read=False
        )
        new_applications_count = new_applications.count()
    
    return render(request, 'jobs/notifications.html', {
        'notifications': all_notifications,
        'unread_count': unread_count,
        'new_applications_count': new_applications_count,
    })


@login_required(login_url='login')
def mark_notification_as_read(request, notification_id):
    """Mark a single notification as read"""
    notification = get_object_or_404(Notification, pk=notification_id)
    
    if notification.recipient != request.user:
        return HttpResponseForbidden("You don't have permission to access this notification.")
    
    notification.is_read = True
    notification.save()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True})
    
    return redirect('notifications')


@login_required(login_url='login')
def mark_all_as_read(request):
    """Mark all notifications as read for the current user"""
    Notification.objects.filter(recipient=request.user, is_read=False).update(is_read=True)
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True})
    
    return redirect('notifications')


@login_required(login_url='login')
def get_unread_count(request):
    """Get unread notification count via AJAX"""
    unread_count = Notification.objects.filter(recipient=request.user, is_read=False).count()
    profile, _ = Profile.objects.get_or_create(user=request.user)
    
    new_applications_count = 0
    if profile.user_type == 'employer':
        new_applications_count = Notification.objects.filter(
            recipient=request.user,
            notification_type='application_received',
            is_read=False
        ).count()
    
    return JsonResponse({
        'unread_count': unread_count,
        'new_applications_count': new_applications_count,
    })


@login_required(login_url='login')
def dashboard(request):
    user = request.user
    # Determine user type
    try:
        profile = user.profile
        user_type = profile.user_type
    except Profile.DoesNotExist:
        user_type = 'student'  # default to student if no profile exists

    context = {}
    if user_type == 'student':
        # Student view: show company count and approved job count
        company_count = Company.objects.count()
        job_count = Job.objects.filter(status='approved').count()  # count only approved jobs
        context.update({
            'company_count': company_count,
            'job_count': job_count,
            'user_type': 'student',
        })
    elif user_type == 'employer':
        # Employer view: show total registered student count
        student_count = User.objects.filter(profile__user_type='student').count()
        context.update({
            'student_count': student_count,
            'user_type': 'employer',
        })
    elif user_type == 'admin':
        # Admin view: show all key counts
        company_count = Company.objects.count()
        job_count = Job.objects.filter(status='approved').count()
        student_count = User.objects.filter(profile__user_type='student').count()
        employer_count = User.objects.filter(profile__user_type='employer').count()
        application_count = Application.objects.count()
        context.update({
            'company_count': company_count,
            'job_count': job_count,
            'student_count': student_count,
            'employer_count': employer_count,
            'application_count': application_count,
            'user_type': 'admin',
        })
    else:
       
        return render(request, 'jobs/dashboard.html', {'error': 'Unknown user type'})

    return render(request, 'jobs/dashboard.html', context)