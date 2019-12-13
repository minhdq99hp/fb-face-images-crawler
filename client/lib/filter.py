def aria_label_filter(aria_label, name):
    if name in aria_label or 'person' in aria_label or 'people' in aria_label:
        return True
    return False