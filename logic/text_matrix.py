# logic/text_matrix.py

from .font_map import FONT_MAP

def generate_letter_matrix(text):
    text = text.upper()
    lines = [[] for _ in range(5)]

    for char in text:
        if char not in FONT_MAP:
            continue  # Skip unsupported characters
        char_map = FONT_MAP[char]
        for i in range(5):
            lines[i].append(char_map[i])
            lines[i].append(" ")  # 1-space gap between letters

    # Combine characters into final matrix rows
    final_matrix = ["".join(line).rstrip() for line in lines]
    return [list(row) for row in final_matrix]  # Return as 2D list (row-major)
