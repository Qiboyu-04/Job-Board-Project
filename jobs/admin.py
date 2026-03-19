from django.contrib import admin
from .models import Profile, Company, Job, Resume, Application 

admin.site.register(Profile)
admin.site.register(Company)
admin.site.register(Job)
admin.site.register(Resume)
admin.site.register(Application)
