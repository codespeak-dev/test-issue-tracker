"""
Endpoint tests for all views
"""

import pytest
import json
from unittest.mock import patch, Mock
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.http import JsonResponse
from issues.models import User, Issue, Comment, Status, Settings, Tag


# Mock the logging function to prevent RawPostDataException
def mock_log_request_response(request, response):
    pass


User = get_user_model()


@patch('issues.views.log_request_response', mock_log_request_response)
class TestEndpoints(TestCase):
    """Test class for endpoint tests"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        
        # Create test users
        self.regular_user = User.objects.create_user(
            email='user@example.com',
            name='Regular User'
        )
        self.staff_user = User.objects.create_user(
            email='staff@example.com',
            name='Staff User',
            is_staff=True
        )
        
        # Create test status
        self.open_status = Status.objects.create(name='Open', is_open=True)
        self.done_status = Status.objects.create(name='Done', is_open=False)
        
        # Create test issue
        self.test_issue = Issue.objects.create(
            summary='Test Issue',
            description='Test description',
            status=self.open_status,
            author=self.regular_user
        )
    
    @pytest.mark.timeout(30)
    def test_issue_list_anonymous(self):
        """
        Test kind: endpoint_tests
        Original method: issue_list
        """
        response = self.client.get(reverse('issue_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Issue')
        self.assertContains(response, self.regular_user.name)
    
    @pytest.mark.timeout(30)
    def test_issue_list_authenticated(self):
        """
        Test kind: endpoint_tests
        Original method: issue_list
        """
        self.client.force_login(self.regular_user)
        response = self.client.get(reverse('issue_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Issue')
    
    @pytest.mark.timeout(30)
    def test_issue_detail_anonymous(self):
        """
        Test kind: endpoint_tests
        Original method: issue_detail
        """
        response = self.client.get(reverse('issue_detail', args=[self.test_issue.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Issue')
        self.assertContains(response, 'Test description')
        # Comment form should not be present for anonymous users
        self.assertNotContains(response, 'Add a comment')
    
    @pytest.mark.timeout(30)
    def test_issue_detail_authenticated(self):
        """
        Test kind: endpoint_tests
        Original method: issue_detail
        """
        self.client.force_login(self.regular_user)
        response = self.client.get(reverse('issue_detail', args=[self.test_issue.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Issue')
        # Comment form should be present for authenticated users
        self.assertContains(response, 'Add a comment')
    
    @pytest.mark.timeout(30)
    def test_issue_detail_not_found(self):
        """
        Test kind: endpoint_tests
        Original method: issue_detail
        """
        response = self.client.get(reverse('issue_detail', args=[999]))
        self.assertEqual(response.status_code, 404)
    
    @pytest.mark.timeout(30)
    def test_issue_create_get_anonymous(self):
        """
        Test kind: endpoint_tests
        Original method: issue_create
        """
        response = self.client.get(reverse('issue_create'))
        self.assertEqual(response.status_code, 302)  # Redirect to login
    
    @pytest.mark.timeout(30)
    def test_issue_create_get_authenticated(self):
        """
        Test kind: endpoint_tests
        Original method: issue_create
        """
        self.client.force_login(self.regular_user)
        response = self.client.get(reverse('issue_create'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Create Issue')
        self.assertContains(response, 'summary')
    
    @pytest.mark.timeout(30)
    def test_issue_create_post_valid(self):
        """
        Test kind: endpoint_tests
        Original method: issue_create
        """
        self.client.force_login(self.regular_user)
        
        data = {
            'summary': 'New Test Issue',
            'description': 'New test description',
            'status': self.open_status.id,
            'assignee': ''  # Explicitly set empty assignee
        }
        
        response = self.client.post(reverse('issue_create'), data=data)
        
        # Should redirect to the new issue
        self.assertEqual(response.status_code, 302)
        
        # Check issue was created
        new_issue = Issue.objects.filter(summary='New Test Issue').first()
        self.assertIsNotNone(new_issue)
        self.assertEqual(new_issue.author, self.regular_user)
        self.assertEqual(new_issue.description, 'New test description')
    
    @pytest.mark.timeout(30)
    def test_issue_create_post_invalid(self):
        """
        Test kind: endpoint_tests
        Original method: issue_create
        """
        self.client.force_login(self.regular_user)
        
        data = {
            'summary': '',  # Required field empty
            'description': 'Description without summary',
            'status': self.open_status.id,
            'assignee': ''
        }
        
        response = self.client.post(reverse('issue_create'), data=data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'This field is required')
    
    @pytest.mark.timeout(30)
    def test_issue_edit_get_anonymous(self):
        """
        Test kind: endpoint_tests
        Original method: issue_edit
        """
        response = self.client.get(reverse('issue_edit', args=[self.test_issue.pk]))
        self.assertEqual(response.status_code, 302)  # Redirect to login
    
    @pytest.mark.timeout(30)
    def test_issue_edit_get_authorized(self):
        """
        Test kind: endpoint_tests
        Original method: issue_edit
        """
        self.client.force_login(self.regular_user)
        response = self.client.get(reverse('issue_edit', args=[self.test_issue.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Edit Issue')
        self.assertContains(response, self.test_issue.summary)
    
    @pytest.mark.timeout(30)
    def test_issue_edit_get_unauthorized(self):
        """
        Test kind: endpoint_tests
        Original method: issue_edit
        """
        # Create another user
        other_user = User.objects.create_user(
            email='other@example.com',
            name='Other User'
        )
        
        self.client.force_login(other_user)
        response = self.client.get(reverse('issue_edit', args=[self.test_issue.pk]))
        self.assertEqual(response.status_code, 200)  # Now anyone can edit
    
    @pytest.mark.timeout(30)
    def test_issue_edit_post_valid(self):
        """
        Test kind: endpoint_tests
        Original method: issue_edit
        """
        self.client.force_login(self.regular_user)
        
        data = {
            'summary': 'Updated Test Issue',
            'description': 'Updated description',
            'status': self.done_status.id,
            'assignee': ''
        }
        
        response = self.client.post(reverse('issue_edit', args=[self.test_issue.pk]), data=data)
        
        # Should redirect to issue detail
        self.assertEqual(response.status_code, 302)
        
        # Check issue was updated
        self.test_issue.refresh_from_db()
        self.assertEqual(self.test_issue.summary, 'Updated Test Issue')
        self.assertEqual(self.test_issue.description, 'Updated description')
        self.assertEqual(self.test_issue.status, self.done_status)
    
    @pytest.mark.timeout(30)
    def test_issue_delete_anonymous(self):
        """
        Test kind: endpoint_tests
        Original method: issue_delete
        """
        response = self.client.delete(reverse('issue_delete', args=[self.test_issue.pk]))
        self.assertEqual(response.status_code, 302)  # Redirect to login
    
    @pytest.mark.timeout(30)
    def test_issue_delete_authorized(self):
        """
        Test kind: endpoint_tests
        Original method: issue_delete
        """
        self.client.force_login(self.regular_user)
        response = self.client.delete(reverse('issue_delete', args=[self.test_issue.pk]))
        self.assertEqual(response.status_code, 200)
        
        # Check response is JSON
        data = response.json()
        self.assertTrue(data['success'])
        
        # Check issue was deleted
        self.assertFalse(Issue.objects.filter(pk=self.test_issue.pk).exists())
    
    @pytest.mark.timeout(30)
    def test_issue_delete_unauthorized(self):
        """
        Test kind: endpoint_tests
        Original method: issue_delete
        """
        other_user = User.objects.create_user(
            email='other@example.com',
            name='Other User'
        )
        
        self.client.force_login(other_user)
        response = self.client.delete(reverse('issue_delete', args=[self.test_issue.pk]))
        self.assertEqual(response.status_code, 403)
    
    @pytest.mark.timeout(30)
    def test_comment_create_anonymous(self):
        """
        Test kind: endpoint_tests
        Original method: comment_create
        """
        data = {'content': 'Test comment'}
        response = self.client.post(
            reverse('comment_create', args=[self.test_issue.pk]),
            data=data
        )
        self.assertEqual(response.status_code, 302)  # Redirect to login
    
    @pytest.mark.timeout(30)
    def test_comment_create_authenticated_valid(self):
        """
        Test kind: endpoint_tests
        Original method: comment_create
        """
        self.client.force_login(self.regular_user)
        
        data = {'content': 'Test comment content'}
        response = self.client.post(
            reverse('comment_create', args=[self.test_issue.pk]),
            data=data
        )
        
        # Should redirect to issue detail
        self.assertEqual(response.status_code, 302)
        
        # Check comment was created
        comment = Comment.objects.filter(issue=self.test_issue).first()
        self.assertIsNotNone(comment)
        self.assertEqual(comment.content, 'Test comment content')
        self.assertEqual(comment.author, self.regular_user)
    
    @pytest.mark.timeout(30)
    def test_comment_create_authenticated_invalid(self):
        """
        Test kind: endpoint_tests
        Original method: comment_create
        """
        self.client.force_login(self.regular_user)
        
        data = {'content': ''}  # Empty content
        response = self.client.post(
            reverse('comment_create', args=[self.test_issue.pk]),
            data=data
        )
        
        # Should still redirect, but no comment created
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Comment.objects.filter(issue=self.test_issue).count(), 0)
    
    @pytest.mark.timeout(30)
    def test_comment_edit_get_authenticated(self):
        """
        Test kind: endpoint_tests
        Original method: comment_edit
        """
        # Create a comment
        comment = Comment.objects.create(
            content='Original comment',
            author=self.regular_user,
            issue=self.test_issue
        )
        
        self.client.force_login(self.regular_user)
        response = self.client.get(reverse('comment_edit', args=[comment.pk]))
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['content'], 'Original comment')
    
    @pytest.mark.timeout(30)
    def test_comment_edit_post_authorized(self):
        """
        Test kind: endpoint_tests
        Original method: comment_edit
        """
        # Create a comment
        comment = Comment.objects.create(
            content='Original comment',
            author=self.regular_user,
            issue=self.test_issue
        )
        
        self.client.force_login(self.regular_user)
        
        data = {'content': 'Updated comment content'}
        response = self.client.post(reverse('comment_edit', args=[comment.pk]), data=data)
        
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        self.assertTrue(response_data['success'])
        
        # Check comment was updated
        comment.refresh_from_db()
        self.assertEqual(comment.content, 'Updated comment content')
    
    @pytest.mark.timeout(30)
    def test_login_view_get(self):
        """
        Test kind: endpoint_tests
        Original method: login_view
        """
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'email')
    
    @pytest.mark.timeout(30)
    def test_login_view_post_valid(self):
        """
        Test kind: endpoint_tests
        Original method: login_view
        """
        data = {'email': 'user@example.com'}
        response = self.client.post(reverse('login'), data=data)
        
        # Should redirect to issue list
        self.assertEqual(response.status_code, 302)
        
        # User should be logged in
        self.assertTrue(response.wsgi_request.user.is_authenticated)
    
    @pytest.mark.timeout(30)
    def test_login_view_post_invalid(self):
        """
        Test kind: endpoint_tests
        Original method: login_view
        """
        data = {'email': 'nonexistent@example.com'}
        response = self.client.post(reverse('login'), data=data)
        
        # Should show form with errors
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'No account found')
    
    @pytest.mark.timeout(30)
    def test_login_view_already_authenticated(self):
        """
        Test kind: endpoint_tests
        Original method: login_view
        """
        self.client.force_login(self.regular_user)
        response = self.client.get(reverse('login'))
        
        # Should redirect to issue list
        self.assertEqual(response.status_code, 302)
    
    @pytest.mark.timeout(30)
    def test_register_view_get(self):
        """
        Test kind: endpoint_tests
        Original method: register_view
        """
        response = self.client.get(reverse('register'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'name')
        self.assertContains(response, 'email')
    
    @pytest.mark.timeout(30)
    def test_register_view_post_valid(self):
        """
        Test kind: endpoint_tests
        Original method: register_view
        """
        data = {
            'name': 'New User',
            'email': 'newuser@example.com'
        }
        response = self.client.post(reverse('register'), data=data)
        
        # Should redirect to issue list
        self.assertEqual(response.status_code, 302)
        
        # User should be created and logged in
        new_user = User.objects.filter(email='newuser@example.com').first()
        self.assertIsNotNone(new_user)
        self.assertEqual(new_user.name, 'New User')
    
    @pytest.mark.timeout(30)
    def test_register_view_post_invalid(self):
        """
        Test kind: endpoint_tests
        Original method: register_view
        """
        data = {
            'name': 'Duplicate User',
            'email': 'user@example.com'  # Already exists
        }
        response = self.client.post(reverse('register'), data=data)
        
        # Should show form with errors
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'already exists')
    
    @pytest.mark.timeout(30)
    def test_logout_view_authenticated(self):
        """
        Test kind: endpoint_tests
        Original method: logout_view
        """
        self.client.force_login(self.regular_user)
        response = self.client.get(reverse('logout'))
        
        # Should redirect to issue list
        self.assertEqual(response.status_code, 302)
    
    @pytest.mark.timeout(30)
    def test_logout_view_anonymous(self):
        """
        Test kind: endpoint_tests
        Original method: logout_view
        """
        response = self.client.get(reverse('logout'))
        
        # Should redirect to issue list
        self.assertEqual(response.status_code, 302)
    
    @pytest.mark.timeout(30)
    def test_settings_view_anonymous(self):
        """
        Test kind: endpoint_tests
        Original method: settings_view
        """
        response = self.client.get(reverse('settings'))
        self.assertEqual(response.status_code, 302)  # Redirect to login
    
    @pytest.mark.timeout(30)
    def test_settings_view_regular_user(self):
        """
        Test kind: endpoint_tests
        Original method: settings_view
        """
        self.client.force_login(self.regular_user)
        response = self.client.get(reverse('settings'))
        self.assertEqual(response.status_code, 403)  # Forbidden
    
    @pytest.mark.timeout(30)
    def test_settings_view_staff_user_get(self):
        """
        Test kind: endpoint_tests
        Original method: settings_view
        """
        self.client.force_login(self.staff_user)
        response = self.client.get(reverse('settings'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'slack_bot_token')
        self.assertContains(response, 'github_access_token')
    
    @pytest.mark.timeout(30)
    def test_settings_view_staff_user_post_valid(self):
        """
        Test kind: endpoint_tests
        Original method: settings_view
        """
        self.client.force_login(self.staff_user)
        
        data = {
            'slack_bot_token': 'xoxb-test-token',
            'slack_channel_id': 'C1234567890',
            'github_access_token': 'ghp_test_token',
            'github_repository_owner': 'testowner',
            'github_repository_name': 'testrepo'
        }
        
        response = self.client.post(reverse('settings'), data=data)
        
        # Should redirect to settings
        self.assertEqual(response.status_code, 302)
        
        # Check settings were saved
        settings = Settings.load()
        self.assertEqual(settings.slack_bot_token, 'xoxb-test-token')
        self.assertEqual(settings.github_access_token, 'ghp_test_token')
    
    @pytest.mark.timeout(30)
    def test_tag_list_anonymous(self):
        """
        Test kind: endpoint_tests
        Original method: tag_list
        """
        response = self.client.get(reverse('tag_list'))
        self.assertEqual(response.status_code, 302)  # Redirect to login
    
    @pytest.mark.timeout(30)
    def test_tag_list_authenticated(self):
        """
        Test kind: endpoint_tests
        Original method: tag_list
        """
        # Create test tags
        tag1 = Tag.objects.create(name='Bug', color='#ff0000')
        tag2 = Tag.objects.create(name='Feature', color='#00ff00')
        
        self.client.force_login(self.regular_user)
        response = self.client.get(reverse('tag_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Bug')
        self.assertContains(response, 'Feature')
    
    @pytest.mark.timeout(30)
    def test_tag_create_get_anonymous(self):
        """
        Test kind: endpoint_tests
        Original method: tag_create
        """
        response = self.client.get(reverse('tag_create'))
        self.assertEqual(response.status_code, 302)  # Redirect to login
    
    @pytest.mark.timeout(30)
    def test_tag_create_get_authenticated(self):
        """
        Test kind: endpoint_tests
        Original method: tag_create
        """
        self.client.force_login(self.regular_user)
        response = self.client.get(reverse('tag_create'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Create Tag')
        self.assertContains(response, 'name')
        self.assertContains(response, 'color')
    
    @pytest.mark.timeout(30)
    def test_tag_create_post_valid(self):
        """
        Test kind: endpoint_tests
        Original method: tag_create
        """
        self.client.force_login(self.regular_user)
        
        data = {
            'name': 'Bug',
            'color': '#ff0000'
        }
        
        response = self.client.post(reverse('tag_create'), data=data)
        
        # Should redirect to tag list
        self.assertEqual(response.status_code, 302)
        
        # Check tag was created
        tag = Tag.objects.filter(name='Bug').first()
        self.assertIsNotNone(tag)
        self.assertEqual(tag.color, '#ff0000')
    
    @pytest.mark.timeout(30)
    def test_tag_create_post_invalid(self):
        """
        Test kind: endpoint_tests
        Original method: tag_create
        """
        self.client.force_login(self.regular_user)
        
        data = {
            'name': '',  # Required field empty
            'color': '#ff0000'
        }
        
        response = self.client.post(reverse('tag_create'), data=data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'This field is required')
    
    @pytest.mark.timeout(30)
    def test_tag_edit_get_anonymous(self):
        """
        Test kind: endpoint_tests
        Original method: tag_edit
        """
        tag = Tag.objects.create(name='Bug', color='#ff0000')
        response = self.client.get(reverse('tag_edit', args=[tag.pk]))
        self.assertEqual(response.status_code, 302)  # Redirect to login
    
    @pytest.mark.timeout(30)
    def test_tag_edit_get_authenticated(self):
        """
        Test kind: endpoint_tests
        Original method: tag_edit
        """
        tag = Tag.objects.create(name='Bug', color='#ff0000')
        
        self.client.force_login(self.regular_user)
        response = self.client.get(reverse('tag_edit', args=[tag.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Edit Tag')
        self.assertContains(response, 'Bug')
    
    @pytest.mark.timeout(30)
    def test_tag_edit_post_valid(self):
        """
        Test kind: endpoint_tests
        Original method: tag_edit
        """
        tag = Tag.objects.create(name='Bug', color='#ff0000')
        
        self.client.force_login(self.regular_user)
        
        data = {
            'name': 'Critical Bug',
            'color': '#cc0000'
        }
        
        response = self.client.post(reverse('tag_edit', args=[tag.pk]), data=data)
        
        # Should redirect to tag list
        self.assertEqual(response.status_code, 302)
        
        # Check tag was updated
        tag.refresh_from_db()
        self.assertEqual(tag.name, 'Critical Bug')
        self.assertEqual(tag.color, '#cc0000')
    
    @pytest.mark.timeout(30)
    def test_tag_edit_not_found(self):
        """
        Test kind: endpoint_tests
        Original method: tag_edit
        """
        self.client.force_login(self.regular_user)
        response = self.client.get(reverse('tag_edit', args=[999]))
        self.assertEqual(response.status_code, 404)
    
    @pytest.mark.timeout(30)
    def test_tag_delete_anonymous(self):
        """
        Test kind: endpoint_tests
        Original method: tag_delete
        """
        tag = Tag.objects.create(name='Bug', color='#ff0000')
        response = self.client.delete(reverse('tag_delete', args=[tag.pk]))
        self.assertEqual(response.status_code, 302)  # Redirect to login
    
    @pytest.mark.timeout(30)
    def test_tag_delete_authenticated(self):
        """
        Test kind: endpoint_tests
        Original method: tag_delete
        """
        tag = Tag.objects.create(name='Bug', color='#ff0000')
        
        self.client.force_login(self.regular_user)
        response = self.client.delete(reverse('tag_delete', args=[tag.pk]))
        self.assertEqual(response.status_code, 200)
        
        # Check response is JSON
        data = response.json()
        self.assertTrue(data['success'])
        
        # Check tag was deleted
        self.assertFalse(Tag.objects.filter(pk=tag.pk).exists())
    
    @pytest.mark.timeout(30)
    def test_tag_delete_not_found(self):
        """
        Test kind: endpoint_tests
        Original method: tag_delete
        """
        self.client.force_login(self.regular_user)
        response = self.client.delete(reverse('tag_delete', args=[999]))
        self.assertEqual(response.status_code, 404)
    
    @pytest.mark.timeout(30)
    def test_issue_restore_anonymous(self):
        """
        Test kind: endpoint_tests
        Original method: issue_restore
        """
        # Create a deleted issue
        deleted_issue = Issue.objects.create(
            summary='Issue to Restore',
            description='Test description',
            status=self.open_status,
            author=self.regular_user
        )
        deleted_issue.soft_delete()
        
        response = self.client.post(reverse('issue_restore', args=[deleted_issue.pk]))
        self.assertEqual(response.status_code, 302)  # Redirect to login
    
    @pytest.mark.timeout(30)
    def test_issue_restore_authorized(self):
        """
        Test kind: endpoint_tests
        Original method: issue_restore
        """
        # Create a deleted issue
        deleted_issue = Issue.objects.create(
            summary='Issue to Restore',
            description='Test description',
            status=self.open_status,
            author=self.regular_user
        )
        deleted_issue.soft_delete()
        
        self.client.force_login(self.regular_user)
        response = self.client.post(reverse('issue_restore', args=[deleted_issue.pk]))
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        
        # Check issue was restored
        deleted_issue.refresh_from_db()
        self.assertFalse(deleted_issue.is_deleted())
    
    @pytest.mark.timeout(30)
    def test_issue_restore_unauthorized(self):
        """
        Test kind: endpoint_tests
        Original method: issue_restore
        """
        # Create another user and their deleted issue
        other_user = User.objects.create_user(
            email='other@example.com',
            name='Other User'
        )
        
        deleted_issue = Issue.objects.create(
            summary='Other User Issue',
            description='Test description',
            status=self.open_status,
            author=other_user
        )
        deleted_issue.soft_delete()
        
        # Try to restore as regular_user (not the author)
        self.client.force_login(self.regular_user)
        response = self.client.post(reverse('issue_restore', args=[deleted_issue.pk]))
        
        self.assertEqual(response.status_code, 403)
        data = response.json()
        self.assertIn('error', data)
    
    @pytest.mark.timeout(30)
    def test_issue_restore_not_deleted(self):
        """
        Test kind: endpoint_tests
        Original method: issue_restore
        """
        # Try to restore an issue that's not deleted
        self.client.force_login(self.regular_user)
        response = self.client.post(reverse('issue_restore', args=[self.test_issue.pk]))
        
        # Should return 404 since issue_restore only works on deleted issues
        self.assertEqual(response.status_code, 404)