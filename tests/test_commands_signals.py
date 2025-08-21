"""
Unit tests for management commands and signals
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from issues.models import User, Issue, Status, Comment, Settings
from issues.management.commands.github_poller import Command
from issues.signals import issue_created


class TestGithubPollerCommand(TestCase):
    """Test class for GitHub poller management command unit tests"""
    
    def setUp(self):
        """Set up test data"""
        self.command = Command()
        self.user = User.objects.create_user(
            email='test@example.com',
            name='Test User'
        )
        self.open_status = Status.objects.create(name='Open', is_open=True)
        self.done_status = Status.objects.create(name='Done', is_open=False)
    
    @pytest.mark.timeout(30)
    @patch('issues.management.commands.github_poller.Settings.load')
    def test_handle_missing_config(self, mock_settings_load):
        """
        Test kind: unit_tests
        Original method: Command.handle
        """
        # Mock settings with missing configuration
        mock_settings = Mock()
        mock_settings.github_access_token = ''
        mock_settings.github_repository_owner = ''
        mock_settings.github_repository_name = ''
        mock_settings_load.return_value = mock_settings
        
        with patch.object(self.command, 'stdout') as mock_stdout:
            with patch.object(self.command, 'poll_github') as mock_poll:
                self.command.handle(once=True, interval=10)
                
                # Should call poll_github once
                mock_poll.assert_called_once()
    
    @pytest.mark.timeout(30)
    @patch('issues.management.commands.github_poller.time.sleep')
    @patch('issues.management.commands.github_poller.Settings.load')
    def test_handle_keyboard_interrupt(self, mock_settings_load, mock_sleep):
        """
        Test kind: unit_tests
        Original method: Command.handle
        """
        mock_settings = Mock()
        mock_settings.github_access_token = 'token'
        mock_settings.github_repository_owner = 'owner'
        mock_settings.github_repository_name = 'repo'
        mock_settings_load.return_value = mock_settings
        
        with patch.object(self.command, 'poll_github', side_effect=KeyboardInterrupt):
            with patch.object(self.command, 'stdout') as mock_stdout:
                self.command.handle(once=False, interval=1)
                
                # Should handle KeyboardInterrupt gracefully
                self.assertTrue(any('stopped by user' in str(call) for call in mock_stdout.write.call_args_list))
    
    @pytest.mark.timeout(30)
    @patch('issues.management.commands.github_poller.Settings.load')
    def test_poll_github_missing_config(self, mock_settings_load):
        """
        Test kind: unit_tests
        Original method: Command.poll_github
        """
        # Mock settings with missing configuration
        mock_settings = Mock()
        mock_settings.github_access_token = ''
        mock_settings.github_repository_owner = 'owner'
        mock_settings.github_repository_name = 'repo'
        mock_settings_load.return_value = mock_settings
        
        with patch.object(self.command, 'stdout') as mock_stdout:
            self.command.poll_github()
            
            # Should skip polling when config is missing
            mock_stdout.write.assert_called_once_with("GitHub integration not configured, skipping poll")
    
    @pytest.mark.timeout(30)
    @patch('issues.management.commands.github_poller.Settings.load')
    @patch('issues.management.commands.github_poller.Github')
    def test_poll_github_success(self, mock_github_class, mock_settings_load):
        """
        Test kind: unit_tests
        Original method: Command.poll_github
        """
        # Mock settings with valid configuration
        mock_settings = Mock()
        mock_settings.github_access_token = 'token'
        mock_settings.github_repository_owner = 'owner'
        mock_settings.github_repository_name = 'repo'
        mock_settings_load.return_value = mock_settings
        
        # Mock GitHub client and repository
        mock_github = Mock()
        mock_repo = Mock()
        mock_github.get_repo.return_value = mock_repo
        mock_repo.get_commits.return_value = []
        mock_github_class.return_value = mock_github
        
        with patch('issues.management.commands.github_poller.timezone') as mock_timezone:
            from datetime import datetime, timezone as dt_timezone
            mock_now = datetime.now(dt_timezone.utc)
            mock_timezone.now.return_value = mock_now
            
            self.command.poll_github()
            
            # Should create GitHub client and get repository
            mock_github_class.assert_called_once_with('token')
            mock_github.get_repo.assert_called_once_with('owner/repo')
            # Check that get_commits was called with a datetime object
            self.assertTrue(mock_repo.get_commits.called)
    
    @pytest.mark.timeout(30)
    def test_process_commit_no_matching_pattern(self):
        """
        Test kind: unit_tests
        Original method: Command.process_commit
        """
        # Mock commit with no matching pattern
        mock_commit = Mock()
        mock_commit.commit.message = 'Regular commit message'
        
        result = self.command.process_commit(mock_commit)
        
        # Should return False when no pattern matches
        self.assertFalse(result)
    
    @pytest.mark.timeout(30)
    def test_process_commit_matching_pattern_issue_not_found(self):
        """
        Test kind: unit_tests
        Original method: Command.process_commit
        """
        # Mock commit with matching pattern
        mock_commit = Mock()
        mock_commit.commit.message = '#999 Fixed the bug'
        mock_commit.sha = 'abc123def456'
        
        with patch.object(self.command, 'stderr') as mock_stderr:
            result = self.command.process_commit(mock_commit)
            
            # Should return False when issue not found
            self.assertFalse(result)
    
    @pytest.mark.timeout(30)
    def test_process_commit_matching_pattern_success(self):
        """
        Test kind: unit_tests
        Original method: Command.process_commit
        """
        # Create test issue
        issue = Issue.objects.create(
            summary='Test Issue',
            description='Test description',
            status=self.open_status,
            author=self.user
        )
        
        # Mock commit with matching pattern
        mock_commit = Mock()
        mock_commit.commit.message = f'#{issue.id} Fixed the issue'
        mock_commit.sha = 'abc123def456'
        mock_commit.html_url = 'https://github.com/owner/repo/commit/abc123'
        mock_commit.commit.author.name = 'Test Author'
        mock_commit.commit.author.date.strftime.return_value = '2023-01-01 10:00:00 UTC'
        
        with patch.object(self.command, 'stdout') as mock_stdout:
            result = self.command.process_commit(mock_commit)
            
            # Should return True and close the issue
            self.assertTrue(result)
            
            # Reload issue from database
            issue.refresh_from_db()
            self.assertEqual(issue.status, self.done_status)
            
            # Should create a comment
            comments = Comment.objects.filter(issue=issue)
            self.assertEqual(comments.count(), 1)
            
            comment = comments.first()
            self.assertIn('automatically closed by commit', comment.content)
            self.assertIn('abc123', comment.content)


class TestIssueCreatedSignal(TestCase):
    """Test class for issue_created signal unit tests"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            email='test@example.com',
            name='Test User'
        )
        self.status = Status.objects.create(name='Open', is_open=True)
    
    @pytest.mark.timeout(30)
    @patch('issues.signals.notify_slack')
    @patch('issues.signals.logger')
    def test_issue_created_new_issue(self, mock_logger, mock_notify_slack):
        """
        Test kind: unit_tests
        Original method: issues.signals.issue_created
        """
        issue = Issue.objects.create(
            summary='Test Issue',
            description='Test description',
            status=self.status,
            author=self.user
        )
        
        # Signal should have been called
        mock_notify_slack.assert_called_once_with(issue)
        
        # Should log the issue creation
        self.assertTrue(mock_logger.info.called)
        log_call_args = mock_logger.info.call_args[0][0]
        
        # Should contain proper JSON data
        import json
        log_data = json.loads(log_call_args)
        self.assertEqual(log_data['event'], 'issue_created')
        self.assertEqual(log_data['issue_id'], issue.id)
        self.assertEqual(log_data['summary'], 'Test Issue')
        self.assertEqual(log_data['author'], 'test@example.com')
    
    @pytest.mark.timeout(30)
    @patch('issues.signals.notify_slack')
    @patch('issues.signals.logger')
    def test_issue_created_updated_issue(self, mock_logger, mock_notify_slack):
        """
        Test kind: unit_tests
        Original method: issues.signals.issue_created
        """
        # Create issue first
        issue = Issue.objects.create(
            summary='Test Issue',
            description='Test description',
            status=self.status,
            author=self.user
        )
        
        # Reset mocks
        mock_notify_slack.reset_mock()
        mock_logger.reset_mock()
        
        # Update the issue (should not trigger signal)
        issue.summary = 'Updated Test Issue'
        issue.save()
        
        # Signal should not have been called for update
        mock_notify_slack.assert_not_called()
        mock_logger.info.assert_not_called()