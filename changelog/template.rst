.. _gv-reference-changelog-{{ versiondata.date }}:

{% if render_title %}
v{{ versiondata.version }} ({{ versiondata.date }})
{{ top_underline * ((versiondata.version + versiondata.date)|length + 4)}}
{% endif %}
{% for section, _ in sections.items() %}
{% set underline = underlines[0] %}

{% if sections[section] %}
{% for category, val in definitions.items() if category in sections[section]%}
{{ definitions[category]['name'] }}
{{ underline * (definitions[category]['name']|length + 1) }}

{% for text, values in sections[section][category]|dictsort(by='value') %}
{% set comma = joiner(', ') %}
- {% for value in values|sort %}{{ comma() }}:fa:`code-pull-request` :pull:`{{ value[1:] }}`{% endfor %}: {{ text|replace(":issue:", ":far:`circle-dot` :issue:") }}

{% endfor %}

{% if sections[section][category]|length == 0 %}
No significant changes.

{% else %}
{% endif %}

{% endfor %}
{% else %}
No significant changes.


{% endif %}
{% endfor %}
