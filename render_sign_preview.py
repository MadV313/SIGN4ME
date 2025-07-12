# logic/render_sign_preview.py — Generates PNG preview of the item-based sign grid

from PIL import Image, ImageDraw, ImageFont
import os

def render_sign_preview(matrix: list, output_path: str, scale: int = 64, border: int = 2, object_type: str = "WoodenCrate", spacing: float = 1.0):
    """
    Renders a PNG preview of the sign layout using item thumbnails.

    Parameters:
    - matrix: 2D list of rows (from generate_letter_matrix)
    - output_path: where to save the image
    - scale: pixel size per tile (default 64px)
    - border: spacing around image (in tiles)
    - object_type: name of the DayZ object (used for thumbnail)
    - spacing: used for visual text label only
    """
    rows = len(matrix)
    cols = len(matrix[0])

    img_width = (cols + border * 2) * scale
    img_height = (rows + border * 2) * scale

    img = Image.new("RGB", (img_width, img_height), "white")
    draw = ImageDraw.Draw(img)

    thumbnail_name = object_type + ".PNG"
    thumb_path = os.path.join("assets", "thumbnails", thumbnail_name)

    try:
        thumb = Image.open(thumb_path).convert("RGBA").resize((scale, scale))
    except Exception as e:
        print(f"[render_sign_preview] ⚠️ Thumbnail not found: {thumb_path} — using fallback. Error: {e}")
        thumb = Image.new("RGBA", (scale, scale), "black")

    for r in range(rows):
        for c in range(cols):
            x = (c + border) * scale
            y = (r + border) * scale
            if matrix[r][c] == "#":
                img.paste(thumb, (x, y), mask=thumb if thumb.mode == "RGBA" else None)

            draw.rectangle([x, y, x + scale, y + scale], outline="#cccccc", width=1)

    try:
        font = ImageFont.truetype("arial.ttf", 14)
    except:
        font = ImageFont.load_default()

    label_text = f"Object: {object_type} | Spacing: {spacing}"
    draw.text((10, img_height - 24), label_text, fill="black", font=font)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    img.save(output_path)
    print(f"✅ Saved sign preview to {output_path}")
