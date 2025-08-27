#!/usr/bin/env python3
"""
Django Template Renderer for the template editor server.
Based on the logic from django_template_renderer.py.
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, Any

# Setup Django environment
import django
from django.conf import settings
from django.template import Template, Context
from django.template.loader import get_template
from django.template.engine import Engine
from django.urls import reverse_lazy
from django.utils.safestring import mark_safe


class MockCSRFToken:
    """Mock CSRF token for templates."""
    def __str__(self):
        return '<input type="hidden" name="csrfmiddlewaretoken" value="mock-csrf-token-12345" />'


class MockUser:
    """Mock user object that behaves like Django's User."""
    def __init__(self, data):
        self.is_authenticated = data.get('is_authenticated', False)
        self.name = data.get('name', '')
        self.is_staff = data.get('is_staff', False)
        
    def __bool__(self):
        return self.is_authenticated


class MockMessage:
    """Mock message object for Django messages framework."""
    def __init__(self, message, tags='info'):
        self.message = message
        self.tags = tags
        
    def __str__(self):
        return self.message


class MockQuerySet:
    """Mock QuerySet that provides Django-like interface for JSON data."""
    def __init__(self, data_list):
        self.data_list = data_list or []
        
    def __iter__(self):
        return iter(self.data_list)
        
    def __len__(self):
        return len(self.data_list)
        
    def __bool__(self):
        return len(self.data_list) > 0
    
    def all(self):
        return MockQuerySet(self.data_list)
    
    def count(self):
        return len(self.data_list)
    
    def exists(self):
        return len(self.data_list) > 0


class MockModel:
    """Mock model that converts JSON data to Django-like objects."""
    def __init__(self, data):
        if isinstance(data, dict):
            for key, value in data.items():
                if key == 'tags' and isinstance(value, dict) and 'all' in value:
                    # Handle tags.all structure
                    setattr(self, key, MockTags(value))
                elif isinstance(value, dict):
                    setattr(self, key, MockModel(value))
                elif isinstance(value, list):
                    setattr(self, key, MockQuerySet([MockModel(item) if isinstance(item, dict) else item for item in value]))
                else:
                    setattr(self, key, value)
        else:
            # Handle primitive values
            for attr in ['id', 'pk', 'name', 'summary', 'description', 'color']:
                setattr(self, attr, data)


class MockTags:
    """Mock tags manager that handles tags.all queries."""
    def __init__(self, data):
        self.all_data = data.get('all', [])
        
    def all(self):
        return MockQuerySet([MockModel(item) for item in self.all_data])
    
    def exists(self):
        return len(self.all_data) > 0


class MockFormField:
    """Mock form field that provides Django form field interface."""
    def __init__(self, field_name, field_html, errors=None, value=None):
        self.field_name = field_name
        self.field_html = mark_safe(field_html)
        self.errors = errors or []
        self._value = value
        # Extract ID from HTML for id_for_label
        import re
        id_match = re.search(r'id="([^"]*)"', field_html)
        self._id = id_match.group(1) if id_match else f"id_{field_name}"
        
        # Extract value from HTML if not provided
        if value is None:
            value_match = re.search(r'value="([^"]*)"', field_html)
            self._value = value_match.group(1) if value_match else ""
    
    def __str__(self):
        return self.field_html
        
    @property
    def id_for_label(self):
        return self._id
        
    def value(self):
        return self._value


def mock_url(name, *args, **kwargs):
    """Mock URL function that generates placeholder URLs."""
    url_patterns = {
        'issue_list': '/',
        'issue_detail': f'/issue/{args[0]}/' if args else '/issue/1/',
        'issue_create': '/issue/new/',
        'issue_edit': f'/issue/{args[0]}/edit/' if args else '/issue/1/edit/',
        'comment_create': f'/issue/{kwargs.get("issue_pk", args[0] if args else "1")}/comment/',
        'login': '/login/',
        'logout': '/logout/',
        'register': '/register/',
        'settings': '/settings/',
        'tag_list': '/tags/',
        'tag_create': '/tags/new/',
        'tag_edit': f'/tags/{args[0]}/edit/' if args else '/tags/1/edit/',
    }
    return url_patterns.get(name, f'/{name}/')


class DjangoTemplateRenderer:
    """Renders Django templates using the actual Django template engine."""
    
    def __init__(self, template_dir: str):
        self.template_dir = Path(template_dir)
        
        # Configure Django settings
        if not settings.configured:
            settings.configure(
                DEBUG=True,
                SECRET_KEY='mock-secret-key-for-template-rendering',
                USE_TZ=True,
                ROOT_URLCONF='urls',
                TEMPLATES=[{
                    'BACKEND': 'django.template.backends.django.DjangoTemplates',
                    'DIRS': [str(self.template_dir)],
                    'OPTIONS': {
                        'context_processors': [],
                        'builtins': [
                            'django.template.defaulttags',
                            'django.template.defaultfilters',
                        ],
                    },
                }],
                INSTALLED_APPS=[
                    'django.contrib.contenttypes',
                ],
            )
            django.setup()
    
    def prepare_context(self, context_data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert JSON context data to Django-compatible objects."""
        context = {}
        
        for key, value in context_data.items():
            if key == 'user':
                context[key] = MockUser(value) if isinstance(value, dict) else value
            elif key == 'messages':
                context[key] = [MockMessage(msg['message'], msg.get('tags', 'info')) for msg in value] if isinstance(value, list) else value
            elif key == 'issues' and isinstance(value, list):
                context[key] = MockQuerySet([MockModel(item) for item in value])
            elif key in ['all_tags', 'tags'] and isinstance(value, list):
                context[key] = MockQuerySet([MockModel(item) for item in value])
            elif key == 'issue' and isinstance(value, dict):
                context[key] = MockModel(value)
            elif key in ['form', 'comment_form'] and isinstance(value, dict):
                # Handle form data - create mock form fields for better Django compatibility
                form_data = {}
                for field_name, field_value in value.items():
                    if field_name.endswith('_errors'):
                        # Keep error lists as-is
                        form_data[field_name] = field_value
                    elif isinstance(field_value, str) and '<' in field_value:
                        # Create MockFormField for HTML form fields
                        errors_key = f"{field_name}_errors"
                        errors = value.get(errors_key, [])
                        form_data[field_name] = MockFormField(field_name, field_value, errors)
                    else:
                        form_data[field_name] = field_value
                context[key] = form_data
            elif isinstance(value, dict):
                context[key] = MockModel(value)
            elif isinstance(value, list):
                context[key] = [MockModel(item) if isinstance(item, dict) else item for item in value]
            else:
                context[key] = value
        
        # Add CSRF token
        context['csrf_token'] = MockCSRFToken()
        
        return context
    
    def render_template(self, template_path: str, context_data: Dict[str, Any]) -> str:
        """Render a Django template with the given context."""
        try:
            # Load the template using Django's template loader
            template = get_template(template_path)
            
            # Prepare the context
            django_context = self.prepare_context(context_data)
            
            # Create Django context with URL function
            django_context['url'] = mock_url
            
            # Render the template
            rendered = template.render(django_context)
            
            return rendered
            
        except Exception as e:
            print(f"Error rendering template {template_path}: {e}")
            import traceback
            traceback.print_exc()
            return f"<html><body><h1>Template Rendering Error</h1><p>{e}</p></body></html>"