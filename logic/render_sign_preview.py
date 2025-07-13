# logic/render_sign_preview.py

from PIL import Image
import os

ASSETS_DIR = "assets/thumbnails"

def render_sign_preview(matrix, output_path, object_type="WoodenCrate", tile_size=64):
    icon_path = os.path.join(ASSETS_DIR, f"{object_type}.PNG")
    if not os.path.exists(icon_path):
        raise FileNotFoundError(f"Icon not found for object: {object_type}")

    icon_img = Image.open(icon_path).convert("RGBA")
    icon_img = icon_img.resize((tile_size, tile_size))

    # ✅ Flip vertically and horizontally to match in-game layout
    matrix = matrix[::-1]
    matrix = [row[::-1] for row in matrix]

    width = len(matrix[0]) * tile_size
    height = len(matrix) * tile_size
    canvas = Image.new("RGBA", (width, height), (0, 0, 0, 0))

    for y, row in enumerate(matrix):
        for x, cell in enumerate(row):
            if cell == "#":
                canvas.paste(icon_img, (x * tile_size, y * tile_size), icon_img)

    canvas.save(output_path)
