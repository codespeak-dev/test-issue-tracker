In the @template-editor folder, write a web server for WYSIWYG editing of Django templates.

Technology:
- use uv to manage the project
- don't use django as a server, use a simple python server if possible (or fastapi if necessary)
- use Gemini to run the LLM, through the `google.generativeai` package
  - use gemini-2.5-flash
  - the API key is in the @template-editor/.env file

Configuration:
- template directory, e.g.: @templates
- data directory, e.g.: @docs/ui_examples_new/templates

The server server takes routes like `issues/issue_detail.html/normal_issue.html` (referred to as route_path below) and does the following:
- takes the template `{template directory}/{route_path}` and renders it with the data from `{data directory}/{route_path}` (replacing the `.html` extension with `.json`) using the logic inspired by @docs/ui_examples_new/django_template_renderer.py
- uses bs4 to inject a reference to a script based on`{template directory}/editor.js` (copy as is or improve as necessary) into the rendered template's `<head>`
- displays the rendered page

When the editor.js's Save button is clickked (when exiting the editing mode), the following happens:
- the client is showing a "Saving..." message
- the new html is sent to the server
- server runs an LLM passing it the new html, the template that was initially rendered and the data it was rendered with and asks to integrate the changes made to the html into the template. If the LLM sees any changes made to the pieces that are part of the data and not the template, it should stop generation with an error message explainig which bits were changed in the data.
- if no error was returned,then the server checks that the new template renders exactly the same as the edited html with the original data; if not it runs the LLM again providing the failed attemp as context: the template and the diff between the target html and the rendering result.
  - if three attempts like this fail, the server should stop and return an error message.
- if the generation succeeds, the server saves the new template to `{template directory}/{route_path}` and renders the same page with it in the browser.
