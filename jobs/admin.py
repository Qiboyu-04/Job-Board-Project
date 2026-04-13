from django.contrib import admin
from django.contrib.auth import get_user_model
from .models import Profile, Company, Job, Resume, Application

User = get_user_model()

# ---------- JobAdmin ----------
class JobAdmin(admin.ModelAdmin):
    list_display = ('title', 'company', 'location', 'status', 'posted_at')
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        elif request.user.is_staff:
            try:
                company = Company.objects.get(user=request.user)
                return qs.filter(company=company)
            except Company.DoesNotExist:
                return qs.none()
        return qs.none()

    def has_change_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        if obj is None:
            return True
        return obj.company and obj.company.user == request.user

    def has_delete_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        if obj is None:
            return True
        return obj.company and obj.company.user == request.user

    def has_add_permission(self, request):
        return request.user.is_superuser or request.user.is_staff

    def save_model(self, request, obj, form, change):
        if request.user.is_staff and not request.user.is_superuser:
            try:
                company = Company.objects.get(user=request.user)
                obj.company = company
                obj.posted_by = request.user
            except Company.DoesNotExist:
                pass
        super().save_model(request, obj, form, change)

    def get_readonly_fields(self, request, obj=None):
        ro_fields = []
        if request.user.is_staff and not request.user.is_superuser:
            ro_fields.append('company')
        return ro_fields

# ---------- ApplicationAdmin ----------
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ('job', 'get_student', 'status', 'applied_at')

    def get_student(self, obj):
        return obj.student.username
    get_student.short_description = 'Applicant'

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        elif request.user.is_staff:
            try:
                company = Company.objects.get(user=request.user)
                return qs.filter(job__company=company)
            except Company.DoesNotExist:
                return qs.none()
        return qs.none()

# ---------- ResumeAdmin ----------
class ResumeAdmin(admin.ModelAdmin):
    list_display = ('get_student', 'title', 'uploaded_at', 'is_default')

    def get_student(self, obj):
        return obj.student.username
    get_student.short_description = 'Student'

    def get_queryset(self, request):
        if request.user.is_superuser:
            return super().get_queryset(request)
        # staff 不允许查看 Resume
        return Resume.objects.none()

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

# ---------- 注册 Admin ----------
admin.site.register(Job, JobAdmin)
admin.site.register(Application, ApplicationAdmin)
admin.site.register(Resume, ResumeAdmin)
admin.site.register(Profile, ProfileAdmin)
admin.site.register(Company, CompanyAdmin)