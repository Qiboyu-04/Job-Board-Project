from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from .models import Application, Profile

class ApplicationForm(forms.ModelForm):
    resume_title = forms.CharField(
        max_length=200,
        required=False,
        label='Resume title',
        help_text='Optional title for the resume file, e.g. "My Internship Resume"'
    )
    resume_file = forms.FileField(
        required=False,
        label='Upload resume',
        help_text='Upload your resume file (PDF, DOCX, etc.)'
    )

    class Meta:
        model = Application
        fields = ['cover_letter']


# User registration form
class UserRegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)
    user_type = forms.ChoiceField(choices=Profile._meta.get_field('user_type').choices)

    class Meta:
        model = User
        fields = ['username', 'email', 'user_type', 'password1', 'password2']

    def save(self, commit=True):
        user = super().save(commit=commit)
        user_type = self.cleaned_data['user_type']

        profile, _ = Profile.objects.get_or_create(user=user)
        profile.user_type = user_type
        profile.save()

        return user


# User login form
class UserLoginForm(AuthenticationForm):
    username = forms.CharField(max_length=150)
    password = forms.CharField(widget=forms.PasswordInput)