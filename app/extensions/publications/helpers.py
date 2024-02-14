from datetime import date, datetime
import os
import shutil


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


def export_zip_to_filesystem(zip_binary: bytes, zip_filename: str, path: str):
    """
    Store zip result in temp folder for reference / debugging
    """
    project_root = os.getcwd()
    temp_dir = os.path.join(project_root, path)
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)
    else:
        # Delete existing files and folders in the directory
        for file_name in os.listdir(temp_dir):
            file_path = os.path.join(temp_dir, file_name)
            if os.path.isfile(file_path):
                os.remove(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
    os.chdir(temp_dir)
    with open(os.path.join(os.getcwd(), zip_filename), "wb") as f:
        f.write(zip_binary)
