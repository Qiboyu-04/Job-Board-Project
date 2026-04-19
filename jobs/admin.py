from django.contrib import admin
from django.contrib.auth import get_user_model
from django.utils.html import format_html
from .models import Profile, Company, Job, Resume, Application, Notification

User = get_user_model()

# ---------- JobAdmin ----------
class JobAdmin(admin.ModelAdmin):
    list_display = ('title', 'company', 'job_type', 'category', 'status', 'posted_at', 'deadline', 'is_within_deadline')
    list_filter = ('status', 'job_type', 'category', 'company', 'posted_at')
    search_fields = ('title', 'description', 'company__name', 'location')
    date_hierarchy = 'posted_at'
    readonly_fields = ('posted_at', 'updated_at', 'posted_by')
    fieldsets = (
        ('Basic Info', {'fields': ('title', 'company', 'location', 'job_type', 'category')}),
        ('Details', {'fields': ('description', 'requirements', 'salary')}),
        ('Status & Time', {'fields': ('status', 'deadline', 'posted_by', 'posted_at', 'updated_at')}),
    )
    actions = ['approve_jobs', 'reject_jobs']

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        # Only show jobs from the current user's company
        user_companies = Company.objects.filter(created_by=request.user)
        return qs.filter(company__in=user_companies)

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        # For non-superuser employers, restrict company choices to their own company
        if not request.user.is_superuser:
            user_companies = Company.objects.filter(created_by=request.user)
            form.base_fields['company'].queryset = user_companies
        return form

    def save_model(self, request, obj, form, change):
        # Auto-set posted_by to current user
        if not change:  # When creating a new job
            obj.posted_by = request.user
            # If user is not superuser, set company to their company
            if not request.user.is_superuser:
                company, _ = Company.objects.get_or_create(
                    created_by=request.user,
                    defaults={'name': f"{request.user.username}'s Company"}
                )
                obj.company = company
        super().save_model(request, obj, form, change)

    def is_within_deadline(self, obj):
        return not obj.is_expired()
    is_within_deadline.boolean = True
    is_within_deadline.short_description = 'Deadline Active'

    def has_change_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        if obj is None:
            return True
        # Check if job belongs to user's company
        user_companies = Company.objects.filter(created_by=request.user)
        return obj.company in user_companies

    def has_delete_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        if obj is None:
            return True
        # Check if job belongs to user's company
        user_companies = Company.objects.filter(created_by=request.user)
        return obj.company in user_companies

    def approve_jobs(self, request, queryset):
        queryset.update(status='approved')
        self.message_user(request, f"Approved {queryset.count()} job(s).")
    approve_jobs.short_description = "Approve selected jobs"

    def reject_jobs(self, request, queryset):
        queryset.update(status='rejected')
        self.message_user(request, f"Rejected {queryset.count()} job(s).")
    reject_jobs.short_description = "Reject selected jobs"


# ---------- ApplicationAdmin ----------
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ('student', 'job', 'status', 'applied_at', 'can_be_cancelled')
    list_filter = ('status', 'applied_at')
    search_fields = ('student__username', 'job__title', 'cover_letter')
    date_hierarchy = 'applied_at'
    readonly_fields = ('applied_at', 'updated_at')
    fieldsets = (
        ('Application Info', {'fields': ('student', 'job', 'resume', 'cover_letter')}),
        ('Status & Time', {'fields': ('status', 'applied_at', 'updated_at')}),
    )
    actions = ['mark_as_reviewed', 'mark_as_interview', 'mark_as_accepted']

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(job__posted_by=request.user)

    def has_change_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        if obj is None:
            return True
        return obj.job.posted_by == request.user

    def has_delete_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        if obj is None:
            return True
        return obj.job.posted_by == request.user

    def mark_as_reviewed(self, request, queryset):
        queryset.update(status='reviewed')
        self.message_user(request, f"Marked {queryset.count()} application(s) as reviewed.")
    mark_as_reviewed.short_description = "Mark as reviewed"

    def mark_as_interview(self, request, queryset):
        queryset.update(status='interview')
        self.message_user(request, f"Marked {queryset.count()} application(s) as interview.")
    mark_as_interview.short_description = "Mark as interview"

    def mark_as_accepted(self, request, queryset):
        queryset.update(status='accepted')
        self.message_user(request, f"Marked {queryset.count()} application(s) as accepted.")
    mark_as_accepted.short_description = "Mark as accepted"

# ---------- ResumeAdmin ----------
class ResumeAdmin(admin.ModelAdmin):
    list_display = ('student', 'title', 'uploaded_at', 'is_default', 'file_link')
    list_filter = ('is_default', 'uploaded_at')
    search_fields = ('student__username', 'title')
    readonly_fields = ('uploaded_at',)

    def file_link(self, obj):
        if obj.file:
            return format_html('<a href="{}" target="_blank">Download</a>', obj.file.url)
        return "No file"
    file_link.short_description = 'Resume File'

# ---------- ProfileAdmin ----------
class ProfileAdmin(admin.ModelAdmin):
    def get_queryset(self, request):
        if request.user.is_superuser:
            return super().get_queryset(request)
        return Profile.objects.none()

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_add_permission(self, request):
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser

# ---------- CompanyAdmin ----------
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_by', 'created_at')

    def get_queryset(self, request):
        if request.user.is_superuser:
            return super().get_queryset(request)
        return Company.objects.none()  # staff 不显示

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_add_permission(self, request):
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser

# ---------- NotificationAdmin ----------
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('recipient', 'notification_type', 'title', 'is_read', 'created_at')
    list_filter = ('is_read', 'notification_type', 'created_at')
    search_fields = ('recipient__username', 'title', 'message')
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'created_at'
    fieldsets = (
        ('Info', {'fields': ('recipient', 'notification_type', 'title', 'message')}),
        ('Status', {'fields': ('is_read', 'application')}),
        ('Time', {'fields': ('created_at', 'updated_at')}),
    )

    def has_add_permission(self, request):
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


# ---------- 注册 Admin ----------
admin.site.register(Job, JobAdmin)
admin.site.register(Application, ApplicationAdmin)
admin.site.register(Resume, ResumeAdmin)
admin.site.register(Profile, ProfileAdmin)
admin.site.register(Company, CompanyAdmin)
admin.site.register(Notification, NotificationAdmin)