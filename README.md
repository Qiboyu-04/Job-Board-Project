pip install -r requirements.txt

二、各部分作用（非常重要）

1 项目主文件夹
student_job_board/

这是 整个 Django 项目核心配置目录。

里面包含：

文件	        作用
settings.py	    项目配置
urls.py	        网站总路由
asgi.py	        异步服务器
wsgi.py	        部署服务器

2 App：jobs
jobs/

这是你创建的 网站功能模块（App）。

这个 App 负责：

Job Listings
Job Database
Web Pages

里面重要文件：

文件	        作用
models.py	    数据库模型
views.py	    网站逻辑
urls.py	        页面路由
admin.py	    后台管理
migrations	    数据库迁移

三、HTML 页面结构

网页文件在：

jobs/templates/jobs/

里面有三个页面：

1 base.html
网站基础模板

作用：

统一网站布局

例如：

Header
Navigation
Footer

其他页面会继承它：

{% extends "jobs/base.html" %}
2 home.html

首页：

http://127.0.0.1:8000/

内容：

Welcome page
Browse jobs button
3 job_list.html

职位列表页面：

http://127.0.0.1:8000/jobs/

功能：

显示所有职位

代码核心：

{% for job in jobs %}

循环数据库里的职位。

四、数据库结构

数据库定义在：

jobs/models.py

核心代码：

class Job(models.Model):

    title = models.CharField(max_length=200)
    company = models.CharField(max_length=200)
    location = models.CharField(max_length=200)
    job_type = models.CharField(max_length=100)
    description = models.TextField()
    deadline = models.DateField()

数据库表：

jobs_job

字段：

字段	    作用
title	    职位名称
company	    公司
location	地点
job_type	类型
description	描述
deadline	截止日期

五、View 逻辑

在：

jobs/views.py

两个核心函数：

首页
def home(request):
    return render(request, "jobs/home.html")
职位列表
def job_list(request):

    jobs = Job.objects.all()

    return render(request, "jobs/job_list.html", {
        "jobs": jobs
    })

功能：

从数据库读取所有职位
发送到 HTML 页面

六、URL 系统

Django 有 两层 URL。

1 主 URL

文件：

student_job_board/urls.py

代码：

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('jobs.urls')),
]

意思：

普通页面交给 jobs app
2 App URL

文件：

jobs/urls.py

代码：

urlpatterns = [

    path('', views.home),

    path('jobs/', views.job_list),

]

对应网址：

URL	页面
/	home
/jobs/	job listing

七、管理后台

在：

jobs/admin.py

注册模型：

admin.site.register(Job)

访问后台：

http://127.0.0.1:8000/admin

可以：

添加职位
删除职位
管理数据
八、项目运行入口

文件：

manage.py

运行服务器：

python manage.py runserver

启动网站：

<<<<<<< HEAD
http://127.0.0.1:8000





python manage.py makemigrations jobs
python manage.py migrate
python manage.py runserver
=======
http://127.0.0.1:8000
>>>>>>> 9207b38e67297427b0ec351de4fd09ed3e228070
