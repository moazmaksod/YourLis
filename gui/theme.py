import flet as ft

# --- Centralized Color Palette ---
# Define semantic names and their light/dark Flet color values.
# This is the new single source of truth for core application colors.
APP_COLORS = {
    "text_default": { # For primary body text, titles, headlines
        "light": ft.Colors.BLACK87, # Slightly off-black for better aesthetics
        "dark": ft.Colors.WHITE,
    },
    "text_muted": { # For secondary text, hints, disabled text (can be adjusted)
        "light": ft.Colors.with_opacity(0.65, ft.Colors.BLACK),
        "dark": ft.Colors.with_opacity(0.70, ft.Colors.WHITE),
    },
    "surface_background": { # Main background for pages and larger surfaces
        "light": ft.Colors.WHITE,
        "dark": ft.Colors.BLACK, # A common very dark background
    },
    "dialog_background": { # Background for dialogs
        "light": ft.Colors.WHITE,
        "dark": ft.Colors.with_opacity(0.15, ft.Colors.WHITE), # Common dark dialog bg
    },
    "card_background": { # Background for cards or distinct sections
        "light": ft.Colors.SURFACE_CONTAINER_HIGHEST, # Material 3 concept for slightly off-main bg
        "dark": ft.Colors.with_opacity(0.08, ft.Colors.WHITE), # Darker card
    },
    "accent_primary": { # Main interactive color (e.g., buttons, active indicators)
        "light": ft.Colors.BLUE_600,
        "dark": ft.Colors.BLUE_300,
    },
    "accent_secondary": { # Secondary interactive color
        "light": ft.Colors.PINK_600,
        "dark": ft.Colors.PINK_300,
    },
    "error_color": {
        "light": ft.Colors.RED_700,
        "dark": ft.Colors.RED_400,
    },
    "success_color": {
        "light": ft.Colors.GREEN_700,
        "dark": ft.Colors.GREEN_400,
    },
    "warning_color": {
        "light": ft.Colors.AMBER_700,
        "dark": ft.Colors.AMBER_400,
    },
    "border_outline_color": { # For borders, dividers
        "light": ft.Colors.GREY_300,
        "dark": ft.Colors.GREY_700,
    },
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

# --- Light Text Theme (using centralized palette) ---
light_text_theme = ft.TextTheme(
    headline_large=ft.TextStyle(font_family=FONT_FAMILY_JOSEFIN_SANS, weight=ft.FontWeight.BOLD, size=24, color=APP_COLORS["text_default"]["light"]),
    headline_medium=ft.TextStyle(font_family=FONT_FAMILY_JOSEFIN_SANS, weight=ft.FontWeight.BOLD, size=20, color=APP_COLORS["text_default"]["light"]),
    headline_small=ft.TextStyle(font_family=FONT_FAMILY_JOSEFIN_SANS, weight=ft.FontWeight.BOLD, size=18, color=APP_COLORS["text_default"]["light"]),
    title_large=ft.TextStyle(font_family=FONT_FAMILY_JOSEFIN_SANS, weight=ft.FontWeight.BOLD, size=20, color=APP_COLORS["text_default"]["light"]),
    title_medium=ft.TextStyle(font_family=FONT_FAMILY_JOSEFIN_SANS, weight=ft.FontWeight.BOLD, size=16, color=APP_COLORS["text_default"]["light"]),
    title_small=ft.TextStyle(font_family=FONT_FAMILY_JOSEFIN_SANS, weight=ft.FontWeight.W_600, size=14, color=APP_COLORS["text_default"]["light"]),
    body_large=ft.TextStyle(font_family=FONT_FAMILY_JOSEFIN_SANS, weight=ft.FontWeight.NORMAL, size=16, color=APP_COLORS["text_default"]["light"]),
    body_medium=ft.TextStyle(font_family=FONT_FAMILY_JOSEFIN_SANS, weight=ft.FontWeight.NORMAL, size=14, color=APP_COLORS["text_default"]["light"]), # Default body text
    label_medium=ft.TextStyle(font_family=FONT_FAMILY_JOSEFIN_SANS, weight=ft.FontWeight.NORMAL, size=12, color=APP_COLORS["text_muted"]["light"]), # Muted for labels
)

# --- Dark Text Theme (using centralized palette) ---
dark_text_theme = ft.TextTheme(
    headline_large=ft.TextStyle(font_family=FONT_FAMILY_JOSEFIN_SANS, weight=ft.FontWeight.BOLD, size=24, color=APP_COLORS["text_default"]["dark"]),
    headline_medium=ft.TextStyle(font_family=FONT_FAMILY_JOSEFIN_SANS, weight=ft.FontWeight.BOLD, size=20, color=APP_COLORS["text_default"]["dark"]),
    headline_small=ft.TextStyle(font_family=FONT_FAMILY_JOSEFIN_SANS, weight=ft.FontWeight.BOLD, size=18, color=APP_COLORS["text_default"]["dark"]),
    title_large=ft.TextStyle(font_family=FONT_FAMILY_JOSEFIN_SANS, weight=ft.FontWeight.BOLD, size=20, color=APP_COLORS["text_default"]["dark"]),
    title_medium=ft.TextStyle(font_family=FONT_FAMILY_JOSEFIN_SANS, weight=ft.FontWeight.BOLD, size=16, color=APP_COLORS["text_default"]["dark"]),
    title_small=ft.TextStyle(font_family=FONT_FAMILY_JOSEFIN_SANS, weight=ft.FontWeight.W_600, size=14, color=APP_COLORS["text_default"]["dark"]),
    body_large=ft.TextStyle(font_family=FONT_FAMILY_JOSEFIN_SANS, weight=ft.FontWeight.NORMAL, size=16, color=APP_COLORS["text_default"]["dark"]),
    body_medium=ft.TextStyle(font_family=FONT_FAMILY_JOSEFIN_SANS, weight=ft.FontWeight.NORMAL, size=14, color=APP_COLORS["text_default"]["dark"]), # Default body text
    label_medium=ft.TextStyle(font_family=FONT_FAMILY_JOSEFIN_SANS, weight=ft.FontWeight.NORMAL, size=12, color=APP_COLORS["text_muted"]["dark"]), # Muted for labels
)

# --- Light Theme (Color Scheme to be updated next) ---
light_theme = ft.Theme(
    color_scheme=ft.ColorScheme( # Will be updated to use APP_COLORS
        on_surface=APP_COLORS["text_default"]["light"],
        surface=APP_COLORS["surface_background"]["light"],
        primary=APP_COLORS["accent_primary"]["light"],
        secondary=APP_COLORS["accent_secondary"]["light"],
        error=APP_COLORS["error_color"]["light"],
        # Add other mappings here as needed, e.g.,
        # primary_container, on_primary, on_secondary, etc.
    ),
    # color_scheme_seed=ft.Colors.BLUE_GREY, # Consider removing if ColorScheme is fully defined
    font_family=FONT_FAMILY_JOSEFIN_SANS,
    page_transitions=common_page_transitions,
    text_theme=light_text_theme,
    use_material3=True,
)

# --- Dark Theme (Color Scheme to be updated next) ---
dark_theme = ft.Theme(
    color_scheme=ft.ColorScheme( # Will be updated to use APP_COLORS
        on_surface=APP_COLORS["text_default"]["dark"],
        surface=APP_COLORS["surface_background"]["dark"],
        primary=APP_COLORS["accent_primary"]["dark"],
        secondary=APP_COLORS["accent_secondary"]["dark"],
        error=APP_COLORS["error_color"]["dark"],
        # Add other mappings here
    ),
    # color_scheme_seed=ft.Colors.BLUE_GREY, # Consider removing
    font_family=FONT_FAMILY_JOSEFIN_SANS,
    page_transitions=common_page_transitions,
    text_theme=dark_text_theme,
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

# Ensure Flet uses Material 3 design system by default
ft.theme = ft.Theme(use_material3=True)

if __name__ == "__main__":
    # Example of how to print theme details (for debugging)
    print("APP_COLORS['text_default']['light']:", APP_COLORS['text_default']['light'])
    print("Light Theme Text Theme Body Medium Color:", light_theme.text_theme.body_medium.color) #type: ignore
    print("Light Theme ColorScheme on_surface:", light_theme.color_scheme.on_surface) #type: ignore
    print("\nAPP_COLORS['text_default']['dark']:", APP_COLORS['text_default']['dark'])
    print("Dark Theme Text Theme Body Medium Color:", dark_theme.text_theme.body_medium.color) #type: ignore
    print("Dark Theme ColorScheme on_surface:", dark_theme.color_scheme.on_surface) #type: ignore

    # Test accessing a color for a component
    # print("\nSimulated component colors:")
    # print(f"Light mode button text color (on_primary): {light_theme.color_scheme.on_primary}")
    # print(f"Light mode button background color (primary): {light_theme.color_scheme.primary}")
    # print(f"Dark mode button text color (on_primary): {dark_theme.color_scheme.on_primary}")
    # print(f"Dark mode button background color (primary): {dark_theme.color_scheme.primary}")
