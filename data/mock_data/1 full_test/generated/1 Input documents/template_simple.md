# Company Info: {{ company | format_string('title') }}

* **ID:** {{ id }})
* **Revenue Q4:** {{revenue_q4}} ({{ revenue_q4 | format_number('spell_out', 'en') }} Euros)
* **Publicly Traded:** {{ is_public | format_bool('bool', 'Yes', 'No') }}