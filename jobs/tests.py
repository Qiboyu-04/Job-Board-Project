from django.test import TestCase
from django.contrib.auth.models import User
from datetime import date, timedelta
from .models import Job, Application


class JobModelTest(TestCase):
    def test_create_job(self):
        user = User.objects.create_user(
            username="jobcreator",
            password="123456"
        )
        job = Job.objects.create(
            title="Test Job",
            location="Test City",
            job_type="full-time",
            deadline=date.today() + timedelta(days=7),
            posted_by=user
        )
        self.assertEqual(job.title, "Test Job")
        self.assertEqual(job.location, "Test City")
        self.assertEqual(job.job_type, "full-time")


class ApplicationTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            password="123456"
        )
        self.job = Job.objects.create(
            title="Test Job",
            location="Test City",
            job_type="full-time",
            deadline=date.today() + timedelta(days=7),
            posted_by=self.user
        )

    def test_apply_job(self):
        app = Application.objects.create(
            student=self.user,
            job=self.job,
            cover_letter="I want this job"
        )

        self.assertEqual(app.student.username, "testuser")
        self.assertEqual(app.job.title, "Test Job")
        self.assertEqual(app.cover_letter, "I want this job")


class JobSearchTest(TestCase):
    def setUp(self):
        user = User.objects.create_user(
            username="searchuser",
            password="123456"
        )
        Job.objects.create(
            title="Teacher",
            location="School",
            job_type="full-time",
            deadline=date.today() + timedelta(days=7),
            posted_by=user
        )
        Job.objects.create(
            title="Engineer",
            location="City",
            job_type="part-time",
            deadline=date.today() + timedelta(days=10),
            posted_by=user
        )

    def test_search_by_title(self):
        results = Job.objects.filter(title__icontains="Teacher")
        self.assertEqual(results.count(), 1)

    def test_filter_by_type(self):
        results = Job.objects.filter(job_type="full-time")
        self.assertEqual(results.count(), 1)