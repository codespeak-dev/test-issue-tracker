#!/usr/bin/env python3
"""
Django Template Renderer for generating static HTML files from templates and JSON data.
Handles template inheritance, filters, URL generation, and form rendering.
"""

import json
import os
import re
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional


class MockCSRFToken:
    """Mock CSRF token for templates."""
    def __str__(self):
        return '<input type="hidden" name="csrfmiddlewaretoken" value="mock-csrf-token-12345" />'


class TemplateRenderer:
    """Renders Django templates to static HTML using JSON data."""
    
    def __init__(self, template_dir: str):
        self.template_dir = Path(template_dir)
        self.url_patterns = {
            'issue_list': '/',
            'issue_detail': '/issue/{pk}/',
            'issue_create': '/issue/new/',
            'issue_edit': '/issue/{pk}/edit/',
            'comment_create': '/issue/{issue_pk}/comment/',
            'login': '/login/',
            'logout': '/logout/',
            'register': '/register/',
            'settings': '/settings/',
            'tag_list': '/tags/',
            'tag_create': '/tags/new/',
            'tag_edit': '/tags/{pk}/edit/',
        }
        
    def render_template(self, template_path: str, context: Dict[str, Any]) -> str:
        """Render a Django template with the given context."""
        template_file = self.template_dir / template_path
        
        if not template_file.exists():
            raise FileNotFoundError(f"Template not found: {template_file}")
        
        content = template_file.read_text()
        
        # Add CSRF token to context
        context['csrf_token'] = MockCSRFToken()
        
        # Handle template inheritance
        if '{% extends' in content:
            content = self._handle_extends(content, context)
        
        # Process template tags and filters
        content = self._process_template(content, context)
        
        return content
    
    def _handle_extends(self, content: str, context: Dict[str, Any]) -> str:
        """Handle template inheritance."""
        # Extract extends directive
        extends_match = re.search(r'{%\s*extends\s+[\'"]([^\'"]+)[\'"]\s*%}', content)
        if not extends_match:
            return content
        
        parent_template = extends_match.group(1)
        parent_path = self.template_dir / parent_template
        
        if not parent_path.exists():
            return content
        
        parent_content = parent_path.read_text()
        
        # Extract blocks from child template
        blocks = {}
        block_pattern = r'{%\s*block\s+(\w+)\s*%}(.*?){%\s*endblock\s*(?:\w+)?\s*%}'
        for match in re.finditer(block_pattern, content, re.DOTALL):
            block_name = match.group(1)
            block_content = match.group(2).strip()
            blocks[block_name] = block_content
        
        # Replace blocks in parent template
        def replace_block(match):
            block_name = match.group(1)
            default_content = match.group(2) if match.group(2) else ''
            return blocks.get(block_name, default_content)
        
        parent_content = re.sub(
            r'{%\s*block\s+(\w+)\s*%}(.*?){%\s*endblock\s*(?:\w+)?\s*%}',
            replace_block,
            parent_content,
            flags=re.DOTALL
        )
        
        return parent_content
    
    def _process_template(self, content: str, context: Dict[str, Any]) -> str:
        """Process template tags, variables, and filters."""
        
        # Process CSRF token
        content = re.sub(r'{%\s*csrf_token\s*%}', str(context.get('csrf_token', '')), content)
        
        # Process URL tags
        content = self._process_url_tags(content, context)
        
        # Process for loops first - they need to set up contexts for variables and conditionals
        content = self._process_for_loops_simple(content, context)
        
        # Process any remaining conditional blocks outside loops
        content = self._process_conditionals(content, context)
        
        # Process any remaining variables outside loops
        content = self._process_variables(content, context)
        
        return content
    
    def _process_url_tags(self, content: str, context: Dict[str, Any]) -> str:
        """Process {% url %} tags."""
        def replace_url(match):
            url_name = match.group(1).strip('\'"')
            args = match.group(2) if match.group(2) else ''
            
            if url_name in self.url_patterns:
                url_pattern = self.url_patterns[url_name]
                
                # Replace placeholders with actual values
                if args:
                    # Extract arguments
                    arg_matches = re.findall(r'(\w+(?:\.\w+)*)', args)
                    for arg in arg_matches:
                        value = self._get_nested_value(context, arg)
                        if value is not None:
                            placeholder = f'{{{arg.split(".")[-1]}}}'
                            url_pattern = url_pattern.replace(placeholder, str(value))
                
                return url_pattern
            
            return f'/{url_name}/'
        
        return re.sub(r'{%\s*url\s+[\'"](\w+)[\'"]([^%]*?)%}', replace_url, content)
    
    def _process_conditionals(self, content: str, context: Dict[str, Any]) -> str:
        """Process {% if %} blocks."""
        # Handle nested conditionals by processing from innermost to outermost
        while True:
            # Find innermost if block (one that doesn't contain other if blocks)
            pattern = r'{%\s*if\s+([^%]+?)%}((?:(?!{%\s*if\s)(?!{%\s*endif\s).)*?){%\s*endif\s*%}'
            match = re.search(pattern, content, re.DOTALL)
            
            if not match:
                break
                
            condition = match.group(1).strip()
            if_content = match.group(2)
            
            # Handle if-else blocks
            else_pattern = r'^(.*?){%\s*else\s*%}(.*)$'
            else_match = re.search(else_pattern, if_content, re.DOTALL)
            
            if else_match:
                true_content = else_match.group(1)
                false_content = else_match.group(2)
            else:
                true_content = if_content
                false_content = ''
            
            # Evaluate condition
            result = self._evaluate_condition(condition, context)
            replacement = true_content if result else false_content
            
            content = content[:match.start()] + replacement + content[match.end():]
        
        return content
    
    def _process_for_loops(self, content: str, context: Dict[str, Any]) -> str:
        """Process {% for %} loops."""
        processed_content = content
        
        while True:
            # Find innermost for loop that hasn't been processed yet
            pattern = r'{%\s*for\s+(\w+)\s+in\s+([^%]+?)%}(.*?){%\s*endfor\s*%}'
            match = re.search(pattern, processed_content, re.DOTALL)
            
            if not match:
                break
            
            loop_var = match.group(1)
            iterable_expr = match.group(2).strip()
            loop_content = match.group(3)
            
            # Handle {% empty %} clause
            empty_pattern = r'^(.*?){%\s*empty\s*%}(.*)$'
            empty_match = re.search(empty_pattern, loop_content, re.DOTALL)
            
            if empty_match:
                main_content = empty_match.group(1)
                empty_content = empty_match.group(2)
            else:
                main_content = loop_content
                empty_content = ''
            
            # Get iterable value
            iterable = self._get_nested_value(context, iterable_expr)
            
            if not iterable or (hasattr(iterable, '__len__') and len(iterable) == 0):
                replacement = empty_content
            else:
                # Render loop content for each item
                rendered_items = []
                for item in iterable:
                    loop_context = context.copy()
                    loop_context[loop_var] = item
                    # Process template content within this specific loop context
                    rendered_item = main_content
                    
                    # Only process nested elements within this item's content
                    # Process nested for loops within this loop context
                    rendered_item = self._process_for_loops(rendered_item, loop_context)
                    # Process conditionals within this loop context  
                    rendered_item = self._process_conditionals(rendered_item, loop_context)
                    # Process variables within this loop context
                    rendered_item = self._process_variables(rendered_item, loop_context)
                    
                    rendered_items.append(rendered_item)
                replacement = ''.join(rendered_items)
            
            # Replace the matched loop with its rendered content
            processed_content = processed_content[:match.start()] + replacement + processed_content[match.end():]
        
        return processed_content
    
    def _process_for_loops_final(self, content: str, context: Dict[str, Any]) -> str:
        """Final processing of for loops after all other template processing is complete."""
        # Process loops from outermost to innermost to avoid nesting issues
        while True:
            # Find any remaining for loop
            pattern = r'{%\s*for\s+(\w+)\s+in\s+([^%]+?)%}(.*?){%\s*endfor\s*%}'
            match = re.search(pattern, content, re.DOTALL)
            
            if not match:
                break
            
            loop_var = match.group(1)
            iterable_expr = match.group(2).strip()
            loop_content = match.group(3)
            
            # Handle {% empty %} clause
            empty_pattern = r'^(.*?){%\s*empty\s*%}(.*)$'
            empty_match = re.search(empty_pattern, loop_content, re.DOTALL)
            
            if empty_match:
                main_content = empty_match.group(1)
                empty_content = empty_match.group(2)
            else:
                main_content = loop_content
                empty_content = ''
            
            # Get iterable value
            iterable = self._get_nested_value(context, iterable_expr)
            
            if not iterable or (hasattr(iterable, '__len__') and len(iterable) == 0):
                replacement = empty_content
            else:
                # Render loop content for each item
                rendered_items = []
                for item in iterable:
                    loop_context = context.copy()
                    loop_context[loop_var] = item
                    
                    # Process this item's content completely
                    rendered_item = main_content
                    
                    # Handle any conditionals within this context
                    rendered_item = self._process_conditionals(rendered_item, loop_context)
                    
                    # Handle variables within this context
                    rendered_item = self._process_variables(rendered_item, loop_context)
                    
                    # Recursively handle nested loops
                    rendered_item = self._process_for_loops_final(rendered_item, loop_context)
                    
                    rendered_items.append(rendered_item)
                    
                replacement = ''.join(rendered_items)
            
            # Replace this loop with its rendered content
            content = content[:match.start()] + replacement + content[match.end():]
        
        return content
    
    def _process_variables(self, content: str, context: Dict[str, Any]) -> str:
        """Process {{ variable }} expressions with filters."""
        def replace_variable(match):
            expr = match.group(1).strip()
            
            # Handle filters
            if '|' in expr:
                parts = expr.split('|')
                var_name = parts[0].strip()
                filters = [f.strip() for f in parts[1:]]
            else:
                var_name = expr
                filters = []
            
            # Get variable value
            value = self._get_nested_value(context, var_name)
            
            # Apply filters
            for filter_expr in filters:
                value = self._apply_filter(value, filter_expr)
            
            return str(value) if value is not None else ''
        
        return re.sub(r'{{\s*([^}]+)\s*}}', replace_variable, content)
    
    def _get_nested_value(self, context: Dict[str, Any], path: str) -> Any:
        """Get nested value from context using dot notation."""
        if not path:
            return None
        
        # Handle special cases
        if path == 'csrf_token':
            return context.get('csrf_token', '')
        
        parts = path.split('.')
        value = context
        
        for part in parts:
            if isinstance(value, dict):
                value = value.get(part)
            elif hasattr(value, part):
                attr = getattr(value, part)
                # Handle method calls
                if callable(attr):
                    if part == 'all':  # Special case for .all() method
                        value = attr if isinstance(attr, list) else []
                    elif part == 'count':  # Special case for .count property
                        value = attr if isinstance(attr, int) else 0
                    elif part == 'exists':  # Special case for .exists() method
                        value = bool(attr) if isinstance(attr, bool) else (len(attr) > 0 if hasattr(attr, '__len__') else bool(attr))
                    else:
                        try:
                            value = attr()
                        except:
                            value = attr
                else:
                    value = attr
            else:
                # Handle Django form field properties
                if len(parts) >= 2 and parts[0] == 'form':
                    field_name = parts[1]
                    if len(parts) == 3 and parts[2] == 'id_for_label':
                        return f'id_{field_name}'
                    elif len(parts) == 3 and parts[2] == 'errors':
                        errors_key = f'{field_name}_errors'
                        return context.get('form', {}).get(errors_key, [])
                    elif len(parts) == 4 and parts[2] == 'errors' and parts[3] == '0':
                        errors_key = f'{field_name}_errors'
                        errors = context.get('form', {}).get(errors_key, [])
                        return errors[0] if errors else ''
                return None
        
        return value
    
    def _evaluate_condition(self, condition: str, context: Dict[str, Any]) -> bool:
        """Evaluate a template condition."""
        condition = condition.strip()
        
        # Handle negation
        if condition.startswith('not '):
            return not self._evaluate_condition(condition[4:], context)
        
        # Handle comparisons
        comparison_ops = ['==', '!=', '<=', '>=', '<', '>', ' in ']
        for op in comparison_ops:
            if op in condition:
                left, right = condition.split(op, 1)
                left_expr = left.strip()
                
                # Handle filters on the left side
                if '|' in left_expr:
                    parts = left_expr.split('|')
                    var_name = parts[0].strip()
                    filters = [f.strip() for f in parts[1:]]
                    left_val = self._get_nested_value(context, var_name)
                    for filter_expr in filters:
                        left_val = self._apply_filter(left_val, filter_expr)
                else:
                    left_val = self._get_nested_value(context, left_expr)
                
                right_val = self._parse_value(right.strip(), context)
                
                if op == '==':
                    return str(left_val) == str(right_val)
                elif op == '!=':
                    return str(left_val) != str(right_val)
                elif op == ' in ':
                    if isinstance(right_val, (list, tuple)):
                        return str(left_val) in [str(item) for item in right_val]
                    else:
                        return str(left_val) in str(right_val)
                elif op == '<':
                    return float(left_val or 0) < float(right_val or 0)
                elif op == '>':
                    return float(left_val or 0) > float(right_val or 0)
                elif op == '<=':
                    return float(left_val or 0) <= float(right_val or 0)
                elif op == '>=':
                    return float(left_val or 0) >= float(right_val or 0)
        
        # Handle logical operators
        if ' and ' in condition:
            parts = condition.split(' and ')
            return all(self._evaluate_condition(part.strip(), context) for part in parts)
        
        if ' or ' in condition:
            parts = condition.split(' or ')
            return any(self._evaluate_condition(part.strip(), context) for part in parts)
        
        # Simple variable evaluation
        value = self._get_nested_value(context, condition)
        
        # Handle boolean conversion
        if isinstance(value, bool):
            return value
        elif isinstance(value, (int, float)):
            return value != 0
        elif isinstance(value, str):
            return len(value) > 0
        elif hasattr(value, '__len__'):
            return len(value) > 0
        
        return value is not None
    
    def _parse_value(self, value_str: str, context: Dict[str, Any]) -> Any:
        """Parse a value string, handling literals and variables."""
        value_str = value_str.strip()
        
        # String literals
        if (value_str.startswith('"') and value_str.endswith('"')) or \
           (value_str.startswith("'") and value_str.endswith("'")):
            return value_str[1:-1]
        
        # Number literals
        try:
            if '.' in value_str:
                return float(value_str)
            else:
                return int(value_str)
        except ValueError:
            pass
        
        # Boolean literals
        if value_str.lower() == 'true':
            return True
        elif value_str.lower() == 'false':
            return False
        elif value_str.lower() == 'none':
            return None
        
        # Variable reference
        return self._get_nested_value(context, value_str)
    
    def _apply_filter(self, value: Any, filter_expr: str) -> Any:
        """Apply a template filter to a value."""
        if ':' in filter_expr:
            filter_name, args = filter_expr.split(':', 1)
        else:
            filter_name = filter_expr
            args = None
        
        if filter_name == 'safe':
            return value  # Already HTML, don't escape
        elif filter_name == 'date':
            if isinstance(value, str):
                try:
                    dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
                    if args == '"M d, Y"':
                        return dt.strftime('%b %d, %Y')
                    elif args == '"M d, Y \\a\\t H:i"':
                        return dt.strftime('%b %d, %Y at %H:%M')
                    else:
                        return dt.strftime('%Y-%m-%d')
                except:
                    return value
        elif filter_name == 'length':
            return len(value) if hasattr(value, '__len__') else 0
        elif filter_name == 'truncatechars':
            if args and isinstance(value, str):
                try:
                    length = int(args)
                    return value[:length] + '...' if len(value) > length else value
                except:
                    pass
        elif filter_name == 'stringformat':
            if args == '"s"':
                return str(value)
            return str(value)
        elif filter_name == 'default':
            return args if value is None or value == '' else value
        elif filter_name == 'upper':
            return str(value).upper()
        elif filter_name == 'lower':
            return str(value).lower()
        
        return value

    def _process_for_loops_simple(self, content: str, context: Dict[str, Any]) -> str:
        """Simple for loop processing that handles nesting correctly."""
        while True:
            # Find the FIRST for loop (not necessarily innermost)
            pattern = r'{%\s*for\s+(\w+)\s+in\s+([^%]+?)%}(.*?){%\s*endfor\s*%}'
            match = re.search(pattern, content, re.DOTALL)
            
            if not match:
                break
            
            loop_var = match.group(1)
            iterable_expr = match.group(2).strip()
            loop_content = match.group(3)
            
            # Handle {% empty %} clause
            empty_pattern = r'^(.*?){%\s*empty\s*%}(.*)$'
            empty_match = re.search(empty_pattern, loop_content, re.DOTALL)
            
            if empty_match:
                main_content = empty_match.group(1)
                empty_content = empty_match.group(2)
            else:
                main_content = loop_content
                empty_content = ''
            
            # Get iterable value
            iterable = self._get_nested_value(context, iterable_expr)
            
            if not iterable or (hasattr(iterable, '__len__') and len(iterable) == 0):
                replacement = empty_content
            else:
                # Render loop content for each item
                rendered_items = []
                for item in iterable:
                    loop_context = context.copy()
                    loop_context[loop_var] = item
                    
                    # Process this item's content step by step
                    rendered_item = main_content
                    
                    # First handle variables (so they can be used in conditions)
                    rendered_item = self._process_variables(rendered_item, loop_context)
                    
                    # Then handle conditionals
                    rendered_item = self._process_conditionals(rendered_item, loop_context)
                    
                    # Then handle any nested loops recursively
                    rendered_item = self._process_for_loops_simple(rendered_item, loop_context)
                    
                    rendered_items.append(rendered_item)
                    
                replacement = ''.join(rendered_items)
            
            # Replace this loop with its rendered content
            content = content[:match.start()] + replacement + content[match.end():]
        
        return content


def main():
    """Render all template states to HTML files."""
    if len(sys.argv) != 2:
        print("Usage: python template_renderer.py <output_dir>")
        sys.exit(1)
    
    output_dir = Path(sys.argv[1])
    template_dir = Path(__file__).parent.parent / "templates"
    
    renderer = TemplateRenderer(str(template_dir))
    
    # Load state descriptions
    state_descriptions_file = output_dir / "state_descriptions.json"
    with open(state_descriptions_file) as f:
        state_descriptions = json.load(f)
    
    # Render each state
    for template_path, states in state_descriptions.items():
        template_name = template_path.replace("templates/", "")
        
        for state_name, state_info in states.items():
            # Load state inputs
            input_file = output_dir / template_path / f"{state_name}.json"
            
            if not input_file.exists():
                print(f"Warning: Input file not found: {input_file}")
                continue
            
            try:
                with open(input_file) as f:
                    context = json.load(f)
                
                # Render template
                html_content = renderer.render_template(template_name, context)
                
                # Save HTML file
                output_file = output_dir / template_path / f"{state_name}.html"
                output_file.parent.mkdir(parents=True, exist_ok=True)
                
                with open(output_file, 'w') as f:
                    f.write(html_content)
                
                print(f"Generated: {output_file}")
                
            except Exception as e:
                print(f"Error rendering {template_path}/{state_name}: {e}")
                import traceback
                traceback.print_exc()


if __name__ == "__main__":
    main()