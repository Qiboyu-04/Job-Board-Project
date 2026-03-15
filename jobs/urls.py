from django.urls import path
from . import views

urlpatterns = [

    path('', views.home),

    path('jobs/', views.job_list),

]