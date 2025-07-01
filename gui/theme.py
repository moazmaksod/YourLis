import flet as ft

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

# --- Light Text Theme ---
# Using ft.Colors.CONSTANT_NAME as per user's working version and error message corrections
light_text_color = ft.Colors.BLACK
light_text_theme = ft.TextTheme(
    headline_large=ft.TextStyle(font_family=FONT_FAMILY_JOSEFIN_SANS, weight=ft.FontWeight.BOLD, size=24, color=light_text_color),
    headline_medium=ft.TextStyle(font_family=FONT_FAMILY_JOSEFIN_SANS, weight=ft.FontWeight.BOLD, size=20, color=light_text_color),
    headline_small=ft.TextStyle(font_family=FONT_FAMILY_JOSEFIN_SANS, weight=ft.FontWeight.BOLD, size=18, color=light_text_color),
    title_large=ft.TextStyle(font_family=FONT_FAMILY_JOSEFIN_SANS, weight=ft.FontWeight.BOLD, size=20, color=light_text_color),
    title_medium=ft.TextStyle(font_family=FONT_FAMILY_JOSEFIN_SANS, weight=ft.FontWeight.BOLD, size=16, color=light_text_color),
    title_small=ft.TextStyle(font_family=FONT_FAMILY_JOSEFIN_SANS, weight=ft.FontWeight.W_600, size=14, color=light_text_color),
    body_large=ft.TextStyle(font_family=FONT_FAMILY_JOSEFIN_SANS, weight=ft.FontWeight.NORMAL, size=16, color=light_text_color),
    body_medium=ft.TextStyle(font_family=FONT_FAMILY_JOSEFIN_SANS, weight=ft.FontWeight.NORMAL, size=14, color=light_text_color),
    label_medium=ft.TextStyle(font_family=FONT_FAMILY_JOSEFIN_SANS, weight=ft.FontWeight.NORMAL, size=12, color=light_text_color),
)

# --- Dark Text Theme ---
dark_text_color = ft.Colors.WHITE
dark_text_theme = ft.TextTheme(
    headline_large=ft.TextStyle(font_family=FONT_FAMILY_JOSEFIN_SANS, weight=ft.FontWeight.BOLD, size=24, color=dark_text_color),
    headline_medium=ft.TextStyle(font_family=FONT_FAMILY_JOSEFIN_SANS, weight=ft.FontWeight.BOLD, size=20, color=dark_text_color),
    headline_small=ft.TextStyle(font_family=FONT_FAMILY_JOSEFIN_SANS, weight=ft.FontWeight.BOLD, size=18, color=dark_text_color),
    title_large=ft.TextStyle(font_family=FONT_FAMILY_JOSEFIN_SANS, weight=ft.FontWeight.BOLD, size=20, color=dark_text_color),
    title_medium=ft.TextStyle(font_family=FONT_FAMILY_JOSEFIN_SANS, weight=ft.FontWeight.BOLD, size=16, color=dark_text_color),
    title_small=ft.TextStyle(font_family=FONT_FAMILY_JOSEFIN_SANS, weight=ft.FontWeight.W_600, size=14, color=dark_text_color),
    body_large=ft.TextStyle(font_family=FONT_FAMILY_JOSEFIN_SANS, weight=ft.FontWeight.NORMAL, size=16, color=dark_text_color),
    body_medium=ft.TextStyle(font_family=FONT_FAMILY_JOSEFIN_SANS, weight=ft.FontWeight.NORMAL, size=14, color=dark_text_color),
    label_medium=ft.TextStyle(font_family=FONT_FAMILY_JOSEFIN_SANS, weight=ft.FontWeight.NORMAL, size=12, color=dark_text_color),
)

# --- Light Theme (Simplified) ---
light_theme = ft.Theme(
    color_scheme_seed=ft.Colors.BLUE_GREY, # A neutral seed
    font_family=FONT_FAMILY_JOSEFIN_SANS,
    page_transitions=common_page_transitions,
    text_theme=light_text_theme, # Explicitly black text for light mode
    use_material3=True,
    # No component-specific themes like elevated_button_theme, input_decoration_theme, etc.
)

# --- Dark Theme (Simplified) ---
# For dark theme, we want specific background from user spec: #1A1A1A
# and primary accent: #3498DB
# ColorScheme is the best place for this.
dark_theme_color_scheme = ft.ColorScheme(
    brightness=ft.Brightness.DARK, # Ensures it's a dark scheme
    primary=ft.Color(APP_COLORS_DARK["accent_blue"] if "APP_COLORS_DARK" in locals() else "#3498DB"), # Main accent
    on_primary=ft.Colors.WHITE, # Text on primary accent
    surface=ft.Color(APP_COLORS_DARK["primary_background"] if "APP_COLORS_DARK" in locals() else "#1A1A1A"), # Main background
    on_surface=ft.Colors.WHITE, # Main text color
    background=ft.Color(APP_COLORS_DARK["primary_background"] if "APP_COLORS_DARK" in locals() else "#1A1A1A"), # Also main background
    on_background=ft.Colors.WHITE, # Main text color
    error=ft.Color(APP_COLORS_DARK["accent_red"] if "APP_COLORS_DARK" in locals() else "#E74C3C"),
    on_error=ft.Colors.WHITE,
    secondary=ft.Color(APP_COLORS_DARK["accent_green"] if "APP_COLORS_DARK" in locals() else "#2ECC71"), # Example secondary
    on_secondary=ft.Colors.WHITE,
    surface_variant=ft.Color(APP_COLORS_DARK["secondary_background"] if "APP_COLORS_DARK" in locals() else "#2C2C2C"), # For cards
    on_surface_variant=ft.Color(APP_COLORS_DARK["text_secondary"] if "APP_COLORS_DARK" in locals() else "#CCCCCC"),
    outline=ft.Color(APP_COLORS_DARK["divider_border"] if "APP_COLORS_DARK" in locals() else "#444444"),
)

dark_theme = ft.Theme(
    color_scheme=dark_theme_color_scheme, # Use the more specific ColorScheme
    font_family=FONT_FAMILY_JOSEFIN_SANS,
    page_transitions=common_page_transitions,
    text_theme=dark_text_theme, # Explicitly white text for dark mode
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

# Fallback global theme settings
ft.theme = ft.Theme(use_material3=True)

# Minimal APP_COLORS_DARK for direct reference if needed by ColorScheme above
# This is a bit of a workaround to avoid NameError if this script is imported before full APP_COLORS_DARK is defined elsewhere
# or if this script is meant to be self-contained for basic theme colors.
if "APP_COLORS_DARK" not in locals():
    APP_COLORS_DARK = {
        "accent_blue": "#3498DB",
        "primary_background": "#1A1A1A",
        "accent_red": "#E74C3C",
        "accent_green": "#2ECC71",
        "secondary_background": "#2C2C2C",
        "text_secondary": "#CCCCCC",
        "divider_border": "#444444",
    }

if __name__ == "__main__":
    print(f"Dark theme primary color: {dark_theme.color_scheme.primary}") #type: ignore
    print(f"Dark theme surface color: {dark_theme.color_scheme.surface}") #type: ignore
    print(f"Light theme primary color from seed: {light_theme.color_scheme_seed}") #type: ignore
```
