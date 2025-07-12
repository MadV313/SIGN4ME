# logic/sign_generator.py — Converts letter matrix into DayZ object list

import os
import json

# ✅ In-game object class mapping
OBJECT_CLASS_MAP = {
    "ImprovisedContainer": "Land_Container_1Mo",
    "SmallProtectiveCase": "SmallProtectorCase",
    "DryBag_Black": "DryBag_Black",
    "WoodenCrate": "WoodenCrate",
    "BoxWooden": "StaticObj_Misc_BoxWooden",
    "Armband_Black": "Armband_Black",
    "JerryCan": "CanisterGasoline"
}

# ✅ Size tweaks per object (for spacing calculations)
OBJECT_SIZE_ADJUSTMENTS = {
    "SmallProtectiveCase": 1.0,
    "SmallProtectorCase": 1.0,
    "DryBag_Black": 1.25,
    "ImprovisedContainer": 1.0,
    "WoodenCrate": 1.1,
    "Armband_Black": 0.5,
    "JerryCan": 1.0,
    "BoxWooden": 1.0
}

MAX_OBJECTS = 950  # ⛔ Optional cap to avoid CE lag/crash

def letter_to_object_list(matrix: list, object_type: str, origin: dict, offset: dict, scale: float = 1.0, spacing: float = None) -> list:
    # Ensure valid object type and resolve to real classname
    if object_type not in OBJECT_CLASS_MAP:
        raise ValueError(f"❌ Unrecognized object type: '{object_type}'. Must be one of: {list(OBJECT_CLASS_MAP.keys())}")

    resolved_type = OBJECT_CLASS_MAP[object_type]
    spacing = spacing if spacing is not None else scale * OBJECT_SIZE_ADJUSTMENTS.get(object_type, 1.0)

    rows = len(matrix)
    cols = len(matrix[0])

    # Centered placement math
    offset_x = round(origin["x"] - ((cols // 2) * spacing) + offset.get("x", 0), 4)
    offset_z = round(origin["z"] - ((rows // 2) * spacing) + offset.get("z", 0), 4)
    top_y = origin["y"] + offset.get("y", 0.0)

    objects = []

    for row in range(rows):
        for col in range(cols):
            if matrix[row][col] != "#":
                continue

            base_x = offset_x + (col * spacing)
            base_z = offset_z + (row * spacing)

            if len(objects) >= MAX_OBJECTS:
                return objects

            obj = {
                "name": resolved_type,
                "pos": [base_x, top_y, base_z],
                "ypr": [0.0, 0.0, 90.0],
                "scale": scale,
                "enableCEPersistency": 0,
                "customString": ""
            }
            objects.append(obj)

    return objects

def save_object_json(object_list: list, output_path: str):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as f:
        json.dump({"Objects": object_list}, f, indent=2)

# ✅ Manual test
if __name__ == "__main__":
    from config import CONFIG
    from text_matrix import generate_letter_matrix

    test_text = "SIGN4ME"
    matrix = generate_letter_matrix(test_text)
    obj_list = letter_to_object_list(
        matrix,
        CONFIG["default_object"],
        CONFIG["origin_position"],
        CONFIG.get("originOffset", {"x": 0.0, "y": 0.0, "z": 0.0}),
        CONFIG.get("defaultScale", 0.5),
        CONFIG.get("defaultSpacing", 1.0)
    )
    save_object_json(obj_list, CONFIG["object_output_path"])
    print(f"✅ Generated {len(obj_list)} sign objects.")
