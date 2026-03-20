

def smart_getattr(obj: Any, attr: str) -> Any:
    """Get an attribute from an object, trying both snake_case and camelCase."""
    if hasattr(obj, attr):
        return getattr(obj, attr)
    
    # Try converting snake_case to camelCase
    camel_attr = ''.join(word.capitalize() if i > 0 else word for i, word in enumerate(attr.split('_')))
    if hasattr(obj, camel_attr):
        return getattr(obj, camel_attr)
    
    raise AttributeError(f"{obj} has no attribute '{attr}' or '{camel_attr}'")