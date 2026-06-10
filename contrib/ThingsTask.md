---
kind: thingstask
tags:
- things
{% for tag in tags %}
{%- if tag != "next" and tag != "active" -%}
  - things/{{ tag }}
{%- endif %}
{% endfor -%}
uuid: {{uuid}}
created: {{created_date}}
completed: {{completed_date}}
modified: {{modified_date}}
project: "{{project}}"
---

> [!warning]- Do not edit!
> This note was created automatically, and may be overwritten at any time. Any edits will likely be lost!

# {{ title }}

- [Things]({{ thingslink }})
- Created: {{created}}
- Completed: {{completed}}
- Modified: {{modified}}

## Notes

{% if notes -%}
{{ notes }}
{%- endif %}


{% if checklist_items %}
## Checklist

```
{%- for item in checklist_items %}
- [{%- if item["stop_date"] -%}x{%- else %} {% endif -%}] {{ item["title"] }} {%- if item["stop_date"] %} ({{ item["stop_date"] }}){% endif -%}
{%- endfor %}
```
{%- endif %}


---

# Metadata

- Kind: [[ThingsTask]]
- Created: [[{{created_date}}]]
- Completed: [[{{completed_date}}]]
- Modified: [[{{modified_date}}]]


<!-- Jinja2 template for use by Things task logger -->
