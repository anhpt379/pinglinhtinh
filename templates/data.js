function dataset_{{ url | md5sum }}() {
  return "{{ keys | join(',') }}\n" +
{% for record in records %}"{{ record | join(',') }}\n" + {% endfor %} 
"";
}

