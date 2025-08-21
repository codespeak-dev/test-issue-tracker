import json
import logging
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponseForbidden
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from .models import Issue, Comment, User, Status, Settings
from .forms import LoginForm, RegisterForm, IssueForm, CommentForm, SettingsForm


logger = logging.getLogger('issues')


def log_request_response(request, response):
    """Helper to log request-response pairs"""
    log_data = {
        "method": request.method,
        "url": request.get_full_path(),
        "headers": dict(request.headers),
        "body_size": len(request.body) if hasattr(request, 'body') else 0,
        "response_status": response.status_code,
        "response_headers": dict(response.items()),
        "response_size": len(response.content) if hasattr(response, 'content') else 0,
        "timestamp": timezone.now().isoformat()
    }
    
    if response.status_code >= 400:
        log_data["response_body"] = response.content.decode('utf-8', errors='ignore')[:1000]
    
    logger.info(json.dumps(log_data))


def issue_list(request):
    """Homepage - list of all issues"""
    issues = Issue.objects.select_related('status', 'author', 'assignee').all()
    
    response = render(request, 'issues/issue_list.html', {
        'issues': issues
    })
    log_request_response(request, response)
    return response


def issue_detail(request, pk):
    """Issue detail view with comments"""
    issue = get_object_or_404(Issue.objects.select_related('status', 'author', 'assignee'), pk=pk)
    comments = issue.comments.select_related('author').all()
    
    comment_form = CommentForm() if request.user.is_authenticated else None
    
    response = render(request, 'issues/issue_detail.html', {
        'issue': issue,
        'comments': comments,
        'comment_form': comment_form
    })
    log_request_response(request, response)
    return response


@login_required
def issue_create(request):
    """Create new issue"""
    if request.method == 'POST':
        form = IssueForm(request.POST)
        if form.is_valid():
            issue = form.save(commit=False)
            issue.author = request.user
            issue.save()
            messages.success(request, 'Issue created successfully!')
            response = redirect('issue_detail', pk=issue.pk)
        else:
            response = render(request, 'issues/issue_form.html', {'form': form, 'title': 'Create Issue'})
    else:
        # Set default status to "Open"
        open_status = Status.objects.filter(name='Open').first()
        form = IssueForm(initial={'status': open_status})
        response = render(request, 'issues/issue_form.html', {'form': form, 'title': 'Create Issue'})
    
    log_request_response(request, response)
    return response


@login_required
def issue_edit(request, pk):
    """Edit existing issue"""
    issue = get_object_or_404(Issue, pk=pk)
    
    # Only author can edit issue
    if issue.author != request.user:
        response = HttpResponseForbidden("You can only edit your own issues.")
        log_request_response(request, response)
        return response
    
    if request.method == 'POST':
        form = IssueForm(request.POST, instance=issue)
        if form.is_valid():
            form.save()
            messages.success(request, 'Issue updated successfully!')
            response = redirect('issue_detail', pk=issue.pk)
        else:
            response = render(request, 'issues/issue_form.html', {
                'form': form, 
                'title': 'Edit Issue',
                'issue': issue
            })
    else:
        form = IssueForm(instance=issue)
        response = render(request, 'issues/issue_form.html', {
            'form': form, 
            'title': 'Edit Issue',
            'issue': issue
        })
    
    log_request_response(request, response)
    return response


@login_required
@require_http_methods(["DELETE"])
def issue_delete(request, pk):
    """Delete issue (AJAX endpoint)"""
    issue = get_object_or_404(Issue, pk=pk)
    
    # Only author can delete issue
    if issue.author != request.user:
        response = JsonResponse({'error': 'You can only delete your own issues.'}, status=403)
        log_request_response(request, response)
        return response
    
    issue.delete()
    messages.success(request, 'Issue deleted successfully!')
    
    response = JsonResponse({'success': True})
    log_request_response(request, response)
    return response


@login_required
def comment_create(request, issue_pk):
    """Add comment to issue"""
    issue = get_object_or_404(Issue, pk=issue_pk)
    
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.author = request.user
            comment.issue = issue
            comment.save()
            messages.success(request, 'Comment added successfully!')
        else:
            messages.error(request, 'Error adding comment.')
    
    response = redirect('issue_detail', pk=issue_pk)
    log_request_response(request, response)
    return response


@login_required
def comment_edit(request, pk):
    """Edit comment (AJAX endpoint)"""
    comment = get_object_or_404(Comment, pk=pk)
    
    # Only author can edit comment
    if comment.author != request.user:
        response = JsonResponse({'error': 'You can only edit your own comments.'}, status=403)
        log_request_response(request, response)
        return response
    
    if request.method == 'POST':
        form = CommentForm(request.POST, instance=comment)
        if form.is_valid():
            form.save()
            response = JsonResponse({
                'success': True, 
                'content_html': comment.content_html(),
                'updated_at': comment.updated_at.strftime('%Y-%m-%d %H:%M')
            })
        else:
            response = JsonResponse({'error': 'Invalid data'}, status=400)
    else:
        response = JsonResponse({'content': comment.content})
    
    log_request_response(request, response)
    return response


def login_view(request):
    """Login page"""
    if request.user.is_authenticated:
        return redirect('issue_list')
    
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            user = User.objects.get(email=email)
            login(request, user)
            messages.success(request, f'Welcome back, {user.name}!')
            response = redirect('issue_list')
        else:
            response = render(request, 'registration/login.html', {'form': form})
    else:
        form = LoginForm()
        response = render(request, 'registration/login.html', {'form': form})
    
    log_request_response(request, response)
    return response


def register_view(request):
    """Registration page"""
    if request.user.is_authenticated:
        return redirect('issue_list')
    
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'Welcome, {user.name}! Your account has been created.')
            response = redirect('issue_list')
        else:
            response = render(request, 'registration/register.html', {'form': form})
    else:
        form = RegisterForm()
        response = render(request, 'registration/register.html', {'form': form})
    
    log_request_response(request, response)
    return response


def logout_view(request):
    """Logout and redirect to homepage"""
    if request.user.is_authenticated:
        messages.success(request, 'You have been logged out successfully.')
        logout(request)
    
    response = redirect('issue_list')
    log_request_response(request, response)
    return response


@login_required
def settings_view(request):
    """Application settings page (admin only)"""
    if not request.user.is_staff:
        response = HttpResponseForbidden("Only staff members can access settings.")
        log_request_response(request, response)
        return response
    
    settings_obj = Settings.load()
    
    if request.method == 'POST':
        form = SettingsForm(request.POST, instance=settings_obj)
        if form.is_valid():
            form.save()
            messages.success(request, 'Settings updated successfully!')
            response = redirect('settings')
        else:
            response = render(request, 'issues/settings.html', {'form': form})
    else:
        form = SettingsForm(instance=settings_obj)
        response = render(request, 'issues/settings.html', {'form': form})
    
    log_request_response(request, response)
    return response