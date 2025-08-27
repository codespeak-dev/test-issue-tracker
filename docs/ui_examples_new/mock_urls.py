"""
Mock URL patterns for template rendering.
This provides the URL configuration required by Django.
"""

from django.urls import path

# Mock view functions (not actually used, just for URL pattern requirements)
def mock_view(request, *args, **kwargs):
    pass

urlpatterns = [
    path('', mock_view, name='issue_list'),
    path('issue/<int:pk>/', mock_view, name='issue_detail'),
    path('issue/new/', mock_view, name='issue_create'),
    path('issue/<int:pk>/edit/', mock_view, name='issue_edit'),
    path('issue/<int:issue_pk>/comment/', mock_view, name='comment_create'),
    path('login/', mock_view, name='login'),
    path('logout/', mock_view, name='logout'),
    path('register/', mock_view, name='register'),
    path('settings/', mock_view, name='settings'),
    path('tags/', mock_view, name='tag_list'),
    path('tags/new/', mock_view, name='tag_create'),
    path('tags/<int:pk>/edit/', mock_view, name='tag_edit'),
]