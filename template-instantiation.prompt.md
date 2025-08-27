<var name="output_dir" value="ui_examples_new"/>

This Django app has 
- models in @issues/models.py, 
- views in @issues/views.py, 
- forms in @issues/forms.py,
- and templates in @templates/. 

Your overall task is to help me render every state of this app's UI as a self-contained HTML file. 
These HTML files will be examples I can show to the user to get their feedback.

To do that, I need you to:
<todo index="1">
Read the templates and identify key UI states and the inputs that determine which state is displayed. Remember them in the following form:
<output_spec type="json" name="state_descriptions" path="{output_dir}/state_descriptions.json">
{
  "template_path": {
    "state_name": {
      "description": "description of the state",
      "relevant_inputs": [
        "input_name": "what value(s) in this input are required to display this state",
        ...
      ]
    },
    ...
  },
  ...
}
</output_spec>
Make sure you do this for every template and for every branch in its logic. E.g. if there is an `if` in the template, make sure to include both branches as separate states. If there is a `for` loop, make sure to include at least the cases for 0 and multiple items (5+). 

IMPORTANT: Always populate non-empty lists with at least 5 items, unless absolutely necessary to instantiate the state.
</todo>

<todo index="2" input="state_descriptions">
foreach template_path in state_descriptions
    foreach state_name in template_path
        generate a JSON file `{output_dir}/{template_path}/{state_name}.json` with the inputs to the correponding template that determine the state. 
        The inputs must have the following format:
        <output_spec type="json" name="state_inputs" path="{output_dir}/{template_path}/{state_name}.json">
        {
          "input_variable": <json value>,
          ...
        }
        </output_spec>
        Take the names of variables from the template. Also, look at @issues/views.py to see how these inputs are formed.
        This data must be for illustrative purposes only. Just an example. You can come up with plausible values for all fields.
        
        IMPORTANT: For Django forms, provide rendered HTML form elements, not form metadata. Templates expect `{{ form.field }}` to render as actual HTML input/textarea/select elements, not as JSON objects with field properties. For example:
        - `"summary": "<input type=\"text\" name=\"summary\" class=\"form-classes\" placeholder=\"Brief summary\" required id=\"id_summary\">"` 
        - NOT `"summary": {"id_for_label": "id_summary", "errors": []}`
        
        For forms with errors, include both the HTML elements (with error styling like red borders) AND separate error arrays:
        - `"field_name": "<input class=\"border-red-300\" ...>"`
        - `"field_name_errors": ["This field is required."]`
        
        Also ensure all user objects include a "name" field, not just authentication status.
        Look at forms in @issues/forms.py to get the necessary fields and layout parameters (styles, etc).
</todo>

<todo index="3" inputs="state_descriptions, state_inputs">
Instantiate the templates from state_descriptions with the inputs from state_inputs.
For each template_path, for each state_name, generate a HTML file `{output_dir}/{template_path}/{state_name}.html` with the rendered template. Use inputs from `{output_dir}/{template_path}/{state_name}.json` and the template in {template_path}.

IMPORTANT: Create a template renderer that uses the Django template engine to render the templates. Make sure it handles:
- `{% extends %}` and `{% block %}` for template inheritance
- `{% if %}...{% else %}...{% endif %}` conditionals with proper evaluation
- `{% for %}...{% empty %}...{% endfor %}` loops with context handling
- `{{ variable|filter }}` with common filters like `|length`, `|date`, `|safe`, `|truncatechars`
- `{% url 'name' param %}` URL generation
- `{% csrf_token %}` CSRF token inclusion

Use the JSON data directly without creating mock Python objects - modern template engines can work with plain JSON/dict structures.

For form error handling, support both:
- `{% if form.field.errors %}` checking for errors
- `{{ form.field.errors.0 }}` displaying first error message

Ensure the renderer handles nested data access like `issue.author.name`, `comments|length`, and `issue.tags.all`.

If template instantiation fails, fix the inputs and try again.
</todo>

<ignore type="comment">
Generate one JSON file with example data that corresponds to the DB structure from @issues/models.py. This data should be structured in such a way that templates can access it in the same way they access the models. 
</ignore>

## Validation and Testing

After generating all HTML files, validate the output by:

1. **Check for broken layouts**: Look for incomplete HTML tags, missing form elements, or raw JSON/template syntax in the output
2. **Verify form rendering**: Ensure forms show actual `<input>`, `<textarea>`, `<select>` elements, not metadata objects
3. **Test all states**: Make sure each UI state demonstrates the intended functionality (empty states, error states, populated states)
4. **Inspect user interactions**: Verify buttons, links, and form actions are properly rendered
5. **Review data consistency**: Check that related data (like issue authors, assignees, tags) displays correctly across templates

Common issues to watch for:
- `{'id_for_label': 'field', 'errors': []}` instead of actual form HTML
- Missing user names (showing "Hello, !" instead of "Hello, John!")
- Showing object references instead of numbers
- Empty or malformed conditional blocks
- Incomplete loops (missing `{% empty %}` handling)


<ignore type="comment">
Notes
- designate representative states (lots of features on one screen)
  - generate them first
- reuse the rendering code
- generate data for non-representative states from representative ones
  - do this all in parallel
- generate one big DB instance to play off of and then derive all the states' data from it
- display a fancy map of previews: 
  - a line per template/major state with previews of substates showing up as soon as they are generated
  - reproduce the structure of the template dir?
    - or maybe just the logic of the app?
</ignore>
