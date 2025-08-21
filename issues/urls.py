from django.urls import path
from . import views

urlpatterns = [
    # Issue views
    path('', views.issue_list, name='issue_list'),
    path('issue/<int:pk>/', views.issue_detail, name='issue_detail'),
    path('issue/new/', views.issue_create, name='issue_create'),
    path('issue/<int:pk>/edit/', views.issue_edit, name='issue_edit'),
    path('issue/<int:pk>/delete/', views.issue_delete, name='issue_delete'),
    
    # Comment views
    path('issue/<int:issue_pk>/comment/', views.comment_create, name='comment_create'),
    path('comment/<int:pk>/edit/', views.comment_edit, name='comment_edit'),
    
    # Authentication views
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    
    # Settings view
    path('settings/', views.settings_view, name='settings'),
]