# Django Template Editor

A WYSIWYG web server for editing Django templates using an LLM-powered backend.

## Setup

1. Install dependencies:
   ```bash
   cd template-editor
   uv pip install -r requirements.txt
   ```

2. Make sure you have a Gemini API key in `.env`:
   ```
   GEMINI_API_KEY=your_api_key_here
   ```

## Running

Start the server:
```bash
python start.py
```

Then navigate to a template route like:
- http://localhost:8000/issues/issue_detail.html/normal_issue.html
- http://localhost:8000/issues/issue_list.html/populated_list_with_tags.html
- http://localhost:8000/registration/login.html/empty_form.html

## Usage

1. **Edit Mode**: Click the pencil icon (✏️) in the top-right to enter edit mode
2. **Select Elements**: Hover over elements to highlight them with a blue border
3. **Edit Content**: Click highlighted elements to make them editable using `contentEditable`
4. **Save Changes**: Click the save icon (💾) to save changes back to the template
5. **Exit**: The page will reload with your updated template

## How It Works

1. **Template Rendering**: Uses Django's template engine with mock data to render templates
2. **Script Injection**: Injects `editor.js` into the rendered HTML for WYSIWYG editing
3. **LLM Integration**: When saving, uses Gemini to integrate HTML changes back into the Django template
4. **Validation**: Ensures the updated template renders the same HTML as the edited version
5. **Retry Logic**: Attempts up to 3 times with feedback if template generation fails

## Directory Structure

- `templates/` - Django template files (editable)
- `docs/ui_examples_new/templates/` - JSON data files for rendering
- `editor.js` - Client-side WYSIWYG editor
- `server.py` - FastAPI web server
- `template_renderer.py` - Django template rendering logic