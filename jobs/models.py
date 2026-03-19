from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

# 用户类型 choices
USER_TYPE_CHOICES = (
    ('student', '学生'),
    ('employer', '雇主'),
    ('admin', '管理员'),
)

# 职位类型 choices
JOB_TYPE_CHOICES = (
    ('intern', '实习'),
    ('part-time', '兼职'),
    ('full-time', '全职'),
)

# 职位状态 choices
JOB_STATUS_CHOICES = (
    ('pending', '待审核'),
    ('approved', '已通过'),
    ('rejected', '已拒绝'),
)

# 申请状态 choices
APPLICATION_STATUS_CHOICES = (
    ('submitted', '已提交'),
    ('reviewed', '已查看'),
    ('interview', '面试中'),
    ('rejected', '已拒绝'),
    ('accepted', '已录用'),
)

class Profile(models.Model):
    """扩展用户信息"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    user_type = models.CharField(max_length=200, choices=USER_TYPE_CHOICES, default='student')
    phone = models.CharField(max_length=200, blank=True)
   

    def __str__(self):
        return self.user

class Company(models.Model):
    """公司信息（雇主关联）"""
    name = models.CharField(max_length=200, unique=True)
    description = models.TextField(blank=True)
    website = models.URLField(blank=True)
    logo = models.ImageField(upload_to='company_logos/', blank=True, null=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='companies')  # 哪个雇主创建了公司信息
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Job(models.Model):
    """职位信息"""
    title = models.CharField(max_length=200)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='jobs', null=True, blank=True)  # 关联公司
    location = models.CharField(max_length=200)
    job_type = models.CharField(max_length=20, choices=JOB_TYPE_CHOICES)
    description = models.TextField()
    requirements = models.TextField(blank=True)  # 职位要求
    salary = models.CharField(max_length=100, blank=True)  # 薪资范围，可以用CharField简单处理
    deadline = models.DateField()
    posted_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='jobs')  # 发布职位的雇主
    status = models.CharField(max_length=20, choices=JOB_STATUS_CHOICES, default='pending')
    posted_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-posted_at']

    def __str__(self):
        return self.title

    def is_expired(self):
        """判断职位是否已过截止日期"""
        return timezone.now().date() > self.deadline

class Resume(models.Model):
    """学生简历"""
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='resumes')
    title = models.CharField(max_length=200, help_text='简历名称，例如“我的实习简历”')
    file = models.FileField(upload_to='resumes/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    is_default = models.BooleanField(default=False)  # 是否为默认简历

    def __str__(self):
        return f"{self.student.username} - {self.title}"

class Application(models.Model):
    """职位申请"""
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='applications')
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='applications')
    resume = models.ForeignKey(Resume, on_delete=models.SET_NULL, null=True, blank=True)  # 申请时使用的简历
    cover_letter = models.TextField(blank=True, help_text='求职信')
    status = models.CharField(max_length=20, choices=APPLICATION_STATUS_CHOICES, default='submitted')
    applied_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('student', 'job')  # 一个学生不能重复申请同一个职位

    def __str__(self):
        return f"{self.student.username} 申请 {self.job.title}"
