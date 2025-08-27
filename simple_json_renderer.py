#!/usr/bin/env python3
"""
Simple JSON-based template renderer that uses raw JSON data without mocking objects.
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


def get_nested_value(data, path, default=''):
    """Get nested value from data using dot notation"""
    if not path or not isinstance(data, dict):
        return default
        
    parts = path.split('.')
    current = data
    
    for part in parts:
        if isinstance(current, dict):
            current = current.get(part, default)
        elif isinstance(current, list):
            if part.isdigit():
                idx = int(part)
                current = current[idx] if idx < len(current) else default
            elif part == 'length':
                return len(current)
            else:
                return default
        else:
            return default
    
    return current if current is not None else default


def evaluate_condition(condition, context):
    """Evaluate template conditions"""
    condition = condition.strip()
    
    # Handle simple boolean checks
    if condition == 'user.is_authenticated':
        return bool(get_nested_value(context, 'user.is_authenticated'))
    elif condition == 'user.is_staff':
        return bool(get_nested_value(context, 'user.is_staff'))
    elif condition == 'messages':
        messages = get_nested_value(context, 'messages', [])
        return bool(messages) and len(messages) > 0
    elif condition in ['issues', 'comments', 'tags', 'edit_history']:
        items = get_nested_value(context, condition, [])
        return bool(items) and len(items) > 0
    elif condition == 'all_tags':
        items = get_nested_value(context, 'all_tags', [])
        return bool(items) and len(items) > 0
    elif condition == 'search_query or selected_tags':
        search = get_nested_value(context, 'search_query', '')
        tags = get_nested_value(context, 'selected_tags', [])
        return bool(search) or (bool(tags) and len(tags) > 0)
    elif condition == 'issue.is_deleted':
        return bool(get_nested_value(context, 'issue.is_deleted'))
    elif condition == 'issue.description':
        desc = get_nested_value(context, 'issue.description', '')
        return bool(desc.strip())
    elif condition == 'issue.assignee':
        return bool(get_nested_value(context, 'issue.assignee'))
    elif condition == 'issue.tags.exists':
        return bool(get_nested_value(context, 'issue.tags.exists'))
    elif condition == 'comment_form':
        return bool(get_nested_value(context, 'comment_form'))
    elif condition.startswith('form.') and '.errors' in condition:
        # Try the new error format first (field_name_errors)
        field_name = condition.replace('form.', '').replace('.errors', '')
        errors = get_nested_value(context, f'form.{field_name}_errors', [])
        if not errors:
            # Fall back to old format
            errors = get_nested_value(context, condition, [])
        return bool(errors) and len(errors) > 0
    elif 'and issue.author == user' in condition:
        issue_author_id = get_nested_value(context, 'issue.author.id')
        user_id = get_nested_value(context, 'user.id')
        return issue_author_id and user_id and issue_author_id == user_id
    elif 'and comment.author == user' in condition:
        return False  # Simplify for now
    elif '==' in condition:
        parts = condition.split('==')
        if len(parts) == 2:
            left = get_nested_value(context, parts[0].strip())
            right = parts[1].strip().strip('\'"')
            return str(left) == right
    
    # Default to False for unknown conditions
    return False


def process_for_loop(content, loop_var, iterable_path, context, empty_content=''):
    """Process a for loop"""
    items = get_nested_value(context, iterable_path, [])
    
    if not items or (isinstance(items, list) and len(items) == 0):
        return empty_content
    
    result = ''
    if isinstance(items, list):
        for item in items:
            # Create new context with loop variable
            loop_context = context.copy()
            loop_context[loop_var] = item
            
            # Recursively process the loop content
            loop_result = render_template_content(content, loop_context)
            result += loop_result
    
    return result


def render_template_content(template_content, context):
    """Render template content with context"""
    
    # Handle {% extends %} - process base template first
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
                block_content = match.group(2)
                blocks[block_name] = block_content
            
            # Replace blocks in base template
            def replace_block(match):
                block_name = match.group(1)
                default_content = match.group(2) if match.group(2) else ''
                return blocks.get(block_name, default_content)
            
            template_content = re.sub(r'{%\s*block\s+(\w+)\s*%}(.*?){%\s*endblock\s*%}', replace_block, base_content, flags=re.DOTALL)
    
    # Remove {% load %} tags
    template_content = re.sub(r'{%\s*load\s+[^%]+%}', '', template_content)
    
    # Process {% for %} loops first (innermost first)
    max_iterations = 10
    iteration = 0
    while re.search(r'{%\s*for\s+\w+\s+in\s+[^%]+\s*%}', template_content) and iteration < max_iterations:
        for_pattern = r'{%\s*for\s+(\w+)\s+in\s+([^%]+?)\s*%}(.*?)(?:{%\s*empty\s*%}(.*?))?{%\s*endfor\s*%}'
        
        def replace_for(match):
            loop_var = match.group(1)
            iterable_path = match.group(2).strip()
            loop_content = match.group(3)
            empty_content = match.group(4) or ''
            
            return process_for_loop(loop_content, loop_var, iterable_path, context, empty_content)
        
        template_content = re.sub(for_pattern, replace_for, template_content, flags=re.DOTALL)
        iteration += 1
    
    # Process {% if %} conditionals
    max_iterations = 10
    iteration = 0
    while re.search(r'{%\s*if\s+[^%]+\s*%}', template_content) and iteration < max_iterations:
        if_pattern = r'{%\s*if\s+([^%]+?)\s*%}(.*?)(?:{%\s*else\s*%}(.*?))?{%\s*endif\s*%}'
        
        def replace_if(match):
            condition = match.group(1)
            if_content = match.group(2)
            else_content = match.group(3) or ''
            
            if evaluate_condition(condition, context):
                return if_content
            else:
                return else_content
        
        template_content = re.sub(if_pattern, replace_if, template_content, flags=re.DOTALL)
        iteration += 1
    
    # Handle variable substitution {{ variable }}
    def replace_var(match):
        var_expression = match.group(1).strip()
        
        # Handle special cases for length
        if '|length' in var_expression:
            var_path = var_expression.replace('|length', '').strip()
            value = get_nested_value(context, var_path, [])
            if isinstance(value, list):
                return str(len(value))
            return '0'
        
        # Handle filters
        if '|' in var_expression:
            var_path, filters = var_expression.split('|', 1)
            value = get_nested_value(context, var_path.strip(), '')
            
            # Process filters
            filter_chain = filters.strip()
            if 'date:' in filter_chain:
                if isinstance(value, str) and ('T' in value or '-' in value):
                    try:
                        if 'T' in value:
                            dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
                        else:
                            dt = datetime.strptime(value[:19], '%Y-%m-%d %H:%M:%S')
                        
                        if 'M d, Y' in filter_chain:
                            return dt.strftime('%b %d, %Y')
                        elif 'H:i' in filter_chain:
                            return dt.strftime('%H:%M')
                        else:
                            return dt.strftime('%b %d, %Y at %H:%M')
                    except:
                        pass
            
            if 'truncatechars:' in filter_chain:
                if isinstance(value, str) and len(value) > 100:
                    return value[:97] + '...'
            
            if 'safe' in filter_chain:
                return str(value)
            
            if 'stringformat:"s"' in filter_chain:
                return str(value)
            
            if 'upper' in filter_chain:
                return str(value).upper()
            
            return str(value) if value else ''
        
        # Handle form error access like form.field.errors.0
        if var_expression.startswith('form.') and '.errors.0' in var_expression:
            field_name = var_expression.replace('form.', '').replace('.errors.0', '')
            errors = get_nested_value(context, f'form.{field_name}_errors', [])
            if errors and len(errors) > 0:
                return str(errors[0])
            return ''
        
        value = get_nested_value(context, var_expression, '')
        # If this looks like HTML (starts with <), return it as-is
        if isinstance(value, str) and value.startswith('<') and value.endswith('>'):
            return value
        return str(value) if value else ''
    
    template_content = re.sub(r'{{([^}]+?)}}', replace_var, template_content)
    
    # Handle {% url %} tags
    url_replacements = {
        'issue_list': '/',
        'issue_create': '/issues/new/',
        'issue_detail': '/issues/{id}/',
        'issue_edit': '/issues/{id}/edit/',
        'comment_create': '/issues/{id}/comments/',
        'tag_list': '/tags/',
        'tag_create': '/tags/new/',
        'tag_edit': '/tags/{id}/edit/',
        'settings': '/settings/',
        'login': '/login/',
        'logout': '/logout/',
        'register': '/register/'
    }
    
    def replace_url(match):
        url_name = match.group(1).strip('\'"')
        
        # Handle URLs with parameters
        if len(match.groups()) > 1 and match.group(2):
            # Has parameters like {% url 'issue_detail' issue.pk %}
            param = match.group(2).strip()
            param_value = get_nested_value(context, param, '1')
            url = url_replacements.get(url_name, f'/{url_name}/')
            return url.replace('{id}', str(param_value))
        
        return url_replacements.get(url_name, f'/{url_name}/')
    
    template_content = re.sub(r'{%\s*url\s+[\'"]([^\'"]+)[\'"](?:\s+([^%]+))?\s*%}', replace_url, template_content)
    
    # Handle {% csrf_token %}
    template_content = re.sub(r'{%\s*csrf_token\s*%}', '<input type="hidden" name="csrfmiddlewaretoken" value="dummy_csrf_token">', template_content)
    
    # Clean up any remaining template tags
    template_content = re.sub(r'{%[^%]*%}', '', template_content)
    
    return template_content


def render_template_file(template_path, json_path, output_path):
    """Render a template file with JSON data"""
    try:
        # Load template
        template_content = load_template(template_path)
        
        # Load JSON data directly - no mocking needed!
        with open(json_path, 'r') as f:
            context = json.load(f)
        
        # Ensure messages is always available
        if 'messages' not in context:
            context['messages'] = []
        
        # Render template
        html = render_template_content(template_content, context)
        
        # Write output
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w') as f:
            f.write(html)
        
        print(f"✓ Rendered {os.path.basename(template_path)} -> {os.path.basename(output_path)}")
        return True
        
    except Exception as e:
        print(f"✗ Error rendering {template_path}: {e}")
        import traceback
        traceback.print_exc()
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
        
        if not path_parts or not path_parts[-1].endswith('.html'):
            continue
        
        # Remove the 'templates' prefix if it exists
        if path_parts[0] == 'templates':
            path_parts = path_parts[1:]
        
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