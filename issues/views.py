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
from django.db.models import Q
from .models import Issue, Comment, User, Status, Settings, Tag, IssueEditHistory
from .forms import LoginForm, RegisterForm, IssueForm, CommentForm, SettingsForm, TagForm


logger = logging.getLogger('issues')


def log_request_response(request, response):
    """Helper to log request-response pairs"""
    # Safely get body size without causing RawPostDataException
    body_size = 0
    try:
        if hasattr(request, 'body'):
            body_size = len(request.body)
    except Exception:
        # If body has been consumed (e.g., by form processing), we can't access it
        body_size = 0
    
    log_data = {
        "method": request.method,
        "url": request.get_full_path(),
        "headers": dict(request.headers),
        "body_size": body_size,
        "response_status": response.status_code,
        "response_headers": dict(response.items()),
        "response_size": len(response.content) if hasattr(response, 'content') else 0,
        "timestamp": timezone.now().isoformat()
    }
    
    if response.status_code >= 400:
        log_data["response_body"] = response.content.decode('utf-8', errors='ignore')[:1000]
    
    logger.info(json.dumps(log_data))


def issue_list(request):
    """Homepage - list of all issues with optional search and tag filtering"""
    issues = Issue.objects.select_related('status', 'author', 'assignee').prefetch_related('tags').all()
    search_query = request.GET.get('search', '').strip()
    selected_tags = request.GET.getlist('tags')
    
    if search_query:
        # Filter issues by search term in summary or description (case-insensitive)
        issues = issues.filter(
            Q(summary__icontains=search_query) | 
            Q(description__icontains=search_query)
        )
    
    if selected_tags:
        # Filter issues by selected tags (OR logic - issues that have at least one of the selected tags)
        issues = issues.filter(tags__id__in=selected_tags).distinct()
    
    # Get all tags for the filter dropdown
    all_tags = Tag.objects.all()
    
    response = render(request, 'issues/issue_list.html', {
        'issues': issues,
        'search_query': search_query,
        'selected_tags': selected_tags,
        'all_tags': all_tags,
    })
    log_request_response(request, response)
    return response


def issue_detail(request, pk):
    """Issue detail view with comments"""
    # Use with_deleted to show deleted issues too (but they will be marked as such)
    issue = get_object_or_404(Issue.objects.with_deleted().select_related('status', 'author', 'assignee').prefetch_related('tags'), pk=pk)
    comments = issue.comments.select_related('author').all()
    edit_history = issue.edit_history.select_related('editor').all()[:10]  # Show last 10 edits
    
    comment_form = CommentForm() if request.user.is_authenticated else None
    
    response = render(request, 'issues/issue_detail.html', {
        'issue': issue,
        'comments': comments,
        'comment_form': comment_form,
        'edit_history': edit_history
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
    """Edit existing issue - anyone can edit"""
    # Use with_deleted to allow editing deleted issues too
    issue = get_object_or_404(Issue.objects.with_deleted(), pk=pk)
    
    if request.method == 'POST':
        form = IssueForm(request.POST, instance=issue)
        if form.is_valid():
            # Track changes before saving
            track_issue_changes(issue, form, request.user)
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
    """Soft delete issue (AJAX endpoint)"""
    issue = get_object_or_404(Issue, pk=pk)
    
    # Only author can delete issue
    if issue.author != request.user:
        response = JsonResponse({'error': 'You can only delete your own issues.'}, status=403)
        log_request_response(request, response)
        return response
    
    issue.soft_delete()
    messages.success(request, 'Issue deleted successfully!')
    
    response = JsonResponse({'success': True})
    log_request_response(request, response)
    return response


@login_required
@require_http_methods(["POST"])
def issue_restore(request, pk):
    """Restore soft-deleted issue (AJAX endpoint)"""
    issue = get_object_or_404(Issue.objects.deleted_only(), pk=pk)
    
    # Only author can restore issue
    if issue.author != request.user:
        response = JsonResponse({'error': 'You can only restore your own issues.'}, status=403)
        log_request_response(request, response)
        return response
    
    issue.restore()
    messages.success(request, 'Issue restored successfully!')
    
    response = JsonResponse({'success': True})
    log_request_response(request, response)
    return response


@login_required
def comment_create(request, issue_pk):
    """Add comment to issue"""
    issue = get_object_or_404(Issue.objects.with_deleted(), pk=issue_pk)
    
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


@login_required
def tag_list(request):
    """List all tags"""
    tags = Tag.objects.all()
    
    response = render(request, 'issues/tag_list.html', {
        'tags': tags
    })
    log_request_response(request, response)
    return response


@login_required
def tag_create(request):
    """Create new tag"""
    if request.method == 'POST':
        form = TagForm(request.POST)
        if form.is_valid():
            tag = form.save()
            messages.success(request, f'Tag "{tag.name}" created successfully!')
            response = redirect('tag_list')
        else:
            response = render(request, 'issues/tag_form.html', {'form': form, 'title': 'Create Tag'})
    else:
        form = TagForm()
        response = render(request, 'issues/tag_form.html', {'form': form, 'title': 'Create Tag'})
    
    log_request_response(request, response)
    return response


@login_required
def tag_edit(request, pk):
    """Edit existing tag"""
    tag = get_object_or_404(Tag, pk=pk)
    
    if request.method == 'POST':
        form = TagForm(request.POST, instance=tag)
        if form.is_valid():
            form.save()
            messages.success(request, f'Tag "{tag.name}" updated successfully!')
            response = redirect('tag_list')
        else:
            response = render(request, 'issues/tag_form.html', {
                'form': form, 
                'title': 'Edit Tag',
                'tag': tag
            })
    else:
        form = TagForm(instance=tag)
        response = render(request, 'issues/tag_form.html', {
            'form': form, 
            'title': 'Edit Tag',
            'tag': tag
        })
    
    log_request_response(request, response)
    return response


@login_required
@require_http_methods(["DELETE"])
def tag_delete(request, pk):
    """Delete tag (AJAX endpoint)"""
    tag = get_object_or_404(Tag, pk=pk)
    
    tag_name = tag.name
    tag.delete()
    messages.success(request, f'Tag "{tag_name}" deleted successfully!')
    
    response = JsonResponse({'success': True})
    log_request_response(request, response)
    return response


def track_issue_changes(issue, form, editor):
    """Track changes made to an issue"""
    if not form.has_changed():
        return
    
    # Map form fields to display names
    field_display_names = {
        'summary': 'Summary',
        'description': 'Description', 
        'status': 'Status',
        'assignee': 'Assignee',
        'tags': 'Tags'
    }
    
    for field_name in form.changed_data:
        old_value = ''
        new_value = ''
        
        if field_name == 'tags':
            # Handle ManyToMany field specially
            old_tags = list(issue.tags.all())
            new_tags = form.cleaned_data['tags']
            old_value = ', '.join([tag.name for tag in old_tags])
            new_value = ', '.join([tag.name for tag in new_tags])
        else:
            # Get old value
            old_field_value = getattr(issue, field_name)
            if old_field_value is not None:
                old_value = str(old_field_value)
            
            # Get new value
            new_field_value = form.cleaned_data.get(field_name)
            if new_field_value is not None:
                new_value = str(new_field_value)
        
        # Create history record
        IssueEditHistory.objects.create(
            issue=issue,
            editor=editor,
            field_name=field_display_names.get(field_name, field_name),
            old_value=old_value,
            new_value=new_value
        )