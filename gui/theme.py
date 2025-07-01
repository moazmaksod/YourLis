import flet as ft

# --- Centralized Color Palette ---
# For custom colors, use the hex string directly. Flet will parse it.
# For Flet predefined colors, use ft.colors.CONSTANT_NAME (lowercase 'c', plural 's').
APP_COLORS_DARK = {
    "primary_background": "#1A1A1A",      # Raw hex string
    "secondary_background": "#2C2C2C",    # Raw hex string
    "sidebar_background": "#222222",      # Raw hex string
    "accent_blue": "#3498DB",             # Raw hex string
    "accent_yellow": "#F39C12",           # Raw hex string
    "accent_red": "#E74C3C",              # Raw hex string
    "accent_green": "#2ECC71",            # Raw hex string
    "text_primary": ft.colors.WHITE,      # Correct: ft.colors.WHITE
    "text_secondary": "#CCCCCC",          # Raw hex string
    "divider_border": "#444444",          # Raw hex string
    "gradient_blue_teal_start": "#00CED1", # Raw hex string
    "gradient_blue_teal_end": "#1ABC9C",   # Raw hex string
    "gradient_blue_purple_start": "#3498DB",# Raw hex string
    "gradient_blue_purple_end": "#8E44AD",  # Raw hex string
    "button_background": "#3498DB",       # Raw hex string (Was accent_blue)
    "button_text": ft.colors.WHITE,       # Correct: ft.colors.WHITE
    "button_hover_background": "#4BA0E0", # Raw hex string (Slightly lighter blue)
    "input_fill_color": "#3A3A3A",        # Raw hex string
    "input_border_color": "#666666",      # Raw hex string
    "input_text_color": ft.colors.WHITE,  # Correct: ft.colors.WHITE
    "dialog_background": "#2C2C2C",       # Raw hex string
    "dialog_text": ft.colors.WHITE,       # Correct: ft.colors.WHITE
    "icon_color": ft.colors.WHITE,        # Correct: ft.colors.WHITE
    "scrollbar_thumb_color": ft.colors.GREY_700, # Correct: ft.colors.GREY_700
    "scrollbar_track_color": ft.colors.GREY_900, # Correct: ft.colors.GREY_900
    "card_elevation": 2,
}

APP_COLORS_LIGHT = {
    "primary_background": ft.colors.WHITE,          # Correct: ft.colors.WHITE
    "secondary_background": ft.colors.GREY_200,     # Correct: ft.colors.GREY_200
    "sidebar_background": ft.colors.GREY_100,       # Correct: ft.colors.GREY_100
    "accent_blue": ft.colors.BLUE_600,              # Correct: ft.colors.BLUE_600
    "accent_yellow": ft.colors.YELLOW_700,          # Correct: ft.colors.YELLOW_700
    "accent_red": ft.colors.RED_600,                # Correct: ft.colors.RED_600
    "accent_green": ft.colors.GREEN_600,            # Correct: ft.colors.GREEN_600
    "text_primary": ft.colors.BLACK87,              # Correct: ft.colors.BLACK87
    "text_secondary": ft.colors.BLACK45,            # Correct: ft.colors.BLACK45
    "divider_border": ft.colors.GREY_400,           # Correct: ft.colors.GREY_400
    "button_background": ft.colors.BLUE_600,        # Correct: ft.colors.BLUE_600
    "button_text": ft.colors.WHITE,                 # Correct: ft.colors.WHITE
    "button_hover_background": ft.colors.BLUE_ACCENT_100, # Correct: ft.colors.BLUE_ACCENT_100
    "input_fill_color": ft.colors.GREY_50,          # Correct: ft.colors.GREY_50
    "input_border_color": ft.colors.GREY_400,       # Correct: ft.colors.GREY_400
    "input_text_color": ft.colors.BLACK87,          # Correct: ft.colors.BLACK87
    "dialog_background": ft.colors.WHITE,           # Correct: ft.colors.WHITE
    "dialog_text": ft.colors.BLACK87,               # Correct: ft.colors.BLACK87
    "icon_color": ft.colors.BLACK54,                # Correct: ft.colors.BLACK54
    "scrollbar_thumb_color": ft.colors.GREY_400,    # Correct: ft.colors.GREY_400
    "scrollbar_track_color": ft.colors.GREY_200,    # Correct: ft.colors.GREY_200
    "card_elevation": 1,
}

# Common UI properties
APP_BORDER_RADIUS = 8

# Font definitions
JOSEFIN_SANS_REGULAR_PATH = "/fonts/sans/JosefinSans-Regular.ttf"
JOSEFIN_SANS_BOLD_PATH = "/fonts/sans/JosefinSans-Bold.ttf"
JOSEFIN_SANS_LIGHT_PATH = "/fonts/sans/JosefinSans-Light.ttf"
FONT_FAMILY_JOSEFIN_SANS = "Josefin Sans"

# Common page transitions
common_page_transitions = ft.PageTransitionsTheme(
    android=ft.PageTransitionTheme.OPEN_UPWARDS,
    ios=ft.PageTransitionTheme.CUPERTINO,
    macos=ft.PageTransitionTheme.ZOOM,
    linux=ft.PageTransitionTheme.ZOOM,
    windows=ft.PageTransitionTheme.ZOOM,
)

# --- Dark Text Theme ---
# Using colors directly from APP_COLORS_DARK dictionary
# These values are now either raw hex strings or correct ft.colors.CONSTANT objects
dark_text_theme = ft.TextTheme(
    headline_large=ft.TextStyle(font_family=FONT_FAMILY_JOSEFIN_SANS, weight=ft.FontWeight.BOLD, size=24, color=APP_COLORS_DARK["text_primary"]),
    headline_medium=ft.TextStyle(font_family=FONT_FAMILY_JOSEFIN_SANS, weight=ft.FontWeight.BOLD, size=20, color=APP_COLORS_DARK["text_primary"]),
    headline_small=ft.TextStyle(font_family=FONT_FAMILY_JOSEFIN_SANS, weight=ft.FontWeight.BOLD, size=18, color=APP_COLORS_DARK["text_primary"]),
    title_large=ft.TextStyle(font_family=FONT_FAMILY_JOSEFIN_SANS, weight=ft.FontWeight.BOLD, size=20, color=APP_COLORS_DARK["text_primary"]),
    title_medium=ft.TextStyle(font_family=FONT_FAMILY_JOSEFIN_SANS, weight=ft.FontWeight.BOLD, size=16, color=APP_COLORS_DARK["text_primary"]),
    title_small=ft.TextStyle(font_family=FONT_FAMILY_JOSEFIN_SANS, weight=ft.FontWeight.W_600, size=14, color=APP_COLORS_DARK["text_primary"]),
    body_large=ft.TextStyle(font_family=FONT_FAMILY_JOSEFIN_SANS, weight=ft.FontWeight.NORMAL, size=16, color=APP_COLORS_DARK["text_primary"]),
    body_medium=ft.TextStyle(font_family=FONT_FAMILY_JOSEFIN_SANS, weight=ft.FontWeight.NORMAL, size=14, color=APP_COLORS_DARK["text_primary"]),
    label_medium=ft.TextStyle(font_family=FONT_FAMILY_JOSEFIN_SANS, weight=ft.FontWeight.NORMAL, size=12, color=APP_COLORS_DARK["text_secondary"]),
)

# --- Light Text Theme ---
light_text_theme = ft.TextTheme(
    headline_large=ft.TextStyle(font_family=FONT_FAMILY_JOSEFIN_SANS, weight=ft.FontWeight.BOLD, size=24, color=APP_COLORS_LIGHT["text_primary"]),
    headline_medium=ft.TextStyle(font_family=FONT_FAMILY_JOSEFIN_SANS, weight=ft.FontWeight.BOLD, size=20, color=APP_COLORS_LIGHT["text_primary"]),
    headline_small=ft.TextStyle(font_family=FONT_FAMILY_JOSEFIN_SANS, weight=ft.FontWeight.BOLD, size=18, color=APP_COLORS_LIGHT["text_primary"]),
    title_large=ft.TextStyle(font_family=FONT_FAMILY_JOSEFIN_SANS, weight=ft.FontWeight.BOLD, size=20, color=APP_COLORS_LIGHT["text_primary"]),
    title_medium=ft.TextStyle(font_family=FONT_FAMILY_JOSEFIN_SANS, weight=ft.FontWeight.BOLD, size=16, color=APP_COLORS_LIGHT["text_primary"]),
    title_small=ft.TextStyle(font_family=FONT_FAMILY_JOSEFIN_SANS, weight=ft.FontWeight.W_600, size=14, color=APP_COLORS_LIGHT["text_primary"]),
    body_large=ft.TextStyle(font_family=FONT_FAMILY_JOSEFIN_SANS, weight=ft.FontWeight.NORMAL, size=16, color=APP_COLORS_LIGHT["text_primary"]),
    body_medium=ft.TextStyle(font_family=FONT_FAMILY_JOSEFIN_SANS, weight=ft.FontWeight.NORMAL, size=14, color=APP_COLORS_LIGHT["text_primary"]),
    label_medium=ft.TextStyle(font_family=FONT_FAMILY_JOSEFIN_SANS, weight=ft.FontWeight.NORMAL, size=12, color=APP_COLORS_LIGHT["text_secondary"]),
)

# --- Dark Theme ---
dark_theme = ft.Theme(
    color_scheme=ft.ColorScheme( # Correct: ft.ColorScheme
        surface=APP_COLORS_DARK["primary_background"],
        on_surface=APP_COLORS_DARK["text_primary"],
        background=APP_COLORS_DARK["primary_background"],
        on_background=APP_COLORS_DARK["text_primary"],
        primary=APP_COLORS_DARK["accent_blue"],
        on_primary=APP_COLORS_DARK["button_text"],
        secondary=APP_COLORS_DARK["accent_green"],
        on_secondary=APP_COLORS_DARK["button_text"],
        error=APP_COLORS_DARK["accent_red"],
        on_error=APP_COLORS_DARK["button_text"],
        surface_variant=APP_COLORS_DARK["secondary_background"],
        on_surface_variant=APP_COLORS_DARK["text_secondary"],
        outline=APP_COLORS_DARK["divider_border"],
    ),
    font_family=FONT_FAMILY_JOSEFIN_SANS,
    page_transitions=common_page_transitions,
    text_theme=dark_text_theme,
    use_material3=True,
    elevated_button_theme=ft.ElevatedButtonTheme(
        style=ft.ButtonStyle(
            bgcolor=APP_COLORS_DARK["button_background"],
            color=APP_COLORS_DARK["button_text"],
            shape=ft.RoundedRectangleBorder(radius=APP_BORDER_RADIUS),
        )
    ),
    outlined_button_theme=ft.OutlinedButtonTheme(
        style=ft.ButtonStyle(
            color=APP_COLORS_DARK["button_background"], # Text/Icon color for outlined button
            side=ft.BorderSide(1, APP_COLORS_DARK["button_background"]),
            shape=ft.RoundedRectangleBorder(radius=APP_BORDER_RADIUS),
        )
    ),
    text_button_theme=ft.TextButtonTheme(
        style=ft.ButtonStyle(
            color=APP_COLORS_DARK["button_background"], # Text/Icon color for text button
            shape=ft.RoundedRectangleBorder(radius=APP_BORDER_RADIUS),
        )
    ),
    input_decoration_theme=ft.InputDecorationTheme(
        fill_color=APP_COLORS_DARK["input_fill_color"],
        border=ft.OutlineInputBorder(border_side=ft.BorderSide(1, APP_COLORS_DARK["input_border_color"]), border_radius=ft.BorderRadius.all(APP_BORDER_RADIUS)),
        focused_border=ft.OutlineInputBorder(border_side=ft.BorderSide(2, APP_COLORS_DARK["accent_blue"]), border_radius=ft.BorderRadius.all(APP_BORDER_RADIUS)),
        label_style=ft.TextStyle(color=APP_COLORS_DARK["text_secondary"]),
        hint_style=ft.TextStyle(color=APP_COLORS_DARK["text_secondary"]),
        content_padding=ft.padding.symmetric(vertical=10, horizontal=12),
        filled=True,
    ),
    icon_theme=ft.IconTheme(
        color=APP_COLORS_DARK["icon_color"],
        size=24,
    ),
    dialog_theme=ft.DialogTheme(
        bgcolor=APP_COLORS_DARK["dialog_background"],
        content_text_style=ft.TextStyle(color=APP_COLORS_DARK["dialog_text"]),
        shape=ft.RoundedRectangleBorder(radius=APP_BORDER_RADIUS),
    ),
    card_theme=ft.CardTheme(
        color=APP_COLORS_DARK["secondary_background"],
        elevation=APP_COLORS_DARK["card_elevation"],
        shape=ft.RoundedRectangleBorder(radius=APP_BORDER_RADIUS),
    ),
    scrollbar_theme=ft.ScrollbarTheme(
        thumb_color=APP_COLORS_DARK["scrollbar_thumb_color"],
        track_color=APP_COLORS_DARK["scrollbar_track_color"],
        thickness=6,
        radius=ft.Radius.circular(3),
        main_axis_margin=5,
        cross_axis_margin=5,
    ),
)

# --- Light Theme ---
light_theme = ft.Theme(
    color_scheme=ft.ColorScheme( # Correct: ft.ColorScheme
        surface=APP_COLORS_LIGHT["primary_background"],
        on_surface=APP_COLORS_LIGHT["text_primary"],
        background=APP_COLORS_LIGHT["primary_background"],
        on_background=APP_COLORS_LIGHT["text_primary"],
        primary=APP_COLORS_LIGHT["accent_blue"],
        on_primary=APP_COLORS_LIGHT["button_text"],
        secondary=APP_COLORS_LIGHT["accent_green"],
        on_secondary=APP_COLORS_LIGHT["button_text"],
        error=APP_COLORS_LIGHT["accent_red"],
        on_error=APP_COLORS_LIGHT["button_text"],
        surface_variant=APP_COLORS_LIGHT["secondary_background"],
        on_surface_variant=APP_COLORS_LIGHT["text_secondary"],
        outline=APP_COLORS_LIGHT["divider_border"],
    ),
    font_family=FONT_FAMILY_JOSEFIN_SANS,
    page_transitions=common_page_transitions,
    text_theme=light_text_theme,
    use_material3=True,
    elevated_button_theme=ft.ElevatedButtonTheme(
        style=ft.ButtonStyle(
            bgcolor=APP_COLORS_LIGHT["button_background"],
            color=APP_COLORS_LIGHT["button_text"],
            shape=ft.RoundedRectangleBorder(radius=APP_BORDER_RADIUS),
        )
    ),
    outlined_button_theme=ft.OutlinedButtonTheme(
        style=ft.ButtonStyle(
            color=APP_COLORS_LIGHT["button_background"],
            side=ft.BorderSide(1, APP_COLORS_LIGHT["button_background"]),
            shape=ft.RoundedRectangleBorder(radius=APP_BORDER_RADIUS),
        )
    ),
    text_button_theme=ft.TextButtonTheme(
        style=ft.ButtonStyle(
            color=APP_COLORS_LIGHT["button_background"],
            shape=ft.RoundedRectangleBorder(radius=APP_BORDER_RADIUS),
        )
    ),
    input_decoration_theme=ft.InputDecorationTheme(
        fill_color=APP_COLORS_LIGHT["input_fill_color"],
        border=ft.OutlineInputBorder(border_side=ft.BorderSide(1, APP_COLORS_LIGHT["input_border_color"]), border_radius=ft.BorderRadius.all(APP_BORDER_RADIUS)),
        focused_border=ft.OutlineInputBorder(border_side=ft.BorderSide(2, APP_COLORS_LIGHT["accent_blue"]), border_radius=ft.BorderRadius.all(APP_BORDER_RADIUS)),
        label_style=ft.TextStyle(color=APP_COLORS_LIGHT["text_secondary"]),
        hint_style=ft.TextStyle(color=APP_COLORS_LIGHT["text_secondary"]),
        content_padding=ft.padding.symmetric(vertical=10, horizontal=12),
        filled=True,
    ),
    icon_theme=ft.IconTheme(
        color=APP_COLORS_LIGHT["icon_color"],
        size=24,
    ),
    dialog_theme=ft.DialogTheme(
        bgcolor=APP_COLORS_LIGHT["dialog_background"],
        content_text_style=ft.TextStyle(color=APP_COLORS_LIGHT["dialog_text"]),
        shape=ft.RoundedRectangleBorder(radius=APP_BORDER_RADIUS),
    ),
    card_theme=ft.CardTheme(
        color=APP_COLORS_LIGHT["secondary_background"],
        elevation=APP_COLORS_LIGHT["card_elevation"],
        shape=ft.RoundedRectangleBorder(radius=APP_BORDER_RADIUS),
    ),
    scrollbar_theme=ft.ScrollbarTheme(
        thumb_color=APP_COLORS_LIGHT["scrollbar_thumb_color"],
        track_color=APP_COLORS_LIGHT["scrollbar_track_color"],
        thickness=6,
        radius=ft.Radius.circular(3),
        main_axis_margin=5,
        cross_axis_margin=5,
    ),
)

def get_app_themes() -> tuple[ft.Theme, ft.Theme]:
    """Returns the light and dark themes for the application."""
    return light_theme, dark_theme

app_fonts = {
    FONT_FAMILY_JOSEFIN_SANS: JOSEFIN_SANS_REGULAR_PATH,
    f"{FONT_FAMILY_JOSEFIN_SANS} Bold": JOSEFIN_SANS_BOLD_PATH,
    f"{FONT_FAMILY_JOSEFIN_SANS} Light": JOSEFIN_SANS_LIGHT_PATH,
}

ft.theme = ft.Theme(use_material3=True)

if __name__ == "__main__":
    # Debug prints
    print("--- Dark Theme Debug Info ---")
    print(f"Button Background: {dark_theme.elevated_button_theme.style.bgcolor}") #type: ignore
    print(f"Input Fill Color: {dark_theme.input_decoration_theme.fill_color}") #type: ignore
    print(f"Text Primary: {APP_COLORS_DARK['text_primary']}")

    print("\n--- Light Theme Debug Info ---")
    print(f"Button Background: {light_theme.elevated_button_theme.style.bgcolor}") #type: ignore
    print(f"Input Fill Color: {light_theme.input_decoration_theme.fill_color}") #type: ignore
    print(f"Text Primary: {APP_COLORS_LIGHT['text_primary']}")
```
