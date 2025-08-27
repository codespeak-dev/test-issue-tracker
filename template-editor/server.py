#!/usr/bin/env python3
"""
FastAPI server for WYSIWYG Django template editing.
"""

import json
import os
import difflib
from pathlib import Path
from typing import Dict, Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from dotenv import load_dotenv
import google.generativeai as genai
from bs4 import BeautifulSoup

from template_renderer import DjangoTemplateRenderer

# Load environment variables
load_dotenv()

app = FastAPI(title="Template Editor")

# Configuration
TEMPLATE_DIR = Path("../templates")
DATA_DIR = Path("../docs/ui_examples_new/templates") 
EDITOR_JS_PATH = Path("./editor.js")

# Initialize Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-2.5-flash')

# Initialize Django renderer
renderer = DjangoTemplateRenderer(str(TEMPLATE_DIR))

# Serve static files
app.mount("/static", StaticFiles(directory="."), name="static")


class SaveRequest(BaseModel):
    html: str
    path: str


def parse_route_path(path: str) -> tuple[str, str]:
    """Parse route path like /issues/issue_detail.html/normal_issue.html"""
    # Remove leading slash
    path = path.lstrip('/')
    
    # Split into template path and data file
    parts = path.split('/')
    if len(parts) < 3:
        raise HTTPException(status_code=400, detail="Invalid route path format")
    
    # Reconstruct template path and data file
    template_path = '/'.join(parts[:-1])  # e.g., "issues/issue_detail.html"
    data_file = parts[-1]  # e.g., "normal_issue.html"
    
    return template_path, data_file


def load_context_data(template_path: str, data_file: str) -> Dict[str, Any]:
    """Load JSON context data for template rendering."""
    # Convert data_file.html to data_file.json
    json_file = data_file.replace('.html', '.json')
    
    data_path = DATA_DIR / template_path / json_file
    
    if not data_path.exists():
        raise HTTPException(status_code=404, detail=f"Data file not found: {data_path}")
    
    with open(data_path, 'r') as f:
        return json.load(f)


def inject_editor_script(html: str) -> str:
    """Inject editor.js script into HTML head using BeautifulSoup."""
    soup = BeautifulSoup(html, 'html.parser')
    
    # Create script tag
    script_tag = soup.new_tag('script', src='/static/editor.js')
    
    # Find head tag and append script
    head = soup.find('head')
    if head:
        head.append(script_tag)
    else:
        # If no head tag, create one and add to html
        head = soup.new_tag('head')
        head.append(script_tag)
        html_tag = soup.find('html')
        if html_tag:
            html_tag.insert(0, head)
        else:
            # Wrap entire content in html/head structure
            new_html = soup.new_tag('html')
            new_head = soup.new_tag('head') 
            new_head.append(script_tag)
            new_body = soup.new_tag('body')
            new_body.extend(soup.contents)
            new_html.append(new_head)
            new_html.append(new_body)
            soup.clear()
            soup.append(new_html)
    
    return str(soup)


async def generate_template_update(original_template: str, original_html: str, edited_html: str, context_data: Dict[str, Any]) -> tuple[str, str]:
    """Use Gemini to update the template based on HTML changes."""
    
    prompt = """You are a Django template expert. I need you to update a Django template based on changes made to its rendered HTML output.

ORIGINAL TEMPLATE:
```
{}
```

ORIGINAL RENDERED HTML:
```
{}
```

EDITED HTML (with user changes):
```
{}
```

TEMPLATE CONTEXT DATA:
```json
{}
```

Your task:
1. Compare the original rendered HTML with the edited HTML to identify what changed
2. Update the Django template to incorporate these changes
3. IMPORTANT: If you detect changes to content that comes from the context data (variables, loops over data, etc.) rather than static template content, respond with an error explaining which data-driven parts were modified
4. Only modify the template structure, static text, CSS classes, HTML attributes, etc. - never change how dynamic data is rendered

RULES:
- Preserve all Django template tags ({{% %}}) and variables ({{{{ }}}})  
- Only update static HTML structure, text, classes, styles
- If user edited content that comes from context data, return an error
- Return ONLY the updated template code, nothing else
- If there's an error, start your response with "ERROR:" followed by the explanation

Updated template:""".format(original_template, original_html, edited_html, json.dumps(context_data, indent=2))

    try:
        response = model.generate_content(prompt)
        result = response.text.strip()
        
        if result.startswith("ERROR:"):
            return None, result[6:].strip()
        
        return result, None
        
    except Exception as e:
        return None, f"LLM generation failed: {str(e)}"


def render_and_compare(template_content: str, template_path: str, context_data: Dict[str, Any], target_html: str) -> tuple[bool, str]:
    """Render template and compare with target HTML."""
    # Save template temporarily and render
    temp_template_path = TEMPLATE_DIR / template_path
    temp_template_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Backup original
    original_content = None
    if temp_template_path.exists():
        with open(temp_template_path, 'r') as f:
            original_content = f.read()
    
    try:
        # Write new template
        with open(temp_template_path, 'w') as f:
            f.write(template_content)
        
        # Render with context
        rendered = renderer.render_template(template_path, context_data)
        
        # Compare rendered HTML with target (ignoring whitespace differences)
        rendered_clean = ' '.join(rendered.split())
        target_clean = ' '.join(target_html.split())
        
        matches = rendered_clean == target_clean
        
        if not matches:
            # Generate diff for debugging
            diff = '\n'.join(difflib.unified_diff(
                target_clean.splitlines(),
                rendered_clean.splitlines(),
                fromfile='target',
                tofile='rendered',
                lineterm=''
            ))
            return False, f"Template renders differently than target:\n{diff}"
        
        return True, "Template renders correctly"
        
    finally:
        # Restore original if it existed
        if original_content is not None:
            with open(temp_template_path, 'w') as f:
                f.write(original_content)
        elif temp_template_path.exists():
            temp_template_path.unlink()


@app.get("/{path:path}")
async def serve_template(path: str):
    """Serve rendered Django template with editor script injected."""
    try:
        if not path:
            return HTMLResponse("<h1>Template Editor</h1><p>Navigate to a template route like /issues/issue_detail.html/normal_issue.html</p>")
        
        template_path, data_file = parse_route_path(path)
        
        # Load context data
        context_data = load_context_data(template_path, data_file)
        
        # Render template
        rendered_html = renderer.render_template(template_path, context_data)
        
        # Inject editor script
        final_html = inject_editor_script(rendered_html)
        
        return HTMLResponse(final_html)
        
    except Exception as e:
        return HTMLResponse(f"<h1>Error</h1><p>{str(e)}</p>", status_code=500)


@app.post("/save")
async def save_template(request: SaveRequest):
    """Save edited template using LLM integration."""
    try:
        template_path, data_file = parse_route_path(request.path)
        
        # Load original template
        original_template_path = TEMPLATE_DIR / template_path
        if not original_template_path.exists():
            raise HTTPException(status_code=404, detail=f"Template not found: {template_path}")
        
        with open(original_template_path, 'r') as f:
            original_template = f.read()
        
        # Load context data
        context_data = load_context_data(template_path, data_file)
        
        # Render original template
        original_html = renderer.render_template(template_path, context_data)
        
        # Strip the editor script from the edited HTML for comparison
        soup = BeautifulSoup(request.html, 'html.parser')
        script_tags = soup.find_all('script', src='/static/editor.js')
        for script in script_tags:
            script.decompose()
        edited_html = str(soup)
        
        # Attempt template update with retries
        max_attempts = 3
        for attempt in range(max_attempts):
            print(f"Attempt {attempt + 1} to generate template update...")
            
            updated_template, error = await generate_template_update(
                original_template, original_html, edited_html, context_data
            )
            
            if error:
                return JSONResponse({"success": False, "error": error})
            
            # Validate the updated template renders correctly
            renders_correctly, validation_message = render_and_compare(
                updated_template, template_path, context_data, edited_html
            )
            
            if renders_correctly:
                # Save the updated template
                with open(original_template_path, 'w') as f:
                    f.write(updated_template)
                
                print(f"Successfully updated template after {attempt + 1} attempts")
                return JSONResponse({"success": True, "message": "Template saved successfully"})
            else:
                print(f"Attempt {attempt + 1} failed validation: {validation_message}")
                # For next iteration, update the original template to be the failed attempt
                # This gives the LLM context about what went wrong
                original_template = f"Previous attempt (failed validation):\n{updated_template}\n\nValidation error:\n{validation_message}\n\nOriginal template:\n{original_template}"
        
        return JSONResponse({
            "success": False, 
            "error": f"Failed to generate correct template after {max_attempts} attempts"
        })
        
    except Exception as e:
        print(f"Save error: {str(e)}")
        return JSONResponse({"success": False, "error": str(e)})


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)