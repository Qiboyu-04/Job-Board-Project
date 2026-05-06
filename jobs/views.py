import os


from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden, JsonResponse
from django.contrib.auth.models import Group, Permission, User
from django.db.models import Count, Q, Avg
from django.db.models.functions import TruncMonth, TruncWeek
from datetime import timedelta, date
from django.utils import timezone
import importlib

try:
    genai = importlib.import_module('google.generativeai')
except ImportError:
    genai = None

from .models import Job, Application, Profile, SavedJob, Company, Resume, JOB_CATEGORY_CHOICES, Notification
from .forms import ApplicationForm, UserRegisterForm, UserLoginForm


def redirect_by_user_type(user):
    profile, _ = Profile.objects.get_or_create(user=user)
    if profile.user_type == 'employer':
        return redirect('company_dashboard')
    return redirect('job_list')


def home(request):
    featured_jobs = Job.objects.filter(status='approved').order_by('-posted_at')[:5]
    return render(request, "jobs/home.html", {'jobs': featured_jobs})


def ai_assistant(request):
    query = request.POST.get('query', '').strip() if request.method == 'POST' else ''
    preferred_type = request.POST.get('preferred_type', '').strip() if request.method == 'POST' else ''
    location = request.POST.get('location', '').strip() if request.method == 'POST' else ''
    skills = request.POST.get('skills', '').strip() if request.method == 'POST' else ''
    ai_response = ''
    recommended_jobs = []
    error = None

    if request.method == 'POST':
        jobs = Job.objects.filter(status='approved')
        if query:
            jobs = jobs.filter(
                Q(title__icontains=query) |
                Q(description__icontains=query) |
                Q(requirements__icontains=query) |
                Q(company__name__icontains=query)
            )
        if preferred_type:
            jobs = jobs.filter(job_type__icontains=preferred_type)
        if location:
            jobs = jobs.filter(location__icontains=location)
        if skills:
            jobs = jobs.filter(
                Q(title__icontains=skills) |
                Q(description__icontains=skills) |
                Q(requirements__icontains=skills) |
                Q(category__icontains=skills)
            )

        recommended_jobs = jobs.order_by('-posted_at')[:5]

        if not genai:
            error = 'Gemini package not installed. Install it with `pip install google-generativeai`.'
        else:
            api_key = os.getenv('GOOGLE_API_KEY', '')
            if not api_key:
                error = 'AI key not configured. Set GOOGLE_API_KEY in your environment.'
            else:
                genai.configure(api_key=api_key)
                model_name = os.getenv('GEMINI_MODEL', 'models/gemini-2.5-flash')

                prompt_jobs = []
                for job in recommended_jobs:
                    prompt_jobs.append(
                        f"- {job.title} at {job.company.name} in {job.location} ({job.job_type}, {job.get_category_display()})\n  Requirements: {job.requirements[:120].replace('\n', ' ')}"
                    )
                if not prompt_jobs:
                    prompt_jobs = ['No approved jobs match the current filters.']

                system_message = (
                    'You are an AI career advisor for a student job board. '
                    'Use only the provided job list when recommending jobs. '
                    'Do not invent jobs or include positions not in the list.'
                )
                user_message = (
                    f"User request: {query or 'Help me find suitable jobs.'}\n"
                    f"Preferred job type: {preferred_type or 'Any'}\n"
                    f"Location: {location or 'Any'}\n"
                    f"Skills / experience summary: {skills or 'Not specified'}\n\n"
                    'Available jobs:\n' + '\n'.join(prompt_jobs) + '\n\n'
                    'Please recommend the most suitable roles, explain why they fit, and mention the top matches by title.'
                )

                try:
                    model = genai.GenerativeModel(model_name)
                    completion = model.generate_content(user_message)
                    ai_response = completion.text.strip()
                except Exception as exc:
                    error = f'AI request failed: {exc}'

    return render(request, 'jobs/ai_assistant.html', {
        'query': query,
        'preferred_type': preferred_type,
        'location': location,
        'skills': skills,
        'ai_response': ai_response,
        'recommended_jobs': recommended_jobs,
        'error': error,
    })


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


@login_required
def dashboard(request):
    user = request.user
    try:
        profile = user.profile
        user_type = profile.user_type
    except Profile.DoesNotExist:
        user_type = 'student'

    context = {'user_type': user_type}

    if user_type == 'student':
        # 基础统计
        company_count = Company.objects.count()
        job_count = Job.objects.filter(status='approved').count()
        context.update({
            'company_count': company_count,
            'job_count': job_count,
        })

        # 热门职位（按申请数量排序，取前5）
        hot_jobs = Job.objects.filter(status='approved').annotate(
            app_count=Count('applications')
        ).order_by('-app_count')[:5]
        context['hot_jobs'] = hot_jobs
        pass

    elif user_type == 'employer':
        # 学生总数
        student_count = User.objects.filter(profile__user_type='student').count()
        context['student_count'] = student_count

        # 雇主自己发布的职位
        my_jobs = Job.objects.filter(posted_by=user)
        # 各职位的申请数量
        job_app_stats = my_jobs.annotate(app_count=Count('applications')).values('id', 'title', 'app_count')
        context['job_app_stats'] = job_app_stats

        funnel_data = []
        for job in my_jobs:
            applications = Application.objects.filter(job=job)
            submitted = applications.filter(status='submitted').count()
            reviewed = applications.filter(status='reviewed').count()
            interview = applications.filter(status='interview').count()
            accepted = applications.filter(status='accepted').count()
            funnel_data.append({
                'title': job.title,
                'submitted': submitted,
                'reviewed': reviewed,
                'interview': interview,
                'accepted': accepted,
            })
        context['funnel_data'] = funnel_data

        # 近6周申请趋势（按周统计自己职位的申请量）
        six_weeks_ago = timezone.now() - timedelta(days=42)
        weekly_apps = (
            Application.objects.filter(
                job__posted_by=user,
                applied_at__gte=six_weeks_ago
            )
            .annotate(week=TruncWeek('applied_at'))
            .values('week')
            .annotate(count=Count('id'))
            .order_by('week')
        )
        weekly_labels = [item['week'].strftime('%Y-%m-%d') for item in weekly_apps]
        weekly_data = [item['count'] for item in weekly_apps]
        context.update({
            'weekly_labels': weekly_labels,
            'weekly_data': weekly_data,
        })

    elif user_type == 'admin':
        # 基础统计
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
        })
        thirty_days_ago = timezone.now() - timedelta(days=30)
        daily_active = User.objects.filter(last_login__gte=thirty_days_ago).count()
        # 新注册用户（最近30天）
        new_users = User.objects.filter(date_joined__gte=thirty_days_ago).count()
        context['daily_active'] = daily_active
        context['new_users'] = new_users
        
        from .models import JOB_CATEGORY_CHOICES
        industry_stats = (
            Job.objects.filter(status='approved')
            .values('category')
            .annotate(count=Count('id'))
            .order_by('-count')[:6]  # 取前6个行业
        )
        # 获取类别的显示名称
        category_map = dict(JOB_CATEGORY_CHOICES)
        industry_labels = [category_map.get(item['category'], item['category']) for item in industry_stats]
        industry_data = [item['count'] for item in industry_stats]
        context['industry_labels'] = industry_labels
        context['industry_data'] = industry_data

        # 近6个月职位发布趋势
        six_months_ago = timezone.now() - timedelta(days=180)
        job_trend = (
            Job.objects.filter(posted_at__gte=six_months_ago)
            .annotate(month=TruncMonth('posted_at'))
            .values('month')
            .annotate(count=Count('id'))
            .order_by('month')
        )
        job_trend_labels = [item['month'].strftime('%Y-%m') for item in job_trend]
        job_trend_data = [item['count'] for item in job_trend]

        # 近6个月申请趋势
        app_trend = (
            Application.objects.filter(applied_at__gte=six_months_ago)
            .annotate(month=TruncMonth('applied_at'))
            .values('month')
            .annotate(count=Count('id'))
            .order_by('month')
        )
        app_trend_labels = [item['month'].strftime('%Y-%m') for item in app_trend]
        app_trend_data = [item['count'] for item in app_trend]

        # 最近5条申请（用于表格）
        recent_apps = Application.objects.select_related('student', 'job').order_by('-applied_at')[:5]

        context.update({
            'job_trend_labels': job_trend_labels,
            'job_trend_data': job_trend_data,
            'app_trend_labels': app_trend_labels,
            'app_trend_data': app_trend_data,
            'recent_apps': recent_apps,
        })
    else:
        return render(request, 'jobs/dashboard.html', {'error': 'Unknown user type'})

    return render(request, 'jobs/dashboard.html', context)