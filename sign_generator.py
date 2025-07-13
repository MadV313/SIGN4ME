import os
import json

OBJECT_CLASS_MAP = {
    "ImprovisedContainer": "Land_Container_1Mo",
    "SmallProtectiveCase": "SmallProtectorCase",
    "DryBag_Black": "DryBag_Black",
    "WoodenCrate": "WoodenCrate",
    "BoxWooden": "StaticObj_Misc_BoxWooden",
    "Armband_Black": "Armband_Black",
    "JerryCan": "CanisterGasoline"
}

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

MAX_OBJECTS = 1200
DEFAULT_YPR = [-178.0899200439453, 0.0, 0.0]

def pad_matrix(matrix: list) -> list:
    max_len = max(len(row) for row in matrix)
    return [row.ljust(max_len) for row in matrix]

def letter_to_object_list(matrix: list, object_type: str, origin: dict, offset: dict, scale: float = 1.0, spacing: float = None, ypr_mode: str = "upright") -> list:
    if object_type not in OBJECT_CLASS_MAP:
        raise ValueError(f"❌ Unrecognized object type: '{object_type}'.")

    resolved_type = OBJECT_CLASS_MAP[object_type]
    spacing = spacing if spacing is not None else scale * OBJECT_SIZE_ADJUSTMENTS.get(object_type, 1.0)

    matrix = pad_matrix(matrix)  # ✅ Make all rows the same length

    rows = len(matrix)
    origin_x = origin.get("x", 0.0)
    origin_y = origin.get("y", 0.0)
    origin_z = origin.get("z", 0.0)

    base_y = origin_y + offset.get("y", 0.0)

    objects = []

    for row in range(rows):
        current_row = matrix[row]
        row_len = len(current_row)

        offset_x = round(origin_x - ((row_len / 2) * spacing) + offset.get("x", 0.0), 6)
        pos_z = round(origin_z - ((rows / 2) * spacing) + (row * spacing) + offset.get("z", 0.0), 6)

        for col in range(row_len):
            if current_row[col] != "#":
                continue

            pos_x = round(offset_x + (col * spacing), 6)
            obj_pos = [pos_x, pos_z, round(base_y, 6)]  # XZY order

            ypr = DEFAULT_YPR if ypr_mode == "upright" else [0.0, 0.0, 0.0]

            obj = {
                "name": resolved_type,
                "pos": obj_pos,
                "ypr": ypr,
                "scale": scale,
                "enableCEPersistency": 0,
                "customString": ""
            }

            objects.append(obj)

    if len(objects) > MAX_OBJECTS:
        print(f"⚠️ Object cap exceeded: {len(objects)} > {MAX_OBJECTS}")
        raise ValueError("Exceeded object limit.")

    print(f"🧱 Final object count: {len(objects)} from {rows} rows × uniform cols")
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
        CONFIG.get("defaultSpacing", 1.0),
        ypr_mode=CONFIG.get("yprMode", "upright")
    )
    save_object_json(obj_list, CONFIG["object_output_path"])
    print(f"✅ Generated {len(obj_list)} sign objects.")
