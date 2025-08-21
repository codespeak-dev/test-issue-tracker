"""
Unit tests for model methods
"""

import pytest
from django.test import TestCase
from django.urls import reverse
from django.core.exceptions import ValidationError
from issues.models import UserManager, User, Issue, Comment, Settings, Status


class TestUserManager(TestCase):
    """Test class for UserManager unit tests"""
    
    @pytest.mark.timeout(30)
    def test_create_user_valid(self):
        """
        Test kind: unit_tests
        Original method: UserManager.create_user
        """
        user = User.objects.create_user(
            email='test@example.com',
            name='Test User'
        )
        self.assertEqual(user.email, 'test@example.com')
        self.assertEqual(user.name, 'Test User')
        self.assertFalse(user.has_usable_password())
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
    
    @pytest.mark.timeout(30)
    def test_create_user_with_extra_fields(self):
        """
        Test kind: unit_tests
        Original method: UserManager.create_user
        """
        user = User.objects.create_user(
            email='test@example.com',
            name='Test User',
            is_staff=True
        )
        self.assertEqual(user.email, 'test@example.com')
        self.assertEqual(user.name, 'Test User')
        self.assertTrue(user.is_staff)
    
    @pytest.mark.timeout(30)
    def test_create_user_no_email(self):
        """
        Test kind: unit_tests
        Original method: UserManager.create_user
        """
        with self.assertRaises(ValueError) as context:
            User.objects.create_user(
                email='',
                name='Test User'
            )
        self.assertEqual(str(context.exception), 'The Email field must be set')
    
    @pytest.mark.timeout(30)
    def test_create_superuser_valid(self):
        """
        Test kind: unit_tests
        Original method: UserManager.create_superuser
        """
        user = User.objects.create_superuser(
            email='admin@example.com',
            name='Admin User'
        )
        self.assertEqual(user.email, 'admin@example.com')
        self.assertEqual(user.name, 'Admin User')
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)
        self.assertFalse(user.has_usable_password())
    
    @pytest.mark.timeout(30)
    def test_create_superuser_with_defaults(self):
        """
        Test kind: unit_tests
        Original method: UserManager.create_superuser
        """
        user = User.objects.create_superuser(
            email='admin@example.com',
            name='Admin User'
        )
        # The create_superuser method should set these to True by default
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)


class TestUser(TestCase):
    """Test class for User unit tests"""
    
    def setUp(self):
        """Set up test data"""
        self.regular_user = User.objects.create_user(
            email='user@example.com',
            name='Regular User'
        )
        self.superuser = User.objects.create_superuser(
            email='admin@example.com',
            name='Admin User'
        )
    
    @pytest.mark.timeout(30)
    def test_has_perm_regular_user(self):
        """
        Test kind: unit_tests
        Original method: User.has_perm
        """
        self.assertFalse(self.regular_user.has_perm('any.permission'))
        self.assertFalse(self.regular_user.has_perm('issues.add_issue'))
        self.assertFalse(self.regular_user.has_perm('issues.change_issue', None))
    
    @pytest.mark.timeout(30)
    def test_has_perm_superuser(self):
        """
        Test kind: unit_tests
        Original method: User.has_perm
        """
        self.assertTrue(self.superuser.has_perm('any.permission'))
        self.assertTrue(self.superuser.has_perm('issues.add_issue'))
        self.assertTrue(self.superuser.has_perm('issues.change_issue', None))
    
    @pytest.mark.timeout(30)
    def test_has_module_perms_regular_user(self):
        """
        Test kind: unit_tests
        Original method: User.has_module_perms
        """
        self.assertFalse(self.regular_user.has_module_perms('issues'))
        self.assertFalse(self.regular_user.has_module_perms('admin'))
        self.assertFalse(self.regular_user.has_module_perms('any_app'))
    
    @pytest.mark.timeout(30)
    def test_has_module_perms_superuser(self):
        """
        Test kind: unit_tests
        Original method: User.has_module_perms
        """
        self.assertTrue(self.superuser.has_module_perms('issues'))
        self.assertTrue(self.superuser.has_module_perms('admin'))
        self.assertTrue(self.superuser.has_module_perms('any_app'))


class TestIssue(TestCase):
    """Test class for Issue unit tests"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            email='user@example.com',
            name='Test User'
        )
        self.status = Status.objects.create(name='Open', is_open=True)
        self.issue = Issue.objects.create(
            summary='Test Issue',
            description='Test **description** with markdown',
            status=self.status,
            author=self.user
        )
    
    @pytest.mark.timeout(30)
    def test_get_absolute_url(self):
        """
        Test kind: unit_tests
        Original method: Issue.get_absolute_url
        """
        expected_url = reverse('issue_detail', args=[self.issue.id])
        self.assertEqual(self.issue.get_absolute_url(), expected_url)
    
    @pytest.mark.timeout(30)
    def test_description_html_with_markdown(self):
        """
        Test kind: unit_tests
        Original method: Issue.description_html
        """
        html = self.issue.description_html()
        self.assertIn('<p>Test <strong>description</strong> with markdown</p>', html)
    
    @pytest.mark.timeout(30)
    def test_description_html_empty(self):
        """
        Test kind: unit_tests
        Original method: Issue.description_html
        """
        issue = Issue.objects.create(
            summary='Empty Description Issue',
            description='',
            status=self.status,
            author=self.user
        )
        html = issue.description_html()
        self.assertEqual(html, '')
    
    @pytest.mark.timeout(30)
    def test_description_html_plain_text(self):
        """
        Test kind: unit_tests
        Original method: Issue.description_html
        """
        issue = Issue.objects.create(
            summary='Plain Text Issue',
            description='Just plain text',
            status=self.status,
            author=self.user
        )
        html = issue.description_html()
        self.assertEqual(html, '<p>Just plain text</p>')


class TestComment(TestCase):
    """Test class for Comment unit tests"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            email='user@example.com',
            name='Test User'
        )
        self.status = Status.objects.create(name='Open', is_open=True)
        self.issue = Issue.objects.create(
            summary='Test Issue',
            description='Test description',
            status=self.status,
            author=self.user
        )
        self.comment = Comment.objects.create(
            content='Test **comment** with markdown',
            author=self.user,
            issue=self.issue
        )
    
    @pytest.mark.timeout(30)
    def test_content_html_with_markdown(self):
        """
        Test kind: unit_tests
        Original method: Comment.content_html
        """
        html = self.comment.content_html()
        self.assertIn('<p>Test <strong>comment</strong> with markdown</p>', html)
    
    @pytest.mark.timeout(30)
    def test_content_html_empty(self):
        """
        Test kind: unit_tests
        Original method: Comment.content_html
        """
        comment = Comment.objects.create(
            content='',
            author=self.user,
            issue=self.issue
        )
        html = comment.content_html()
        self.assertEqual(html, '')
    
    @pytest.mark.timeout(30)
    def test_content_html_plain_text(self):
        """
        Test kind: unit_tests
        Original method: Comment.content_html
        """
        comment = Comment.objects.create(
            content='Just plain text comment',
            author=self.user,
            issue=self.issue
        )
        html = comment.content_html()
        self.assertEqual(html, '<p>Just plain text comment</p>')


class TestSettings(TestCase):
    """Test class for Settings unit tests"""
    
    @pytest.mark.timeout(30)
    def test_save_singleton_pattern(self):
        """
        Test kind: unit_tests
        Original method: Settings.save
        """
        # Create first instance
        settings1 = Settings(
            slack_bot_token='token1',
            slack_channel_id='channel1'
        )
        settings1.save()
        self.assertEqual(settings1.pk, 1)
        
        # Create second instance - should override the first
        settings2 = Settings(
            slack_bot_token='token2',
            slack_channel_id='channel2'
        )
        settings2.save()
        self.assertEqual(settings2.pk, 1)
        
        # Should only have one instance in database
        self.assertEqual(Settings.objects.count(), 1)
        
        # Latest values should be in the database
        settings_from_db = Settings.objects.get(pk=1)
        self.assertEqual(settings_from_db.slack_bot_token, 'token2')
        self.assertEqual(settings_from_db.slack_channel_id, 'channel2')
    
    @pytest.mark.timeout(30)
    def test_delete_prevention(self):
        """
        Test kind: unit_tests
        Original method: Settings.delete
        """
        settings = Settings(
            slack_bot_token='token',
            slack_channel_id='channel'
        )
        settings.save()
        
        # Attempt to delete should not actually delete the object
        settings.delete()
        
        # Should still exist in database
        self.assertEqual(Settings.objects.count(), 1)
        self.assertTrue(Settings.objects.filter(pk=1).exists())
    
    @pytest.mark.timeout(30)
    def test_load_existing(self):
        """
        Test kind: unit_tests
        Original method: Settings.load
        """
        # Create settings instance
        original_settings = Settings(
            slack_bot_token='existing_token',
            slack_channel_id='existing_channel'
        )
        original_settings.save()
        
        # Load should return the existing instance
        loaded_settings = Settings.load()
        self.assertEqual(loaded_settings.pk, 1)
        self.assertEqual(loaded_settings.slack_bot_token, 'existing_token')
        self.assertEqual(loaded_settings.slack_channel_id, 'existing_channel')
    
    @pytest.mark.timeout(30)
    def test_load_create_new(self):
        """
        Test kind: unit_tests
        Original method: Settings.load
        """
        # Ensure no settings exist
        Settings.objects.all().delete()
        
        # Load should create a new instance
        loaded_settings = Settings.load()
        self.assertEqual(loaded_settings.pk, 1)
        self.assertEqual(loaded_settings.slack_bot_token, '')
        self.assertEqual(loaded_settings.slack_channel_id, '')
        
        # Should exist in database
        self.assertEqual(Settings.objects.count(), 1)