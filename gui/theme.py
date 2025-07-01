import flet as ft

# --- Centralized Color Palette (Dark Mode Focused as per User Spec) ---
# Using ft.Color("hex_code") for specified colors, and ft.Color.WHITE/BLACK for pure white/black.
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

    # Gradient colors - these are harder to use directly in simple ColorScheme/TextStyle
    # but can be stored here for reference or used by custom components.
    "gradient_blue_teal_start": ft.Color("#00CED1"), # Dark Turquoise
    "gradient_blue_teal_end": ft.Color("#1ABC9C"),   # Turquoise
    "gradient_blue_purple_start": ft.Color("#3498DB"),# Medium Blue
    "gradient_blue_purple_end": ft.Color("#8E44AD"),  # Soft Purple
}

# (A basic light theme counterpart can be defined later if needed)
# For now, we can make a placeholder light theme or derive it simply.
APP_COLORS_LIGHT = {
    "primary_background": ft.Color.WHITE,
    "secondary_background": ft.Color.GREY_200, # Example
    "sidebar_background": ft.Color.GREY_100,  # Example

    "accent_blue": ft.Color.BLUE_600,       # Example
    "accent_yellow": ft.Color.YELLOW_700,   # Example
    "accent_red": ft.Color.RED_600,         # Example
    "accent_green": ft.Color.GREEN_600,     # Example

    "text_primary": ft.Color.BLACK87,
    "text_secondary": ft.Color.BLACK45,

    "divider_border": ft.Color.GREY_400,    # Example
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
        # Primary surface colors
        surface=APP_COLORS_DARK["primary_background"],
        on_surface=APP_COLORS_DARK["text_primary"],
        # Background is often the same as surface for main content area
        background=APP_COLORS_DARK["primary_background"],
        on_background=APP_COLORS_DARK["text_primary"],

        # Primary accent color (used for main interactive elements like buttons)
        primary=APP_COLORS_DARK["accent_blue"],
        on_primary=ft.Color.WHITE, # Text/icons on primary background

        # Secondary accent color (for other interactive elements)
        secondary=APP_COLORS_DARK["accent_green"], # Example: using green as secondary
        on_secondary=ft.Color.WHITE, # Text/icons on secondary background

        # Error color
        error=APP_COLORS_DARK["accent_red"],
        on_error=ft.Color.WHITE, # Text/icons on error background

        # For cards or sections that stand out slightly from the main surface
        surface_variant=APP_COLORS_DARK["secondary_background"],
        on_surface_variant=APP_COLORS_DARK["text_secondary"],

        outline=APP_COLORS_DARK["divider_border"],
    ),
    font_family=FONT_FAMILY_JOSEFIN_SANS,
    page_transitions=common_page_transitions,
    text_theme=dark_text_theme,
    use_material3=True,
    # Example for specific component themes (can be expanded)
    # elevated_button_theme=ft.ElevatedButtonThemeData(
    #     style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10))
    # ),
    # text_button_theme=ft.TextButtonThemeData(
    #     style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10))
    # ),
    # navigation_rail_theme=ft.NavigationRailThemeData(
    #    selected_icon_theme=ft.IconThemeData(color=APP_COLORS_DARK["accent_blue"]),
    #    unselected_icon_theme=ft.IconThemeData(color=APP_COLORS_DARK["text_secondary"]),
    #    selected_label_text_style=ft.TextStyle(color=APP_COLORS_DARK["accent_blue"]),
    #    unselected_label_text_style=ft.TextStyle(color=APP_COLORS_DARK["text_secondary"]),
    #    # indicator_color=APP_COLORS_DARK["accent_blue"], # For the selection indicator
    # )
)

# --- Light Theme (basic placeholder, can be detailed later) ---
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

ft.theme = ft.Theme(use_material3=True)

if __name__ == "__main__":
    pass # Add debug prints here if needed
```
