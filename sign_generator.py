# logic/sign_generator.py — Converts letter matrix into DayZ object list

import os
import json

# ✅ In-game object class mapping (value = in-game classname)
OBJECT_CLASS_MAP = {
    "ImprovisedContainer": "Land_Container_1Mo",
    "SmallProtectiveCase": "SmallProtectorCase",
    "DryBag_Black": "DryBag_Black",
    "WoodenCrate": "WoodenCrate",
    "BoxWooden": "StaticObj_Misc_BoxWooden",
    "Armband_Black": "Armband_Black",
    "JerryCan": "CanisterGasoline"
}

# ✅ Size tweaks per object (for spacing calculation)
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

# ✅ Max object cap — enforced inside loop
MAX_OBJECTS = 1200

# ✅ Select YPR array based on mode
def resolve_ypr(mode: str) -> list:
    if mode == "flat":
        return [0.0, 0.0, 0.0]  # Flat on ground, no roll
    return [-180.0, 0.0, 0.0]  # Upright: Face correct direction, fix backward+flip

def letter_to_object_list(matrix: list, object_type: str, origin: dict, offset: dict, scale: float = 1.0, spacing: float = None, ypr_mode: str = "upright") -> list:
    if object_type not in OBJECT_CLASS_MAP:
        raise ValueError(f"❌ Unrecognized object type: '{object_type}'. Must be one of: {list(OBJECT_CLASS_MAP.keys())}")

    # ✅ Flip matrix both vertically and horizontally to correct render direction
    matrix = [row[::-1] for row in matrix[::-1]]

    resolved_type = OBJECT_CLASS_MAP[object_type]
    spacing = spacing if spacing is not None else scale * OBJECT_SIZE_ADJUSTMENTS.get(object_type, 1.0)
    ypr = resolve_ypr(ypr_mode)

    rows = len(matrix)
    cols = len(matrix[0])

    # ✅ Proper origin offset (centered)
    origin_x = origin.get("x", 0.0)
    origin_y = origin.get("y", 0.0)
    origin_z = origin.get("z", 0.0)

    offset_x = round(origin_x - ((cols // 2) * spacing) + offset.get("x", 0.0), 4)
    offset_z = round(origin_z - ((rows // 2) * spacing) + offset.get("z", 0.0), 4)
    base_y = origin_y + offset.get("y", 0.0)

    objects = []

    for row in range(rows):
        for col in range(cols):
            if matrix[row][col] != "#":
                continue

            pos_x = offset_x + (col * spacing)
            pos_z = offset_z + (row * spacing)

            # ✅ Output [X, Y, Z] — correct order for DayZ
            obj_pos = [round(pos_x, 4), round(base_y, 4), round(pos_z, 4)]

            obj = {
                "name": resolved_type,
                "pos": obj_pos,
                "ypr": ypr,
                "scale": scale,
                "enableCEPersistency": 0,
                "customString": ""
            }

            objects.append(obj)

            if len(objects) >= MAX_OBJECTS:
                return objects

    return objects

def save_object_json(object_list: list, output_path: str):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as f:
        json.dump({"Objects": object_list}, f, indent=2)

# ✅ Manual test hook
if __name__ == "__main__":
    from config import CONFIG
    from text_matrix import generate_letter_matrix

    test_text = "SIGN4ME"
    matrix = generate_letter_matrix(test_text)
    matrix = [row[::-1] for row in matrix[::-1]]
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
