pip install -r requirements.txt

秋假更新后网站功能：

1.修复了先前admin端公司无法正常看到自己发布的工作的问题

2.增加了admin端的筛选和增加批量通过和拒绝

3.增加了admin中查看deadline是否已经过期

4.修复了上面2，3的小问题

5.修改了未登录无法查看工作细节的前端小问题

6.增加了工作种类（categories），现在前端岗位筛选和admin端工作发布可以选择工作种类

7.增加了通知页面，现在学生端发布申请和公司端改变申请状态都会收到信息，可查看申请进度。

8.修改了你现在看到的readme...QAQ

启动网站：

<<<<<<< HEAD
http://127.0.0.1:8000





python manage.py makemigrations jobs
python manage.py migrate
python manage.py runserver
=======
http://127.0.0.1:8000
>>>>>>> 9207b38e67297427b0ec351de4fd09ed3e228070
