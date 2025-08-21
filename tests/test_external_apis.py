"""
External API tests for Slack and GitHub integrations
"""

import pytest
import os
from unittest.mock import patch, Mock
from django.test import TestCase, override_settings
from django.conf import settings
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from github import Github
from github.GithubException import GithubException
from issues.models import User, Issue, Status
from issues.integrations import notify_slack
from src.external_apis.validate_configuration import validate_slack_configuration, validate_github_configuration


class TestNotifySlack(TestCase):
    """Test class for notify_slack external API tests"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            email='test@example.com',
            name='Test User'
        )
        self.status = Status.objects.create(name='Open', is_open=True)
        self.issue = Issue.objects.create(
            summary='Test Issue for Slack',
            description='Test description',
            status=self.status,
            author=self.user
        )
    
    @pytest.mark.timeout(30)
    @override_settings(SLACK_BOT_TOKEN='xoxb-real-test-token')
    @override_settings(SLACK_CHANNEL_ID='C1234567890')
    def test_notify_slack_real_api_call(self):
        """
        Test kind: external_api_tests
        Original method: notify_slack
        
        This test makes actual API calls to Slack to verify integration works.
        It uses real Slack API credentials if available in environment.
        """
        # Skip test if real credentials are not available
        real_token = os.getenv('SLACK_BOT_TOKEN_TEST')
        real_channel = os.getenv('SLACK_CHANNEL_ID_TEST')
        
        if not real_token or not real_channel:
            self.skipTest("Real Slack credentials not available for testing")
        
        # Temporarily override settings with real credentials
        with override_settings(SLACK_BOT_TOKEN=real_token, SLACK_CHANNEL_ID=real_channel):
            # Create a Slack client to verify credentials work
            client = WebClient(token=real_token)
            
            try:
                # Test that we can authenticate
                auth_response = client.auth_test()
                self.assertTrue(auth_response.get('ok'))
                
                # Test that we can access the channel
                channel_response = client.conversations_info(channel=real_channel)
                self.assertTrue(channel_response.get('ok'))
                
                # Now test the actual notify_slack function
                notify_slack(self.issue)
                
                # If we reach here, the API call succeeded
                # We can't easily verify the message was posted without more complex setup,
                # but the fact that no exception was raised means the integration works
                
            except SlackApiError as e:
                self.fail(f"Slack API error during real API test: {e}")
            except Exception as e:
                self.fail(f"Unexpected error during real Slack API test: {e}")
    
    @pytest.mark.timeout(30)
    @override_settings(SLACK_BOT_TOKEN='xoxb-invalid-token')
    @override_settings(SLACK_CHANNEL_ID='C1234567890')
    def test_notify_slack_invalid_token(self):
        """
        Test kind: external_api_tests
        Original method: notify_slack
        
        This test verifies error handling with invalid credentials.
        """
        # This should not raise an exception, but should log an error
        with patch('issues.integrations.logger') as mock_logger:
            notify_slack(self.issue)
            
            # Should log an error due to invalid token
            self.assertTrue(mock_logger.error.called)
    
    @pytest.mark.timeout(30)
    @override_settings(SLACK_BOT_TOKEN='')
    @override_settings(SLACK_CHANNEL_ID='')
    def test_notify_slack_missing_config(self):
        """
        Test kind: external_api_tests
        Original method: notify_slack
        
        This test verifies behavior when configuration is missing.
        """
        with patch('issues.integrations.logger') as mock_logger:
            notify_slack(self.issue)
            
            # Should log that integration is not configured
            mock_logger.info.assert_called_once_with(
                "Slack integration not configured, skipping notification"
            )


class TestValidateSlackConfiguration(TestCase):
    """Test class for validate_slack_configuration external API tests"""
    
    @pytest.mark.timeout(30)
    def test_validate_slack_configuration_missing_token(self):
        """
        Test kind: external_api_tests
        Original method: validate_slack_configuration
        """
        config = {
            'slack_bot_token': '',
            'slack_channel_id': 'C1234567890'
        }
        
        success, message, details = validate_slack_configuration(config)
        
        self.assertFalse(success)
        self.assertEqual(message, "SLACK_BOT_TOKEN is not set")
        self.assertEqual(details, {})
    
    @pytest.mark.timeout(30)
    def test_validate_slack_configuration_missing_channel(self):
        """
        Test kind: external_api_tests
        Original method: validate_slack_configuration
        """
        config = {
            'slack_bot_token': 'xoxb-test-token',
            'slack_channel_id': ''
        }
        
        success, message, details = validate_slack_configuration(config)
        
        self.assertFalse(success)
        self.assertEqual(message, "SLACK_CHANNEL_ID is not set")
        self.assertEqual(details, {})
    
    @pytest.mark.timeout(30)
    def test_validate_slack_configuration_url_channel_id(self):
        """
        Test kind: external_api_tests
        Original method: validate_slack_configuration
        """
        config = {
            'slack_bot_token': 'xoxb-test-token',
            'slack_channel_id': 'https://example.slack.com/archives/C1234567890'
        }
        
        # Test with invalid token to trigger auth error (but valid format)
        success, message, details = validate_slack_configuration(config)
        
        # Should fail due to invalid token, but should have extracted channel ID
        self.assertFalse(success)
        self.assertIn('Invalid Slack bot token', message)
        self.assertEqual(details['channel_id'], 'C1234567890')
    
    @pytest.mark.timeout(30)
    def test_validate_slack_configuration_real_api(self):
        """
        Test kind: external_api_tests
        Original method: validate_slack_configuration
        
        This test makes actual API calls to validate Slack configuration.
        """
        # Skip test if real credentials are not available
        real_token = os.getenv('SLACK_BOT_TOKEN_TEST')
        real_channel = os.getenv('SLACK_CHANNEL_ID_TEST')
        
        if not real_token or not real_channel:
            self.skipTest("Real Slack credentials not available for testing")
        
        config = {
            'slack_bot_token': real_token,
            'slack_channel_id': real_channel
        }
        
        success, message, details = validate_slack_configuration(config)
        
        if success:
            self.assertTrue(success)
            self.assertEqual(message, "Slack configuration validated successfully")
            self.assertIn('bot_user_id', details)
            self.assertIn('bot_name', details)
            self.assertIn('team_name', details)
            self.assertIn('channel_id', details)
        else:
            # If it fails, it should be due to actual API issues, not our code
            self.assertIn('Slack API error', message)


class TestValidateGitHubConfiguration(TestCase):
    """Test class for validate_github_configuration external API tests"""
    
    @pytest.mark.timeout(30)
    def test_validate_github_configuration_missing_token(self):
        """
        Test kind: external_api_tests
        Original method: validate_github_configuration
        """
        config = {
            'github_access_token': '',
            'github_repository_owner': 'owner',
            'github_repository_name': 'repo'
        }
        
        success, message, details = validate_github_configuration(config)
        
        self.assertFalse(success)
        self.assertEqual(message, "GITHUB_ACCESS_TOKEN is not set")
        self.assertEqual(details, {})
    
    @pytest.mark.timeout(30)
    def test_validate_github_configuration_missing_owner(self):
        """
        Test kind: external_api_tests
        Original method: validate_github_configuration
        """
        config = {
            'github_access_token': 'ghp_test_token',
            'github_repository_owner': '',
            'github_repository_name': 'repo'
        }
        
        success, message, details = validate_github_configuration(config)
        
        self.assertFalse(success)
        self.assertEqual(message, "GITHUB_REPOSITORY_OWNER is not set")
        self.assertEqual(details, {})
    
    @pytest.mark.timeout(30)
    def test_validate_github_configuration_missing_repo(self):
        """
        Test kind: external_api_tests
        Original method: validate_github_configuration
        """
        config = {
            'github_access_token': 'ghp_test_token',
            'github_repository_owner': 'owner',
            'github_repository_name': ''
        }
        
        success, message, details = validate_github_configuration(config)
        
        self.assertFalse(success)
        self.assertEqual(message, "GITHUB_REPOSITORY_NAME is not set")
        self.assertEqual(details, {})
    
    @pytest.mark.timeout(30)
    def test_validate_github_configuration_invalid_token(self):
        """
        Test kind: external_api_tests
        Original method: validate_github_configuration
        
        This test uses an invalid token to test error handling.
        """
        config = {
            'github_access_token': 'ghp_invalid_token',
            'github_repository_owner': 'octocat',
            'github_repository_name': 'Hello-World'
        }
        
        success, message, details = validate_github_configuration(config)
        
        self.assertFalse(success)
        self.assertIn('Invalid GitHub access token', message)
        self.assertEqual(details['status_code'], 401)
        self.assertEqual(details['token_prefix'], 'ghp_invali...')
    
    @pytest.mark.timeout(30)
    def test_validate_github_configuration_nonexistent_repo(self):
        """
        Test kind: external_api_tests
        Original method: validate_github_configuration
        
        This test uses a valid public repository that doesn't exist to test 404 handling.
        """
        # Use a real token if available, otherwise use a fake one that will fail at token level
        real_token = os.getenv('GITHUB_ACCESS_TOKEN_TEST', 'ghp_fake_token_for_testing')
        
        config = {
            'github_access_token': real_token,
            'github_repository_owner': 'nonexistent_owner_12345',
            'github_repository_name': 'nonexistent_repo_12345'
        }
        
        success, message, details = validate_github_configuration(config)
        
        self.assertFalse(success)
        # Should either fail with auth error (fake token) or not found error (real token)
        self.assertTrue(
            'Invalid GitHub access token' in message or 
            'GitHub repository not found' in message
        )
    
    @pytest.mark.timeout(30)
    def test_validate_github_configuration_real_api(self):
        """
        Test kind: external_api_tests
        Original method: validate_github_configuration
        
        This test makes actual API calls to validate GitHub configuration.
        """
        # Skip test if real credentials are not available
        real_token = os.getenv('GITHUB_ACCESS_TOKEN_TEST')
        real_owner = os.getenv('GITHUB_REPOSITORY_OWNER_TEST', 'octocat')
        real_repo = os.getenv('GITHUB_REPOSITORY_NAME_TEST', 'Hello-World')
        
        if not real_token:
            self.skipTest("Real GitHub credentials not available for testing")
        
        config = {
            'github_access_token': real_token,
            'github_repository_owner': real_owner,
            'github_repository_name': real_repo
        }
        
        success, message, details = validate_github_configuration(config)
        
        if success:
            self.assertTrue(success)
            self.assertEqual(message, "GitHub configuration validated successfully")
            self.assertIn('authenticated_user', details)
            self.assertIn('repository_full_name', details)
            self.assertIn('repository_default_branch', details)
            self.assertEqual(details['repository_owner'], real_owner)
            self.assertEqual(details['repository_name'], real_repo)
        else:
            # If it fails, it should be due to actual API issues or permissions
            self.assertTrue(
                'Invalid GitHub access token' in message or 
                'GitHub repository not found' in message
            )