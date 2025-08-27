<var name="output_dir" value="ui_examples"/>

This Django app has 
- models in @issues/models.py, 
- views in @issues/views.py, 
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
</todo>

<todo index="3" inputs="state_descriptions, state_inputs">
Instantiate the templates from state_descriptions with the inputs from state_inputs.
For each template_path, for each state_name, generate a HTML file `{output_dir}/{template_path}/{state_name}.html` with the rendered template. Use inputs from `{output_dir}/{template_path}/{state_name}.json` and the template in {template_path}.

If template instantiation fails, fix the inputs and try again.
</todo>

<ignore type="comment">
Generate one JSON file with example data that corresponds to the DB structure from @issues/models.py. This data should be structured in such a way that templates can access it in the same way they access the models. 
</ignore>