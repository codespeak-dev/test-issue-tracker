"""
Unit tests for middleware and utility functions
"""

import pytest
import json
import time
from unittest.mock import Mock, patch, MagicMock
from django.test import TestCase, RequestFactory
from django.http import HttpResponse
from django.utils import timezone
from issues.middleware import RequestLoggingMiddleware
from issues.views import log_request_response
from src.external_apis.validate_configuration import load_configuration


class TestRequestLoggingMiddleware(TestCase):
    """Test class for RequestLoggingMiddleware unit tests"""
    
    def setUp(self):
        """Set up test data"""
        self.factory = RequestFactory()
        self.middleware = RequestLoggingMiddleware(Mock())
    
    @pytest.mark.timeout(30)
    def test_process_request(self):
        """
        Test kind: unit_tests
        Original method: RequestLoggingMiddleware.process_request
        """
        request = self.factory.get('/test/')
        
        # Process request should set start time and return None
        result = self.middleware.process_request(request)
        
        self.assertIsNone(result)
        self.assertTrue(hasattr(request, '_start_time'))
        self.assertIsInstance(request._start_time, float)
        
        # Start time should be close to current time
        self.assertAlmostEqual(request._start_time, time.time(), delta=1.0)
    
    @pytest.mark.timeout(30)
    @patch('issues.middleware.logger')
    def test_process_response_with_start_time(self, mock_logger):
        """
        Test kind: unit_tests
        Original method: RequestLoggingMiddleware.process_response
        """
        request = self.factory.post('/test/', data={'key': 'value'})
        request._start_time = time.time() - 0.1  # 100ms ago
        response = HttpResponse('Test response', status=200)
        response['Content-Type'] = 'text/html'
        
        result = self.middleware.process_response(request, response)
        
        # Should return the original response
        self.assertEqual(result, response)
        
        # Should log the request-response data
        self.assertTrue(mock_logger.info.called)
        log_call_args = mock_logger.info.call_args[0][0]
        log_data = json.loads(log_call_args)
        
        self.assertEqual(log_data['method'], 'POST')
        self.assertEqual(log_data['url'], '/test/')
        self.assertEqual(log_data['response_status'], 200)
        self.assertIsInstance(log_data['duration_ms'], float)
        self.assertGreater(log_data['duration_ms'], 0)
        self.assertIn('timestamp', log_data)
    
    @pytest.mark.timeout(30)
    @patch('issues.middleware.logger')
    def test_process_response_without_start_time(self, mock_logger):
        """
        Test kind: unit_tests
        Original method: RequestLoggingMiddleware.process_response
        """
        request = self.factory.get('/test/')
        # No _start_time attribute
        response = HttpResponse('Test response', status=200)
        
        result = self.middleware.process_response(request, response)
        
        # Should return the original response
        self.assertEqual(result, response)
        
        # Should log without duration
        self.assertTrue(mock_logger.info.called)
        log_call_args = mock_logger.info.call_args[0][0]
        log_data = json.loads(log_call_args)
        
        self.assertIsNone(log_data['duration_ms'])
    
    @pytest.mark.timeout(30)
    @patch('issues.middleware.logger')
    def test_process_response_error_status(self, mock_logger):
        """
        Test kind: unit_tests
        Original method: RequestLoggingMiddleware.process_response
        """
        request = self.factory.get('/test/')
        request._start_time = time.time()
        response = HttpResponse('Error response', status=500)
        
        result = self.middleware.process_response(request, response)
        
        # Should return the original response
        self.assertEqual(result, response)
        
        # Should log with response body for error status
        self.assertTrue(mock_logger.info.called)
        log_call_args = mock_logger.info.call_args[0][0]
        log_data = json.loads(log_call_args)
        
        self.assertEqual(log_data['response_status'], 500)
        self.assertEqual(log_data['response_body'], 'Error response')


class TestLogRequestResponse(TestCase):
    """Test class for log_request_response utility function"""
    
    def setUp(self):
        """Set up test data"""
        self.factory = RequestFactory()
    
    @pytest.mark.timeout(30)
    @patch('issues.views.logger')
    @patch('issues.views.timezone')
    def test_log_request_response_success(self, mock_timezone, mock_logger):
        """
        Test kind: unit_tests
        Original method: log_request_response
        """
        mock_timezone.now.return_value.isoformat.return_value = '2023-01-01T00:00:00'
        
        request = self.factory.post('/test/', data={'key': 'value'})
        request.headers = {'Content-Type': 'application/json'}
        # Create a property mock for the body attribute
        def mock_body():
            return b'{"key": "value"}'
        
        with patch.object(type(request), 'body', property(lambda self: b'{"key": "value"}')):
            response = HttpResponse('Success response', status=200)
            response['Content-Type'] = 'text/html'
            
            log_request_response(request, response)
            
            # Should log the request-response data
            self.assertTrue(mock_logger.info.called)
            log_call_args = mock_logger.info.call_args[0][0]
            log_data = json.loads(log_call_args)
            
            self.assertEqual(log_data['method'], 'POST')
            self.assertEqual(log_data['url'], '/test/')
            self.assertEqual(log_data['body_size'], len(b'{"key": "value"}'))
            self.assertEqual(log_data['response_status'], 200)
            self.assertEqual(log_data['timestamp'], '2023-01-01T00:00:00')
    
    @pytest.mark.timeout(30)
    @patch('issues.views.logger')
    @patch('issues.views.timezone')
    def test_log_request_response_error_status(self, mock_timezone, mock_logger):
        """
        Test kind: unit_tests
        Original method: log_request_response
        """
        mock_timezone.now.return_value.isoformat.return_value = '2023-01-01T00:00:00'
        
        request = self.factory.get('/test/')
        response = HttpResponse('Error response content', status=404)
        
        log_request_response(request, response)
        
        # Should log with response body for error status
        self.assertTrue(mock_logger.info.called)
        log_call_args = mock_logger.info.call_args[0][0]
        log_data = json.loads(log_call_args)
        
        self.assertEqual(log_data['response_status'], 404)
        self.assertEqual(log_data['response_body'], 'Error response content')


class TestLoadConfiguration(TestCase):
    """Test class for load_configuration utility function"""
    
    @pytest.mark.timeout(30)
    @patch('src.external_apis.validate_configuration.os.path.exists')
    @patch('src.external_apis.validate_configuration.sys.exit')
    def test_load_configuration_no_file(self, mock_exit, mock_exists):
        """
        Test kind: unit_tests
        Original method: load_configuration
        """
        mock_exists.return_value = False
        
        load_configuration()
        
        # Should call sys.exit when file doesn't exist
        mock_exit.assert_called_once_with(1)
    
    @pytest.mark.timeout(30)
    @patch('src.external_apis.validate_configuration.os.path.exists')
    @patch('src.external_apis.validate_configuration.load_dotenv')
    @patch('src.external_apis.validate_configuration.os.getenv')
    def test_load_configuration_success(self, mock_getenv, mock_load_dotenv, mock_exists):
        """
        Test kind: unit_tests
        Original method: load_configuration
        """
        mock_exists.return_value = True
        mock_getenv.side_effect = lambda key: {
            'SLACK_BOT_TOKEN': 'test_slack_token',
            'SLACK_CHANNEL_ID': 'test_channel_id',
            'GITHUB_ACCESS_TOKEN': 'test_github_token',
            'GITHUB_REPOSITORY_OWNER': 'test_owner',
            'GITHUB_REPOSITORY_NAME': 'test_repo'
        }.get(key)
        
        result = load_configuration()
        
        # Should load dotenv and return config
        mock_load_dotenv.assert_called_once_with('.env.local')
        
        expected_config = {
            'slack_bot_token': 'test_slack_token',
            'slack_channel_id': 'test_channel_id',
            'github_access_token': 'test_github_token',
            'github_repository_owner': 'test_owner',
            'github_repository_name': 'test_repo'
        }
        self.assertEqual(result, expected_config)