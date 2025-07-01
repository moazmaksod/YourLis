import flet as ft

# --- Centralized Color Palette ---
# For custom colors, use ft.Color("hex_string").
# For Flet predefined colors, use ft.Colors.CONSTANT_NAME.
APP_COLORS_DARK = {
    "primary_background": ft.Color("#1A1A1A"),
    "secondary_background": ft.Color("#2C2C2C"),
    "sidebar_background": ft.Color("#222222"),
    "accent_blue": ft.Color("#3498DB"),
    "accent_yellow": ft.Color("#F39C12"),
    "accent_red": ft.Color("#E74C3C"),
    "accent_green": ft.Color("#2ECC71"),
    "text_primary": ft.Colors.WHITE,
    "text_secondary": ft.Color("#CCCCCC"),
    "divider_border": ft.Color("#444444"),
    "gradient_blue_teal_start": ft.Color("#00CED1"),
    "gradient_blue_teal_end": ft.Color("#1ABC9C"),
    "gradient_blue_purple_start": ft.Color("#3498DB"),
    "gradient_blue_purple_end": ft.Color("#8E44AD"),
    "button_background": ft.Color("#3498DB"), # Was accent_blue
    "button_text": ft.Colors.WHITE,
    "button_hover_background": ft.Color("#4BA0E0"), # Slightly lighter blue
    "input_fill_color": ft.Color("#3A3A3A"),
    "input_border_color": ft.Color("#666666"),
    "input_text_color": ft.Colors.WHITE,
    "dialog_background": ft.Color("#2C2C2C"),
    "dialog_text": ft.Colors.WHITE,
    "icon_color": ft.Colors.WHITE,
    "scrollbar_thumb_color": ft.Colors.GREY_700, # Simplified from MaterialState
    "scrollbar_track_color": ft.Colors.GREY_900, # Simplified
    "card_elevation": 2,
}

APP_COLORS_LIGHT = {
    "primary_background": ft.Colors.WHITE,
    "secondary_background": ft.Colors.GREY_200,
    "sidebar_background": ft.Colors.GREY_100,
    "accent_blue": ft.Colors.BLUE_600,
    "accent_yellow": ft.Colors.YELLOW_700,
    "accent_red": ft.Colors.RED_600,
    "accent_green": ft.Colors.GREEN_600,
    "text_primary": ft.Colors.BLACK87,
    "text_secondary": ft.Colors.BLACK45, # Using a predefined Flet color constant
    "divider_border": ft.Colors.GREY_400,
    "button_background": ft.Colors.BLUE_600,
    "button_text": ft.Colors.WHITE,
    "button_hover_background": ft.Colors.BLUE_ACCENT_100, # A light Flet blue
    "input_fill_color": ft.Colors.GREY_50,
    "input_border_color": ft.Colors.GREY_400,
    "input_text_color": ft.Colors.BLACK87,
    "dialog_background": ft.Colors.WHITE,
    "dialog_text": ft.Colors.BLACK87,
    "icon_color": ft.Colors.BLACK54,
    "scrollbar_thumb_color": ft.Colors.GREY_400, # Simplified
    "scrollbar_track_color": ft.Colors.GREY_200, # Simplified
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
    color_scheme=ft.ColorScheme(
        surface=APP_COLORS_DARK["primary_background"],
        on_surface=APP_COLORS_DARK["text_primary"],
        background=APP_COLORS_DARK["primary_background"],
        on_background=APP_COLORS_DARK["text_primary"],
        primary=APP_COLORS_DARK["accent_blue"],
        on_primary=APP_COLORS_DARK["button_text"], # Usually white for dark accents
        secondary=APP_COLORS_DARK["accent_green"],
        on_secondary=APP_COLORS_DARK["button_text"], # Usually white for dark accents
        error=APP_COLORS_DARK["accent_red"],
        on_error=APP_COLORS_DARK["button_text"], # Usually white for dark accents
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
            bgcolor=APP_COLORS_DARK["button_background"], # Simplified: no MaterialState
            color=APP_COLORS_DARK["button_text"],
            shape=ft.RoundedRectangleBorder(radius=APP_BORDER_RADIUS),
        )
    ),
    outlined_button_theme=ft.OutlinedButtonTheme(
        style=ft.ButtonStyle(
            color=APP_COLORS_DARK["button_background"], # Simplified
            side=ft.BorderSide(1, APP_COLORS_DARK["button_background"]), # Simplified
            shape=ft.RoundedRectangleBorder(radius=APP_BORDER_RADIUS),
        )
    ),
    text_button_theme=ft.TextButtonTheme(
        style=ft.ButtonStyle(
            color=APP_COLORS_DARK["button_background"], # Simplified
            shape=ft.RoundedRectangleBorder(radius=APP_BORDER_RADIUS),
        )
    ),
    input_decoration_theme=ft.InputDecorationTheme(
        fill_color=APP_COLORS_DARK["input_fill_color"],
        # border_side is part of 'border', 'enabled_border', 'focused_border' etc.
        # We'll set a general 'border' and 'focused_border'.
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
    scrollbar_theme=ft.ScrollbarTheme( # Simplified, no MaterialState
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
    color_scheme=ft.ColorScheme(
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
            bgcolor=APP_COLORS_LIGHT["button_background"], # Simplified
            color=APP_COLORS_LIGHT["button_text"],
            shape=ft.RoundedRectangleBorder(radius=APP_BORDER_RADIUS),
        )
    ),
    outlined_button_theme=ft.OutlinedButtonTheme(
        style=ft.ButtonStyle(
            color=APP_COLORS_LIGHT["button_background"], # Simplified
            side=ft.BorderSide(1, APP_COLORS_LIGHT["button_background"]), # Simplified
            shape=ft.RoundedRectangleBorder(radius=APP_BORDER_RADIUS),
        )
    ),
    text_button_theme=ft.TextButtonTheme(
        style=ft.ButtonStyle(
            color=APP_COLORS_LIGHT["button_background"], # Simplified
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
    scrollbar_theme=ft.ScrollbarTheme( # Simplified
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
