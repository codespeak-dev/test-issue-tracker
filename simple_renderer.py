#!/usr/bin/env python3
"""
Simple template renderer using string replacement and basic template logic.
"""

import os
import json
import re
from pathlib import Path
from datetime import datetime


def load_template(template_path):
    """Load template content"""
    with open(template_path, 'r') as f:
        return f.read()


def process_value(value, context):
    """Process a template value through context"""
    if isinstance(value, str) and value.startswith('{{') and value.endswith('}}'):
        # Extract variable path
        var_path = value.strip('{}').strip()
        return get_nested_value(context, var_path)
    return value


def get_nested_value(data, path):
    """Get nested value from data using dot notation"""
    parts = path.split('.')
    current = data
    
    for part in parts:
        if isinstance(current, dict):
            current = current.get(part, '')
        elif hasattr(current, part):
            attr = getattr(current, part)
            if callable(attr):
                current = attr()
            else:
                current = attr
        else:
            return ''
    
    return current if current is not None else ''


def render_simple_template(template_content, context):
    """Simple template renderer with basic Django template syntax support"""
    
    # Handle {% extends 'base.html' %} - load base template
    extends_match = re.search(r'{%\s*extends\s+[\'"]([^\'"]+)[\'\"]\s*%}', template_content)
    if extends_match:
        base_template_name = extends_match.group(1)
        base_path = f'/Users/abreslav/codespeak/dogfooding/issue-tracker/templates/{base_template_name}'
        if os.path.exists(base_path):
            base_content = load_template(base_path)
            
            # Extract blocks from current template
            blocks = {}
            block_pattern = r'{%\s*block\s+(\w+)\s*%}(.*?){%\s*endblock\s*%}'
            for match in re.finditer(block_pattern, template_content, re.DOTALL):
                block_name = match.group(1)
                block_content = match.group(2).strip()
                blocks[block_name] = block_content
            
            # Replace blocks in base template
            def replace_block(match):
                block_name = match.group(1)
                default_content = match.group(2).strip() if match.group(2) else ''
                return blocks.get(block_name, default_content)
            
            template_content = re.sub(r'{%\s*block\s+(\w+)\s*%}(.*?){%\s*endblock\s*%}', replace_block, base_content, flags=re.DOTALL)
    
    # Remove {% load static %} tags
    template_content = re.sub(r'{%\s*load\s+\w+\s*%}', '', template_content)
    
    # Handle simple variable substitution {{ variable }}
    def replace_var(match):
        var_path = match.group(1).strip()
        
        # Handle filters like |date:"M d, Y"
        if '|' in var_path:
            var_name, filters = var_path.split('|', 1)
            value = get_nested_value(context, var_name.strip())
            
            # Simple date filter
            if 'date:' in filters:
                if isinstance(value, str) and 'T' in value:
                    try:
                        dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
                        return dt.strftime('%b %d, %Y')
                    except:
                        pass
            
            # Truncate filter
            if 'truncatechars:' in filters:
                if isinstance(value, str) and len(value) > 50:
                    return value[:47] + '...'
            
            # Safe filter (just return as-is for HTML content)
            if 'safe' in filters:
                return str(value)
            
            return str(value)
        
        value = get_nested_value(context, var_path)
        return str(value) if value is not None else ''
    
    template_content = re.sub(r'{{([^}]+)}}', replace_var, template_content)
    
    # Handle {% url 'name' %} tags (replace with placeholder URLs)
    url_replacements = {
        'issue_list': '/',
        'issue_create': '/issues/new/',
        'issue_detail': '/issues/1/',
        'issue_edit': '/issues/1/edit/',
        'comment_create': '/issues/1/comments/',
        'tag_list': '/tags/',
        'tag_create': '/tags/new/',
        'tag_edit': '/tags/1/edit/',
        'settings': '/settings/',
        'login': '/login/',
        'logout': '/logout/',
        'register': '/register/'
    }
    
    def replace_url(match):
        url_name = match.group(1).strip('\'"')
        return url_replacements.get(url_name, f'/{url_name}/')
    
    template_content = re.sub(r'{%\s*url\s+[\'"]([^\'"]+)[\'"].*?%}', replace_url, template_content)
    
    # Handle {% csrf_token %}
    template_content = re.sub(r'{%\s*csrf_token\s*%}', '<input type="hidden" name="csrfmiddlewaretoken" value="csrf_token_placeholder">', template_content)
    
    # Handle {% if %} conditionals (simple cases)
    def process_if_blocks(content):
        # Simple if user.is_authenticated
        if_pattern = r'{%\s*if\s+([^%]+)\s*%}(.*?)(?:{%\s*else\s*%}(.*?))?{%\s*endif\s*%}'
        
        def replace_if(match):
            condition = match.group(1).strip()
            if_content = match.group(2)
            else_content = match.group(3) or ''
            
            # Evaluate simple conditions
            if condition == 'user.is_authenticated':
                is_auth = get_nested_value(context, 'user.is_authenticated')
                return if_content if is_auth else else_content
            elif condition == 'user.is_staff':
                is_staff = get_nested_value(context, 'user.is_staff')
                return if_content if is_staff else else_content
            elif condition in ['messages', 'issues', 'comments', 'tags']:
                items = get_nested_value(context, condition)
                has_items = bool(items) and (not hasattr(items, '__len__') or len(items) > 0)
                return if_content if has_items else else_content
            elif condition.startswith('issue.'):
                value = get_nested_value(context, condition)
                return if_content if value else else_content
            elif 'search_query or selected_tags' in condition:
                search = get_nested_value(context, 'search_query')
                tags = get_nested_value(context, 'selected_tags')
                has_filter = bool(search) or (bool(tags) and len(tags) > 0)
                return if_content if has_filter else else_content
            elif 'and issue.author == user' in condition:
                return else_content  # Default to else for complex conditions
            elif '==' in condition or '!=' in condition:
                # Simple equality checks - default to false for safety
                return else_content
            else:
                # Default case - assume false
                return else_content
        
        return re.sub(if_pattern, replace_if, content, flags=re.DOTALL)
    
    template_content = process_if_blocks(template_content)
    
    # Handle {% for %} loops
    def process_for_blocks(content):
        for_pattern = r'{%\s*for\s+(\w+)\s+in\s+([^%]+)\s*%}(.*?)(?:{%\s*empty\s*%}(.*?))?{%\s*endfor\s*%}'
        
        def replace_for(match):
            loop_var = match.group(1)
            iterable_path = match.group(2).strip()
            loop_content = match.group(3)
            empty_content = match.group(4) or ''
            
            items = get_nested_value(context, iterable_path)
            if not items or (hasattr(items, '__len__') and len(items) == 0):
                return empty_content
            
            result = ''
            if hasattr(items, '__iter__') and not isinstance(items, str):
                for item in items:
                    # Create new context with loop variable
                    loop_context = context.copy()
                    loop_context[loop_var] = item
                    
                    # Simple variable replacement in loop content
                    loop_html = loop_content
                    loop_html = re.sub(r'{{([^}]+)}}', lambda m: str(get_nested_value(loop_context, m.group(1).strip())), loop_html)
                    
                    result += loop_html
            
            return result
        
        return re.sub(for_pattern, replace_for, content, flags=re.DOTALL)
    
    template_content = process_for_blocks(template_content)
    
    # Clean up remaining template tags
    template_content = re.sub(r'{%[^%]*%}', '', template_content)
    
    return template_content


def create_mock_context(json_data):
    """Create a mock context from JSON data"""
    
    class MockObject:
        def __init__(self, data):
            if isinstance(data, dict):
                for key, value in data.items():
                    if isinstance(value, dict):
                        setattr(self, key, MockObject(value))
                    elif isinstance(value, list):
                        setattr(self, key, [MockObject(item) if isinstance(item, dict) else item for item in value])
                    else:
                        setattr(self, key, value)
        
        def __bool__(self):
            return True
        
        def __len__(self):
            return 1
    
    context = {}
    for key, value in json_data.items():
        if isinstance(value, dict):
            context[key] = MockObject(value)
        elif isinstance(value, list):
            context[key] = [MockObject(item) if isinstance(item, dict) else item for item in value]
        else:
            context[key] = value
    
    # Add empty messages by default
    if 'messages' not in context:
        context['messages'] = []
    
    return context


def render_template_file(template_path, json_path, output_path):
    """Render template file with JSON data"""
    try:
        # Load template
        template_content = load_template(template_path)
        
        # Load JSON data
        with open(json_path, 'r') as f:
            json_data = json.load(f)
        
        # Create context
        context = create_mock_context(json_data)
        
        # Render template
        html = render_simple_template(template_content, context)
        
        # Write output
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w') as f:
            f.write(html)
        
        print(f"✓ Rendered {os.path.basename(template_path)} -> {os.path.basename(output_path)}")
        return True
        
    except Exception as e:
        print(f"✗ Error rendering {template_path}: {e}")
        return False


def main():
    """Main function"""
    base_dir = Path('/Users/abreslav/codespeak/dogfooding/issue-tracker')
    templates_dir = base_dir / 'templates'
    ui_examples_dir = base_dir / 'ui_examples'
    
    success_count = 0
    total_count = 0
    
    # Process all JSON files
    for json_file in ui_examples_dir.rglob('*.json'):
        if json_file.name == 'state_descriptions.json':
            continue
            
        # Extract template path
        rel_path = json_file.relative_to(ui_examples_dir)
        path_parts = list(rel_path.parts[:-1])  # Remove filename
        
        if not path_parts[-1].endswith('.html'):
            continue
        
        # Remove the 'templates' prefix if it exists
        if path_parts[0] == 'templates':
            path_parts = path_parts[1:]
        
        template_name = path_parts[-1]
        template_path = templates_dir / '/'.join(path_parts)
        
        if not template_path.exists():
            print(f"Template not found: {template_path}")
            continue
        
        # Create output path
        state_name = json_file.stem
        output_path = json_file.parent / f'{state_name}.html'
        
        total_count += 1
        if render_template_file(str(template_path), str(json_file), str(output_path)):
            success_count += 1
    
    print(f"\\nCompleted: {success_count}/{total_count} templates rendered successfully")


if __name__ == '__main__':
    main()