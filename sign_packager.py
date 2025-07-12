# logic/sign_packager.py — Returns path to .json export for Sign4Me output

import os

def create_sign_zip(object_json_path: str, preview_image_path: str, zip_output_path: str, extra_text: str = "", export_mode: str = "json") -> str:
    """
    Skips zip creation and returns only the path to the object JSON file.
    Used for sending raw object layout directly into Discord without zipping.
    """
    os.makedirs(os.path.dirname(object_json_path), exist_ok=True)

    print(f"[sign_packager] 🔄 Export mode: '{export_mode}'. Returning JSON file only.")
    return object_json_path
