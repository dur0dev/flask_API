import yaml

def load_doc(name):
    with open('swagger/global.yaml', 'r') as f:
        docs = yaml.safe_load(f)
    
    if name not in docs:
        return ""
    
    spec = docs[name]
    
    # Build Flask-RESTX docstring format
    docstring = f"{spec.get('summary', '')}\n---\n"
    
    # Add each section
    for key, value in spec.items():
        if key != 'summary':
            docstring += f"{key}:\n"
            # Convert back to YAML format with proper indentation
            yaml_str = yaml.dump(value, default_flow_style=False, indent=2)
            indented = '\n'.join(['  ' + line for line in yaml_str.split('\n')])
            docstring += indented + '\n'
    
    return docstring.strip()

def swagger_doc(name):
    def decorator(func):
        func.__doc__ = load_doc(name)
        return func
    return decorator