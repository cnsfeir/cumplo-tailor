def update_dictionary(original: dict, new: dict) -> dict:
    """Merge recursively the new dictionary into the original dictionary overwriting existing values."""
    for key, value in new.items():
        if key in original and isinstance(original[key], dict) and isinstance(value, dict):
            update_dictionary(original[key], value)
            continue

        original[key] = value
    return original
