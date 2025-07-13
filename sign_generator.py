import os
import json
from decimal import Decimal
from json import JSONEncoder

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

# ✅ Use Decimal to lock-in YPR format
DEFAULT_YPR = [
    Decimal("-178.0899200439453"),
    Decimal("0.000000000016678911585188417"),
    Decimal("0.000002056595349131385")
]

class FixedFloatEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super().default(obj)

def letter_to_object_list(matrix: list, object_type: str, origin: dict, offset: dict, scale: float = 1.0, spacing: float = None, ypr_mode: str = "upright") -> list:
    if object_type not in OBJECT_CLASS_MAP:
        raise ValueError(f"❌ Unrecognized object type: '{object_type}'.")

    resolved_type = OBJECT_CLASS_MAP[object_type]
    spacing = spacing if spacing is not None else scale * OBJECT_SIZE_ADJUSTMENTS.get(object_type, 1.0)

    rows = len(matrix)
    cols = len(matrix[0])

    origin_x = origin.get("x", 0.0)
    origin_y = origin.get("y", 0.0)
    origin_z = origin.get("z", 0.0)

    offset_x = round(origin_x - ((cols // 2) * spacing) + offset.get("x", 0.0), 6)
    offset_z = round(origin_z - ((rows // 2) * spacing) + offset.get("z", 0.0), 6)
    base_y = origin_y + offset.get("y", 0.0)

    objects = []

    for row in range(rows):
        for col in range(cols):
            if matrix[row][col] != "#":
                continue

            pos_x = round(offset_x + (col * spacing), 6)
            pos_z = round(offset_z + (row * spacing), 6)

            obj_pos = [pos_x, pos_z, round(base_y, 6)]  # ✅ XZY

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

            if len(objects) >= MAX_OBJECTS:
                return objects

    return objects

def save_object_json(object_list: list, output_path: str):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as f:
        json.dump({"Objects": object_list}, f, indent=2, cls=FixedFloatEncoder)

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
