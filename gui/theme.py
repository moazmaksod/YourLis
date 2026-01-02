import flet as ft
from typing import Dict, Final

# ==============================================================================
# --- 1. THEME CONFIGURATION & CONSTANTS ---
# ==============================================================================

# --- Font Family ---
# Define the primary font family for consistent use across the app.
FONT_FAMILY_JOSEFIN_SANS: Final[str] = "Josefin Sans"

# --- App Fonts ---
# A dictionary mapping the font family names to their file paths.
# This is loaded into the app to make the fonts available.
APP_FONTS: Final[Dict[str, str]] = {
    FONT_FAMILY_JOSEFIN_SANS: "/fonts/sans/JosefinSans-Regular.ttf",
    f"{FONT_FAMILY_JOSEFIN_SANS} Bold": "/fonts/sans/JosefinSans-Bold.ttf",
    f"{FONT_FAMILY_JOSEFIN_SANS} Light": "/fonts/sans/JosefinSans-Light.ttf",
}

# --- Common Page Transitions ---
# Centralize page transition themes for uniform navigation animations.
COMMON_PAGE_TRANSITIONS: Final[ft.PageTransitionsTheme] = ft.PageTransitionsTheme(
    android=ft.PageTransitionTheme.OPEN_UPWARDS,
    ios=ft.PageTransitionTheme.CUPERTINO,
    macos=ft.PageTransitionTheme.ZOOM,
    linux=ft.PageTransitionTheme.ZOOM,
    windows=ft.PageTransitionTheme.ZOOM,
)

# ==============================================================================
# --- 2. COLOR DEFINITIONS (SINGLE SOURCE OF TRUTH) ---
# ==============================================================================

# --- Light Theme Colors ---
class LightThemeColors:
    PRIMARY: Final[str] = "#2196F3"          # Blue
    ON_PRIMARY: Final[str] = "#FFFFFF"
    BACKGROUND: Final[str] = "#FFFFFF"
    ON_BACKGROUND: Final[str] = "#000000"
    SURFACE: Final[str] = "#FFFFFF"
    ON_SURFACE: Final[str] = "#000000"
    SURFACE_VARIANT: Final[str] = "#F5F5F5"
    ON_SURFACE_VARIANT: Final[str] = "#333333"
    SECONDARY: Final[str] = "#FFEB3B"        # Yellow
    ON_SECONDARY: Final[str] = "#000000"
    ERROR: Final[str] = "#E74C3C"
    ON_ERROR: Final[str] = "#FFFFFF"
    OUTLINE: Final[str] = "#CCCCCC"

# It generates a full, harmonious color scheme automatically.
LIGHT_THEME_SEED_COLOR: Final[str] = ft.Colors.BLUE_GREY_700

# --- Dark Theme Colors ---
# Define a clear palette for the dark theme using a class for organization.
# This structure makes it easy to see and modify the entire theme's color story.
class DarkThemeColors:
    PRIMARY: Final[str] = "#3498DB"          # Accent Blue
    ON_PRIMARY: Final[str] = "#FFFFFF"       # White Text on Primary
    BACKGROUND: Final[str] = "#1A1A1A"      # Primary Background
    ON_BACKGROUND: Final[str] = "#FFFFFF"    # White Text on Background
    SURFACE: Final[str] = "#1A1A1A"          # Component Backgrounds (e.g., Card)
    ON_SURFACE: Final[str] = "#FFFFFF"       # White Text on Surface
    SURFACE_VARIANT: Final[str] = "#2C2C2C"   # Secondary Background (e.g., Dialogs, Sidebar)
    ON_SURFACE_VARIANT: Final[str] = "#CCCCCC" # Grey Text on Variant
    SECONDARY: Final[str] = "#2ECC71"        # Accent Green
    ON_SECONDARY: Final[str] = "#FFFFFF"     # White Text on Secondary
    ERROR: Final[str] = "#E74C3C"            # Accent Red
    ON_ERROR: Final[str] = "#FFFFFF"         # White Text on Error
    OUTLINE: Final[str] = "#444444"          # Borders, Dividers

# ==============================================================================
# --- 3. TEXT THEME DEFINITIONS ---
# ==============================================================================

def _create_text_theme(primary_color: str) -> ft.TextTheme:
    """
    Factory function to create a TextTheme with a consistent font family.
    This reduces code duplication for light and dark themes.
    """
    return ft.TextTheme(
        headline_large=ft.TextStyle(font_family=FONT_FAMILY_JOSEFIN_SANS, weight=ft.FontWeight.BOLD, size=24, color=primary_color),
        headline_medium=ft.TextStyle(font_family=FONT_FAMILY_JOSEFIN_SANS, weight=ft.FontWeight.BOLD, size=20, color=primary_color),
        headline_small=ft.TextStyle(font_family=FONT_FAMILY_JOSEFIN_SANS, weight=ft.FontWeight.BOLD, size=18, color=primary_color),
        title_large=ft.TextStyle(font_family=FONT_FAMILY_JOSEFIN_SANS, weight=ft.FontWeight.BOLD, size=20, color=primary_color),
        title_medium=ft.TextStyle(font_family=FONT_FAMILY_JOSEFIN_SANS, weight=ft.FontWeight.BOLD, size=16, color=primary_color),
        title_small=ft.TextStyle(font_family=FONT_FAMILY_JOSEFIN_SANS, weight=ft.FontWeight.W_600, size=14, color=primary_color),
        body_large=ft.TextStyle(font_family=FONT_FAMILY_JOSEFIN_SANS, weight=ft.FontWeight.NORMAL, size=16, color=primary_color),
        body_medium=ft.TextStyle(font_family=FONT_FAMILY_JOSEFIN_SANS, weight=ft.FontWeight.NORMAL, size=14, color=primary_color),
        # Let label color be inherited by default, can be overridden if needed.
        label_medium=ft.TextStyle(font_family=FONT_FAMILY_JOSEFIN_SANS, weight=ft.FontWeight.NORMAL, size=12),
    )

# --- Light Text Theme ---
# Material 3 themes handle most text colors automatically based on the background.
# We only need to define the typography.
light_text_theme = _create_text_theme(primary_color=ft.Colors.BLACK)

# --- Dark Text Theme ---
# Create the base theme and then customize the specific secondary text color.
dark_text_theme = _create_text_theme(primary_color=DarkThemeColors.ON_BACKGROUND)
dark_text_theme.label_medium.color = DarkThemeColors.ON_SURFACE_VARIANT # Specific override for secondary text

# ==============================================================================
# --- 4. THEME OBJECTS ---
# ==============================================================================

# --- Light Theme ---
# Now uses an explicit color_scheme for full compatibility
light_theme = ft.Theme(
    color_scheme=ft.ColorScheme(
        primary=LightThemeColors.PRIMARY,
        on_primary=LightThemeColors.ON_PRIMARY,
        surface=LightThemeColors.SURFACE,
        on_surface=LightThemeColors.ON_SURFACE,
        on_surface_variant=LightThemeColors.ON_SURFACE_VARIANT,
        secondary=LightThemeColors.SECONDARY,
        on_secondary=LightThemeColors.ON_SECONDARY,
        error=LightThemeColors.ERROR,
        on_error=LightThemeColors.ON_ERROR,
        outline=LightThemeColors.OUTLINE,
    ),
    font_family=FONT_FAMILY_JOSEFIN_SANS,
    page_transitions=COMMON_PAGE_TRANSITIONS,
    text_theme=light_text_theme,
    use_material3=True,
)

# --- Dark Theme ---
# Constructed using the explicit color scheme defined in the DarkThemeColors class.
dark_theme = ft.Theme(
    color_scheme=ft.ColorScheme(
        primary=DarkThemeColors.PRIMARY,
        on_primary=DarkThemeColors.ON_PRIMARY,
        surface=DarkThemeColors.SURFACE,
        on_surface=DarkThemeColors.ON_SURFACE,
        on_surface_variant=DarkThemeColors.ON_SURFACE_VARIANT,
        secondary=DarkThemeColors.SECONDARY,
        on_secondary=DarkThemeColors.ON_SECONDARY,
        error=DarkThemeColors.ERROR,
        on_error=DarkThemeColors.ON_ERROR,
        outline=DarkThemeColors.OUTLINE,
    ),
    font_family=FONT_FAMILY_JOSEFIN_SANS,
    page_transitions=COMMON_PAGE_TRANSITIONS,
    text_theme=dark_text_theme,
    use_material3=True,
)


# ==============================================================================
# --- 5. PUBLIC API ---
# ==============================================================================

def get_app_themes() -> tuple[ft.Theme, ft.Theme]:
    """Returns the configured light and dark themes for the application."""
    return light_theme, dark_theme

def get_app_fonts() -> Dict[str, str]:
    """Returns the dictionary of fonts to be loaded by the app."""
    return APP_FONTS

# Alias for direct import, maintaining compatibility with existing code.
app_fonts = APP_FONTS
