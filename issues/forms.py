from django import forms
from django.contrib.auth import authenticate
from django.core.exceptions import ValidationError
from .models import User, Issue, Comment, Settings


class LoginForm(forms.Form):
    """Form for email-based login"""
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500',
            'placeholder': 'Enter your email'
        })
    )
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if not User.objects.filter(email=email).exists():
            raise ValidationError("No account found with this email. Please register first.")
        return email


class RegisterForm(forms.ModelForm):
    """Form for user registration"""
    
    class Meta:
        model = User
        fields = ['name', 'email']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500',
                'placeholder': 'Enter your full name'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500',
                'placeholder': 'Enter your email'
            }),
        }
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError("An account with this email already exists. Please login instead.")
        return email


class IssueForm(forms.ModelForm):
    """Form for creating and editing issues"""
    
    class Meta:
        model = Issue
        fields = ['summary', 'description', 'status', 'assignee']
        widgets = {
            'summary': forms.TextInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500',
                'placeholder': 'Brief summary of the issue'
            }),
            'description': forms.Textarea(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500',
                'rows': 6,
                'placeholder': 'Detailed description (Markdown supported)'
            }),
            'status': forms.Select(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500'
            }),
            'assignee': forms.Select(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make assignee optional
        self.fields['assignee'].empty_label = "Unassigned"
        self.fields['assignee'].required = False


class CommentForm(forms.ModelForm):
    """Form for creating and editing comments"""
    
    class Meta:
        model = Comment
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500',
                'rows': 4,
                'placeholder': 'Add a comment (Markdown supported)'
            }),
        }


class SettingsForm(forms.ModelForm):
    """Form for application settings"""
    
    class Meta:
        model = Settings
        fields = [
            'slack_bot_token', 'slack_channel_id',
            'github_access_token', 'github_repository_owner', 'github_repository_name'
        ]
        widgets = {
            'slack_bot_token': forms.PasswordInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500',
                'placeholder': 'xoxb-...'
            }),
            'slack_channel_id': forms.TextInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500',
                'placeholder': 'Channel ID or URL'
            }),
            'github_access_token': forms.PasswordInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500',
                'placeholder': 'ghp_...'
            }),
            'github_repository_owner': forms.TextInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500',
                'placeholder': 'owner/organization'
            }),
            'github_repository_name': forms.TextInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500',
                'placeholder': 'repository-name'
            }),
        }
        labels = {
            'slack_bot_token': 'Slack Bot Token',
            'slack_channel_id': 'Slack Channel ID',
            'github_access_token': 'GitHub Access Token',
            'github_repository_owner': 'GitHub Repository Owner',
            'github_repository_name': 'GitHub Repository Name',
        }