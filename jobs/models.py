from django.db import models

from django.contrib.auth.models import User
from django.utils import timezone

USER_TYPE_CHOICES = (
    ('student', 'student'),
    ('employer', 'employer'),
    ('admin', 'admin'),
)


JOB_TYPE_CHOICES = (
    ('intern', 'intern'),
    ('part-time', 'part-time'),
    ('full-time', 'full-time'),
)


JOB_STATUS_CHOICES = (
    ('pending', 'pending'),
    ('approved', 'approved'),
    ('rejected', 'rejected'),
)


APPLICATION_STATUS_CHOICES = (
    ('submitted', 'submitted'),
    ('reviewed', 'reviewed'),
    ('interview', 'interview'),
    ('rejected', 'rejected'),
    ('accepted', 'accepted'),
)

class Profile(models.Model):
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    user_type = models.CharField(max_length=200, choices=USER_TYPE_CHOICES, default='student')
    phone = models.CharField(max_length=200, blank=True)
   

    def __str__(self):
        return self.user

class Company(models.Model):
   
    name = models.CharField(max_length=200, unique=True)
    description = models.TextField(blank=True)
    website = models.URLField(blank=True)
    logo = models.ImageField(upload_to='company_logos/', blank=True, null=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='companies')  
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Job(models.Model):
   
    title = models.CharField(max_length=200)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='jobs', null=True, blank=True)  # 关联公司
    location = models.CharField(max_length=200)
    job_type = models.CharField(max_length=20, choices=JOB_TYPE_CHOICES)
    description = models.TextField()
    requirements = models.TextField(blank=True)  
    salary = models.CharField(max_length=100, blank=True)  
    deadline = models.DateField()
    posted_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='jobs') 
    status = models.CharField(max_length=20, choices=JOB_STATUS_CHOICES, default='pending')
    posted_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-posted_at']

    def __str__(self):
        return self.title

    def is_expired(self):
        
        return timezone.now().date() > self.deadline

class Resume(models.Model):
    
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='resumes')
    title = models.CharField(max_length=200, help_text='Resume Name')
    file = models.FileField(upload_to='resumes/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    is_default = models.BooleanField(default=False)  
    def __str__(self):
        return f"{self.student.username} - {self.title}"

class Application(models.Model):
   
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='applications')
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='applications')
    resume = models.ForeignKey(Resume, on_delete=models.SET_NULL, null=True, blank=True)  
    cover_letter = models.TextField(blank=True, help_text='Cover Letter')
    status = models.CharField(max_length=20, choices=APPLICATION_STATUS_CHOICES, default='submitted')
    applied_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('student', 'job') 

    def __str__(self):
        return f"{self.student.username} Apply {self.job.title}"




