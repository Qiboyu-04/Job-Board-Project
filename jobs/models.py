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

JOB_CATEGORY_CHOICES = (
    ('accounting', 'Accounting'),
    ('agriculture_fishing_forestry', 'Agriculture, fishing & forestry'),
    ('architecture', 'Architecture'),
    ('automotive', 'Automotive'),
    ('banking_finance_insurance', 'Banking, finance & insurance'),
    ('construction_roading', 'Construction & roading'),
    ('customer_service', 'Customer service'),
    ('education', 'Education'),
    ('engineering', 'Engineering'),
    ('executive_general_management', 'Executive & general management'),
    ('government_council', 'Government & council'),
    ('healthcare', 'Healthcare'),
    ('hospitality_tourism', 'Hospitality & tourism'),
    ('hr_recruitment', 'HR & recruitment'),
    ('it', 'IT'),
    ('legal', 'Legal'),
    ('manufacturing_operations', 'Manufacturing & operations'),
    ('marketing_media_communications', 'Marketing, media & communications'),
    ('office_administration', 'Office & administration'),
    ('property', 'Property'),
    ('retail', 'Retail'),
    ('sales', 'Sales'),
    ('science_technology', 'Science & technology'),
    ('trades_services', 'Trades & services'),
    ('transport_logistics', 'Transport & logistics'),
    ('other', 'Other'),
)

EDUCATION_LEVEL_CHOICES = (
    ('middle_school', 'Middle School'),
    ('high_school', 'High School'),
    ('vocational_high_school', 'Vocational High School'),
    ('junior_college', 'Junior College'),
    ('bachelor', 'Bachelor'),
    ('master', 'Master'),
    ('doctorate', 'Doctorate'),
    ('other', 'Other'),
)

EXPERIENCE_UNIT_CHOICES = (
    ('months', 'Months'),
    ('years', 'Years'),
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
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile',
        verbose_name='User'
    )
    user_type = models.CharField(
        max_length=20,
        choices=USER_TYPE_CHOICES,
        default='student',
        verbose_name='User Type'
    )
    phone = models.CharField(
        max_length=20,
        blank=True,
        verbose_name='Phone Number'
    )

    class Meta:
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'

    def __str__(self):
        return f"{self.user.username} - {self.get_user_type_display()}"

class Company(models.Model):
    name = models.CharField(
        max_length=200,
        unique=True,
        verbose_name='Company Name'
    )
    description = models.TextField(
        blank=True,
        verbose_name='Company Description'
    )
    website = models.URLField(
        blank=True,
        verbose_name='Company Website'
    )
    logo = models.ImageField(
        upload_to='company_logos/',
        blank=True,
        null=True,
        verbose_name='Company Logo'
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='companies',
        verbose_name='Created By'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Created At'
    )

    class Meta:
        verbose_name = 'Company'
        verbose_name_plural = 'Companies'
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['created_by']),
        ]

    def __str__(self):
        return self.name
    
class Job(models.Model):
    title = models.CharField(
        max_length=200,
        verbose_name='Job Title'
    )
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='jobs',
        verbose_name='Company'
    )
    location = models.CharField(
        max_length=200,
        verbose_name='Location'
    )
    job_type = models.CharField(
        max_length=20,
        choices=JOB_TYPE_CHOICES,
        verbose_name='Job Type'
    )
    category = models.CharField(
        max_length=50,
        choices=JOB_CATEGORY_CHOICES,
        default='other',
        verbose_name='Category'
    )
    description = models.TextField(
        verbose_name='Job Description'
    )
    requirements = models.TextField(
        blank=True,
        verbose_name='Requirements'
    )
    salary = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Salary Range'
    )
    deadline = models.DateField(
        verbose_name='Application Deadline'
    )
    posted_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='jobs',
        verbose_name='Posted By'
    )
    status = models.CharField(
        max_length=20,
        choices=JOB_STATUS_CHOICES,
        default='pending',
        verbose_name='Review Status'
    )
    posted_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Posted At'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Updated At'
    )

    class Meta:
        verbose_name = 'Job'
        verbose_name_plural = 'Jobs'
        ordering = ['-posted_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['posted_at']),
            models.Index(fields=['company']),
            models.Index(fields=['posted_by']),
            models.Index(fields=['category']),
            models.Index(fields=['-posted_at']),
        ]

    def __str__(self):
        return self.title

    def is_expired(self):
        """Check if the job posting has passed its deadline"""
        return timezone.now().date() > self.deadline
    is_expired.boolean = True
    is_expired.short_description = 'Expired'

class Resume(models.Model):
    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='resumes',
        verbose_name='Student'
    )
    title = models.CharField(
        max_length=200,
        help_text='Resume title, e.g., "My Internship Resume"',
        verbose_name='Resume Title'
    )
    file = models.FileField(
        upload_to='resumes/',
        verbose_name='Resume File'
    )
    uploaded_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Uploaded At'
    )
    is_default = models.BooleanField(
        default=False,
        verbose_name='Set as Default'
    )

    class Meta:
        verbose_name = 'Resume'
        verbose_name_plural = 'Resumes'
        indexes = [
            models.Index(fields=['student']),
            models.Index(fields=['is_default']),
        ]

    def __str__(self):
        return f"{self.student.username} - {self.title}"
    
class Application(models.Model):
    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='applications',
        verbose_name='Student'
    )
    job = models.ForeignKey(
        Job,
        on_delete=models.CASCADE,
        related_name='applications',
        verbose_name='Job'
    )
    resume = models.ForeignKey(
        Resume,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Resume Used'
    )
    education_level = models.CharField(
        max_length=30,
        choices=EDUCATION_LEVEL_CHOICES,
        blank=True,
        verbose_name='Education Level'
    )
    experience_value = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name='Work Experience'
    )
    experience_unit = models.CharField(
        max_length=10,
        choices=EXPERIENCE_UNIT_CHOICES,
        default='years',
        verbose_name='Experience Unit'
    )
    cover_letter = models.TextField(
        blank=True,
        help_text='Cover Letter',
        verbose_name='Cover Letter'
    )
    status = models.CharField(
        max_length=20,
        choices=APPLICATION_STATUS_CHOICES,
        default='submitted',
        verbose_name='Application Status'
    )
    applied_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Applied At'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Updated At'
    )

    class Meta:
        verbose_name = 'Job Application'
        verbose_name_plural = 'Job Applications'
        unique_together = ('student', 'job')
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['applied_at']),
            models.Index(fields=['student', 'job']),
        ]

    def __str__(self):
        return f"{self.student.username} applied for {self.job.title}"

    def can_be_cancelled(self):
        """Check if the application can be cancelled (only when status is 'submitted')"""
        return self.status == 'submitted'
    can_be_cancelled.boolean = True
    can_be_cancelled.short_description = 'Cancellable'




class SavedJob(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    job = models.ForeignKey(Job, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('user', 'job')

    def __str__(self):
        return f"{self.user.username} saved {self.job.title}"


# Notification types
NOTIFICATION_TYPE_CHOICES = (
    ('application_received', 'Application Received'),
    ('application_reviewed', 'Application Reviewed'),
    ('application_interview', 'Interview Invitation'),
    ('application_accepted', 'Application Accepted'),
    ('application_rejected', 'Application Rejected'),
)


class Notification(models.Model):
    # Recipient can be student or employer
    recipient = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notifications',
        verbose_name='Recipient'
    )
    application = models.ForeignKey(
        Application,
        on_delete=models.CASCADE,
        related_name='notifications',
        verbose_name='Application',
        null=True,
        blank=True
    )
    notification_type = models.CharField(
        max_length=30,
        choices=NOTIFICATION_TYPE_CHOICES,
        verbose_name='Notification Type'
    )
    title = models.CharField(
        max_length=200,
        verbose_name='Title'
    )
    message = models.TextField(
        verbose_name='Message'
    )
    is_read = models.BooleanField(
        default=False,
        verbose_name='Is Read'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Created At'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Updated At'
    )

    class Meta:
        verbose_name = 'Notification'
        verbose_name_plural = 'Notifications'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient', '-created_at']),
            models.Index(fields=['is_read']),
            models.Index(fields=['notification_type']),
        ]

    def __str__(self):
        return f"{self.title} - {self.recipient.username}"