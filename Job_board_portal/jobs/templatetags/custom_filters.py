from django import template

register = template.Library()

@register.filter
def split(value, delimiter=','):
    return value.split(delimiter)

@register.filter
def trim(value):
    return value.strip()



from django import template
import json
import ast

register = template.Library()

@register.filter
def display_skills(skill_data):
    """
    Handles all possible skill data formats:
    - List of dicts: [{'value': 'Python'}, {'value': 'Django'}]
    - JSON string: '[{"value": "Python"}]'
    - List of strings: ['Python', 'Django']
    - String: "Python, Django"
    """
    if not skill_data:
        return []
    
    # If it's already a list
    if isinstance(skill_data, list):
        skills = []
        for item in skill_data:
            if isinstance(item, dict) and 'value' in item:
                skills.append(str(item['value']))
            else:
                skills.append(str(item))
        return skills
    
    # If it's a string that might be JSON
    if isinstance(skill_data, str):
        try:
            # Try to parse as JSON
            parsed = json.loads(skill_data)
            if isinstance(parsed, list):
                return display_skills(parsed)  # Recursive call
        except json.JSONDecodeError:
            # If not JSON, try to split by commas
            return [s.strip() for s in skill_data.split(',') if s.strip()]
    
    return []


@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)


@register.simple_tag
def param_replace(request, **kwargs):
    params = request.GET.copy()
    for key, value in kwargs.items():
        params[key] = value
    return params.urlencode()