from datetime import date, datetime


def serialize_datetime(obj):
    """
    Recursively convert datetime and date objects to strings in a dictionary.
    """
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    elif isinstance(obj, dict):
        return {key: serialize_datetime(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [serialize_datetime(element) for element in obj]
    else:
        return obj
