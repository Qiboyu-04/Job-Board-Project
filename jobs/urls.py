from django.urls import path
from . import views

from django.conf import settings
from django.conf.urls.static import static



urlpatterns = [

    path('', views.home),

    path('jobs/', views.job_list),

    path('jobs/<int:job_id>/', views.job_detail, name='job_detail'),

    path('jobs/<int:job_id>/apply/', views.apply_job, name='apply_job'),

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
