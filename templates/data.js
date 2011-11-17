{% if offset %}
dataset_{{ url | md5sum }} = [{% for record in records %}
  [{{ record | join(',') }}],{% endfor %} 
]
{% else %}
[{% for record in records %}
	[{{ record | join(',') }}],{% endfor %} 
]
{% endif %}

