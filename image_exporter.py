import os
import io
from PIL import Image, ImageDraw, ImageFont

def get_font(size, bold=False):
    """Attempt to load a clean system font (Segoe UI or Arial), fallback to default."""
    font_names = [
        "segoeuib.ttf" if bold else "segoeui.ttf", 
        "arialbd.ttf" if bold else "arial.ttf"
    ]
    for fn in font_names:
        try:
            return ImageFont.truetype(fn, size)
        except IOError:
            continue
    return ImageFont.load_default()

def export_results_to_image(filepath, app_specs, scores, game_name, logo_data, profiles_data):
    """Procedurally generates a full matrix table image comparing all three profiles."""
    
    # 1. Setup Layout Dimensions
    margin = 20
    col_labels_w = 300
    col_w = 280
    img_width = margin * 2 + col_labels_w + (col_w * 3)  # Total width: ~1200px
    
    # Extract profiles safely
    tier_keys = list(profiles_data.keys())
    if len(tier_keys) < 3:
        return  # Safeguard if data is missing
        
    p_perf = profiles_data[tier_keys[0]]
    p_bal = profiles_data[tier_keys[1]]
    p_max = profiles_data[tier_keys[2]]
    
    # Gather all unique settings across profiles (excluding Estimated FPS for rows)
    all_settings = []
    for k in p_bal.keys():
        if k != "Estimated FPS" and k not in all_settings:
            all_settings.append(k)
            
    row_height = 36
    row_spacing = 4
    
    hw_box_h = 110
    game_box_h = 80
    header_h = 55
    settings_h = len(all_settings) * (row_height + row_spacing)
    
    y_hw_box = 60
    y_game_box = y_hw_box + hw_box_h + 15
    y_table_header = y_game_box + game_box_h + 20
    y_settings = y_table_header + header_h + 10
    total_height = y_settings + settings_h + 40

    img = Image.new('RGB', (img_width, total_height), color="#121212")
    draw = ImageDraw.Draw(img)

    # Fonts
    font_title = get_font(26, bold=True)
    font_header = get_font(15, bold=True)
    font_text = get_font(14, bold=False)
    font_bold = get_font(14, bold=True)
    font_small = get_font(12, bold=False)

    # 2. Draw Title
    draw.text((margin, margin), "Game Optimizer Results - Optimization Matrix", font=font_title, fill="#ffffff")

    # 3. Hardware Block (Stacked vertically)
    draw.rounded_rectangle([(margin, y_hw_box), (img_width - margin, y_hw_box + hw_box_h)], radius=6, fill="#1c1c1e")
    draw.text((margin + 15, y_hw_box + 15), "SYSTEM HARDWARE", font=font_header, fill="#3498db")
    
    y_text = y_hw_box + 42
    draw.text((margin + 15, y_text), f"CPU: {app_specs.get('CPU', 'Unknown CPU')} ({scores['cpu']} pts)", font=font_text, fill="#e0e0e0")
    draw.text((margin + 15, y_text + 22), f"GPU: {app_specs.get('GPU', 'Unknown GPU')} ({scores['gpu']} pts)", font=font_text, fill="#e0e0e0")
    draw.text((margin + 15, y_text + 44), f"RAM: {app_specs.get('RAM', 'Unknown')} GB ({scores['ram']} pts)", font=font_text, fill="#e0e0e0")

    # 4. Game Block
    draw.rounded_rectangle([(margin, y_game_box), (img_width - margin, y_game_box + game_box_h)], radius=6, fill="#1c1c1e")
    
    logo_x = margin + 15
    text_x = logo_x
    if logo_data:
        try:
            logo_img = Image.open(io.BytesIO(logo_data)).convert("RGBA")
            logo_bg = Image.new("RGBA", logo_img.size, (28, 28, 30, 255))
            logo_bg.paste(logo_img, (0, 0), logo_img)
            logo_bg = logo_bg.resize((140, 65)) 
            img.paste(logo_bg, (logo_x, y_game_box + 7))
            text_x = logo_x + 160
        except Exception:
            pass
    
    draw.text((text_x, y_game_box + 25), game_name, font=font_title, fill="#ffffff")

    # 5. Table Headers
    draw.rounded_rectangle([(margin, y_table_header), (img_width - margin, y_table_header + header_h)], radius=6, fill="#2a2a2c")
    
    col_x = [margin + 15, margin + col_labels_w, margin + col_labels_w + col_w, margin + col_labels_w + col_w * 2]
    
    draw.text((col_x[0], y_table_header + 18), "Graphics Setting", font=font_header, fill="#ffffff")
    
    for i, profile_key in enumerate(tier_keys):
        p_name = profile_key.split('. ')[-1]
        fps_val = profiles_data[profile_key].get("Estimated FPS", "N/A")
        
        draw.text((col_x[i+1], y_table_header + 8), p_name.upper(), font=font_bold, fill="#f39c12")
        draw.text((col_x[i+1], y_table_header + 28), f"Est. FPS: {fps_val}", font=font_small, fill="#2ecc71")

    # 6. Table Rows
    current_y = y_settings
    
    def get_color(val_str):
        if any(x in val_str for x in ["Enabled", "DLSS", "Ultra", "High", "Performance"]): return "#2ecc71"
        if any(x in val_str for x in ["Disabled", "Off", "Low", "Lowest", "UNPLAYABLE", "Poor"]): return "#e74c3c"
        return "#e0e0e0"

    for idx, setting in enumerate(all_settings):
        bg_color = "#252526" if idx % 2 == 0 else "#1e1e1f"
        draw.rounded_rectangle([(margin, current_y), (img_width - margin, current_y + row_height)], radius=4, fill=bg_color)
        
        # Setting Label
        draw.text((col_x[0], current_y + 8), str(setting), font=font_bold, fill="#ffffff")
        
        # Values
        val1 = str(p_perf.get(setting, "-"))
        val2 = str(p_bal.get(setting, "-"))
        val3 = str(p_max.get(setting, "-"))
        
        draw.text((col_x[1], current_y + 8), val1, font=font_bold, fill=get_color(val1))
        draw.text((col_x[2], current_y + 8), val2, font=font_bold, fill=get_color(val2))
        draw.text((col_x[3], current_y + 8), val3, font=font_bold, fill=get_color(val3))
        
        current_y += (row_height + row_spacing)

    # 7. Footer
    draw.text((margin, total_height - 25), "Generated locally by Game Optimizer", font=font_small, fill="#555555")

    img.save(filepath)