"""
Unit tests for form methods
"""

import pytest
from django.test import TestCase
from django.core.exceptions import ValidationError
from issues.forms import LoginForm, RegisterForm, IssueForm
from issues.models import User


class TestFormMethods(TestCase):
    """Test class for form method unit tests"""
    
    def setUp(self):
        """Set up test data"""
        # Create a test user
        self.test_user = User.objects.create_user(
            email='test@example.com',
            name='Test User'
        )
    
    @pytest.mark.timeout(30)
    def test_login_form_clean_email_valid_user(self):
        """
        Test kind: unit_tests
        Original method: LoginForm.clean_email
        """
        form = LoginForm(data={'email': 'test@example.com'})
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['email'], 'test@example.com')
    
    @pytest.mark.timeout(30)
    def test_login_form_clean_email_invalid_user(self):
        """
        Test kind: unit_tests
        Original method: LoginForm.clean_email
        """
        form = LoginForm(data={'email': 'nonexistent@example.com'})
        self.assertFalse(form.is_valid())
        self.assertIn('No account found with this email', str(form.errors['email']))
    
    @pytest.mark.timeout(30)
    def test_login_form_clean_email_empty(self):
        """
        Test kind: unit_tests
        Original method: LoginForm.clean_email
        """
        form = LoginForm(data={'email': ''})
        self.assertFalse(form.is_valid())
        self.assertIn('This field is required', str(form.errors['email']))
    
    @pytest.mark.timeout(30)
    def test_register_form_clean_email_new_user(self):
        """
        Test kind: unit_tests
        Original method: RegisterForm.clean_email
        """
        form = RegisterForm(data={
            'email': 'newuser@example.com',
            'name': 'New User'
        })
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['email'], 'newuser@example.com')
    
    @pytest.mark.timeout(30)
    def test_register_form_clean_email_existing_user(self):
        """
        Test kind: unit_tests
        Original method: RegisterForm.clean_email
        """
        form = RegisterForm(data={
            'email': 'test@example.com',
            'name': 'Duplicate User'
        })
        self.assertFalse(form.is_valid())
        self.assertIn('An account with this email already exists', str(form.errors['email']))
    
    @pytest.mark.timeout(30)
    def test_register_form_clean_email_empty(self):
        """
        Test kind: unit_tests
        Original method: RegisterForm.clean_email
        """
        form = RegisterForm(data={'email': '', 'name': 'Test Name'})
        self.assertFalse(form.is_valid())
        self.assertIn('This field is required', str(form.errors['email']))
    
    @pytest.mark.timeout(30)
    def test_issue_form_init_without_args(self):
        """
        Test kind: unit_tests
        Original method: IssueForm.__init__
        """
        form = IssueForm()
        # Test that assignee field is properly configured
        self.assertFalse(form.fields['assignee'].required)
        self.assertEqual(form.fields['assignee'].empty_label, "Unassigned")
    
    @pytest.mark.timeout(30)
    def test_issue_form_init_with_instance(self):
        """
        Test kind: unit_tests
        Original method: IssueForm.__init__
        """
        # Create a minimal issue instance for testing
        from issues.models import Status
        status, _ = Status.objects.get_or_create(name='Open', defaults={'is_open': True})
        
        # Create test data for the form
        initial_data = {
            'summary': 'Test Issue',
            'description': 'Test description',
            'status': status.id,
        }
        
        form = IssueForm(data=initial_data)
        
        # Test that assignee field is properly configured even with data
        self.assertFalse(form.fields['assignee'].required)
        self.assertEqual(form.fields['assignee'].empty_label, "Unassigned")
        
        # Form should be valid with minimal required fields
        self.assertTrue(form.is_valid())