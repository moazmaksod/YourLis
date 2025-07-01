import flet as ft

# --- Centralized Color Palette (Dark Mode Focused as per User Spec) ---
# Using ft.Color("hex_code") for specified colors, and ft.Color.WHITE/BLACK for pure white/black,
# and ft.Color.CONSTANT_NAME for other Flet predefined color constants.
APP_COLORS_DARK = {
    "primary_background": ft.Color("#1A1A1A"),      # Deep charcoal black
    "secondary_background": ft.Color("#2C2C2C"),    # Slightly lighter, warm dark grey (for cards)
    "sidebar_background": ft.Color("#222222"),      # Darker grey for sidebar

    "accent_blue": ft.Color("#3498DB"),             # Vibrant blue
    "accent_yellow": ft.Color("#F39C12"),           # Bright, orangey yellow
    "accent_red": ft.Color("#E74C3C"),               # Strong, clear red
    "accent_green": ft.Color("#2ECC71"),             # Fresh, medium-dark green

    "text_primary": ft.Color.WHITE,                 # Pure white for prominent titles
    "text_secondary": ft.Color("#CCCCCC"),          # Light grey for less prominent text (can also use #B0B0B0)

    "divider_border": ft.Color("#444444"),          # Subtle light grey for borders/dividers

    "gradient_blue_teal_start": ft.Color("#00CED1"), # Dark Turquoise
    "gradient_blue_teal_end": ft.Color("#1ABC9C"),   # Turquoise
    "gradient_blue_purple_start": ft.Color("#3498DB"),# Medium Blue
    "gradient_blue_purple_end": ft.Color("#8E44AD"),  # Soft Purple
}

APP_COLORS_LIGHT = {
    "primary_background": ft.Color.WHITE,
    "secondary_background": ft.Color.GREY_200,
    "sidebar_background": ft.Color.GREY_100,

    "accent_blue": ft.Color.BLUE_600,
    "accent_yellow": ft.Color.YELLOW_700,
    "accent_red": ft.Color.RED_600,
    "accent_green": ft.Color.GREEN_600,

    "text_primary": ft.Color.BLACK87,
    "text_secondary": ft.Color.BLACK45,

    "divider_border": ft.Color.GREY_400,
}


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

# --- Dark Text Theme (using new palette) ---
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

# --- Light Text Theme (using new palette) ---
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
        on_primary=ft.Color.WHITE,
        secondary=APP_COLORS_DARK["accent_green"],
        on_secondary=ft.Color.WHITE,
        error=APP_COLORS_DARK["accent_red"],
        on_error=ft.Color.WHITE,
        surface_variant=APP_COLORS_DARK["secondary_background"],
        on_surface_variant=APP_COLORS_DARK["text_secondary"],
        outline=APP_COLORS_DARK["divider_border"],
    ),
    font_family=FONT_FAMILY_JOSEFIN_SANS,
    page_transitions=common_page_transitions,
    text_theme=dark_text_theme,
    use_material3=True,
)

# --- Light Theme ---
light_theme = ft.Theme(
    color_scheme=ft.ColorScheme(
        surface=APP_COLORS_LIGHT["primary_background"],
        on_surface=APP_COLORS_LIGHT["text_primary"],
        background=APP_COLORS_LIGHT["primary_background"],
        on_background=APP_COLORS_LIGHT["text_primary"],
        primary=APP_COLORS_LIGHT["accent_blue"],
        on_primary=ft.Color.WHITE,
        secondary=APP_COLORS_LIGHT["accent_green"],
        on_secondary=ft.Color.WHITE,
        error=APP_COLORS_LIGHT["accent_red"],
        on_error=ft.Color.WHITE,
        surface_variant=APP_COLORS_LIGHT["secondary_background"],
        on_surface_variant=APP_COLORS_LIGHT["text_secondary"],
        outline=APP_COLORS_LIGHT["divider_border"],
    ),
    font_family=FONT_FAMILY_JOSEFIN_SANS,
    page_transitions=common_page_transitions,
    text_theme=light_text_theme,
    use_material3=True,
)

def get_app_themes() -> tuple[ft.Theme, ft.Theme]:
    """Returns the light and dark themes for the application."""
    return light_theme, dark_theme

app_fonts = {
    FONT_FAMILY_JOSEFIN_SANS: JOSEFIN_SANS_REGULAR_PATH,
    f"{FONT_FAMILY_JOSEFIN_SANS} Bold": JOSEFIN_SANS_BOLD_PATH,
    f"{FONT_FAMILY_JOSEFIN_SANS} Light": JOSEFIN_SANS_LIGHT_PATH,
}

# This global ft.theme might not be necessary if page.theme and page.dark_theme are always set.
# It acts as a fallback. It should also use Material 3 if other themes do.
ft.theme = ft.Theme(use_material3=True)

if __name__ == "__main__":
    # This block is for direct execution testing of this file, which is unlikely in a Flet app.
    # If you were to run `python gui/theme.py`, these prints would execute.
    # For Flet app context, these won't run unless explicitly called.
    print("--- Dark Theme Debug Info ---")
    print(f"Primary Background (surface): {dark_theme.color_scheme.surface}") #type: ignore
    print(f"Primary Text (on_surface): {dark_theme.color_scheme.on_surface}") #type: ignore
    print(f"Card Background (surface_variant): {dark_theme.color_scheme.surface_variant}") #type: ignore
    print(f"Card Text (on_surface_variant): {dark_theme.color_scheme.on_surface_variant}") #type: ignore
    print(f"Accent Blue (primary): {dark_theme.color_scheme.primary}") #type: ignore
    print(f"Text on Accent Blue (on_primary): {dark_theme.color_scheme.on_primary}") #type: ignore
    print(f"Sidebar Background (intended): {APP_COLORS_DARK['sidebar_background']}")
    print(f"Divider/Border (outline): {dark_theme.color_scheme.outline}") #type: ignore
    print(f"Text Theme Body Medium Color: {dark_theme.text_theme.body_medium.color}") #type: ignore

    print("\n--- Light Theme Debug Info ---")
    print(f"Primary Background (surface): {light_theme.color_scheme.surface}") #type: ignore
    print(f"Primary Text (on_surface): {light_theme.color_scheme.on_surface}") #type: ignore
    print(f"Text Theme Body Medium Color: {light_theme.text_theme.body_medium.color}") #type: ignore

```
