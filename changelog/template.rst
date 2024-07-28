{% for section in sections %}
{% set underline = underlines[0] %}
{% if section %}
{{ section }}
{{ underline * section|length }}{% set underline = underlines[1] %}

{% endif %}
{% if sections[section] %}
{% for category in definitions if category in sections[section] %}

{{ definitions[category]['name'] }}
{{ underline * (definitions[category]['name']|length + 1) }}

{% if definitions[category]['showcontent'] %}
{% for text, values in sections[section][category]|dictsort(by='value') %}
{% if not values or values[0][0] == '+' %}
- {{ text }}
{% else %}
{% set comma = joiner(', ') %}
- {% for value in values|sort %}{{ comma() }}:fa:`code-pull-request` :pull:`{{ value[1:] }}`{% endfor %}: {{ text|replace(":issue:", ":far:`circle-dot` :issue:") }}
{% endif %}
{% endfor %}

{% else %}
- {{ sections[section][category]['']|join(', ') }}

{% endif %}
{% if sections[section][category]|length == 0 %}

No significant changes.

{% else %}
{% endif %}
{% endfor %}
{% else %}

No significant changes.

{% endif %}
{% endfor %}
