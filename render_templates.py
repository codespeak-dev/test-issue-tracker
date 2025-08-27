#!/usr/bin/env python3
"""
Template renderer for generating HTML files from Django templates and JSON data.
"""

import os
import sys
import django
import json
from pathlib import Path
from datetime import datetime
from django.template import Template, Context
from django.template.loader import get_template
from django.conf import settings

# Add the project directory to Python path
sys.path.append('/Users/abreslav/codespeak/dogfooding/issue-tracker')

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bugger.settings')

try:
    django.setup()
except Exception as e:
    print(f"Error setting up Django: {e}")
    # If Django setup fails, we'll create a minimal configuration
    if not settings.configured:
        settings.configure(
            DEBUG=True,
            TEMPLATES=[{
                'BACKEND': 'django.template.backends.django.DjangoTemplates',
                'DIRS': ['/Users/abreslav/codespeak/dogfooding/issue-tracker/templates'],
                'APP_DIRS': True,
                'OPTIONS': {
                    'context_processors': [],
                },
            }],
            USE_TZ=True,
        )
        django.setup()

from django.template.loader import get_template


class MockUser:
    """Mock user object to simulate Django user"""
    def __init__(self, data):
        if isinstance(data, dict):
            self.is_authenticated = data.get('is_authenticated', False)
            self.name = data.get('name', 'Anonymous')
            self.is_staff = data.get('is_staff', False)
            self.id = data.get('id', None)
        else:
            self.is_authenticated = False
            self.name = 'Anonymous'
            self.is_staff = False
            self.id = None


class MockObject:
    """Mock Django model object"""
    def __init__(self, data):
        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, dict):
                    setattr(self, key, MockObject(value))
                elif isinstance(value, list):
                    setattr(self, key, [MockObject(item) if isinstance(item, dict) else item for item in value])
                else:
                    setattr(self, key, value)
        else:
            self.value = data
    
    def __str__(self):
        return getattr(self, 'name', getattr(self, 'summary', str(getattr(self, 'value', 'MockObject'))))
    
    def all(self):
        """Simulate Django QuerySet all() method"""
        if hasattr(self, 'all_items'):
            return self.all_items
        return []
    
    def count(self):
        """Simulate Django QuerySet count() method"""
        if hasattr(self, 'all_items'):
            return len(self.all_items)
        return 0
    
    def exists(self):
        """Simulate Django QuerySet exists() method"""
        if hasattr(self, 'all_items'):
            return len(self.all_items) > 0
        return False


class MockForm:
    """Mock Django form"""
    def __init__(self, data):
        if isinstance(data, dict):
            for key, value in data.items():
                setattr(self, key, MockFormField(value) if isinstance(value, dict) else value)
        self.data = data or {}


class MockFormField:
    """Mock Django form field"""
    def __init__(self, data):
        if isinstance(data, dict):
            self.id_for_label = data.get('id_for_label', f'id_{hash(str(data))}')
            self.errors = data.get('errors', [])
            self.label = data.get('label', '')
            self.value = data.get('value', '')
        else:
            self.id_for_label = f'id_{hash(str(data))}'
            self.errors = []
            self.label = str(data)
            self.value = data
    
    def __str__(self):
        return f'<input id="{self.id_for_label}" value="{self.value}">'


def process_context_data(data):
    """Convert JSON data to Django-like objects"""
    processed = {}
    
    for key, value in data.items():
        if key == 'user':
            processed[key] = MockUser(value)
        elif key == 'form':
            processed[key] = MockForm(value)
        elif key in ['issue', 'comment', 'tag'] or key.endswith('s'):  # Handle models and querysets
            if isinstance(value, list):
                processed[key] = [MockObject(item) if isinstance(item, dict) else item for item in value]
            elif isinstance(value, dict):
                processed[key] = MockObject(value)
            else:
                processed[key] = value
        else:
            processed[key] = value
    
    # Add common template context variables
    processed.update({
        'messages': [],  # No messages by default
        'request': type('MockRequest', (), {'user': processed.get('user', MockUser({}))})(),
    })
    
    return processed


def render_template_with_data(template_path, data_path, output_path):
    """Render a Django template with JSON data"""
    try:
        # Load JSON data
        with open(data_path, 'r') as f:
            json_data = json.load(f)
        
        # Process context data
        context_data = process_context_data(json_data)
        
        # Load and render template
        template = get_template(template_path)
        context = Context(context_data)
        rendered_html = template.render(context)
        
        # Write output
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w') as f:
            f.write(rendered_html)
        
        print(f"Rendered {template_path} -> {output_path}")
        return True
        
    except Exception as e:
        print(f"Error rendering {template_path} with {data_path}: {e}")
        return False


def main():
    """Main function to render all templates"""
    base_dir = Path('/Users/abreslav/codespeak/dogfooding/issue-tracker')
    ui_examples_dir = base_dir / 'ui_examples'
    
    # Track success/failure
    success_count = 0
    total_count = 0
    
    # Find all JSON files in the ui_examples directory
    for json_file in ui_examples_dir.rglob('*.json'):
        if json_file.name == 'state_descriptions.json':
            continue
        
        # Extract template path and state name from file path
        rel_path = json_file.relative_to(ui_examples_dir)
        path_parts = list(rel_path.parts[:-1])  # Remove .json filename
        state_name = json_file.stem
        
        # Construct template path
        template_path = '/'.join(path_parts)
        
        # Skip if not a template file
        if not template_path.endswith('.html'):
            continue
        
        # Construct output path
        output_dir = ui_examples_dir / Path(*path_parts[:-1]) / json_file.stem
        output_path = output_dir / f'{state_name}.html'
        
        total_count += 1
        if render_template_with_data(template_path, str(json_file), str(output_path)):
            success_count += 1
    
    print(f"\\nCompleted: {success_count}/{total_count} templates rendered successfully")


if __name__ == '__main__':
    main()