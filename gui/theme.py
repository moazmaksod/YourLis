import flet as ft

# --- User-Specified Dark Colors ---
# Storing raw hex strings and direct ft.Colors objects as per user specification.
# These will be used to construct the dark_theme_color_scheme and dark_text_theme.
USER_SPEC_DARK_COLORS = {
    "primary_background_hex": "#1A1A1A",
    "secondary_background_hex": "#2C2C2C",
    "sidebar_background_hex": "#222222", # Note: sidebar bg needs explicit component styling
    "accent_blue_hex": "#3498DB",
    "accent_yellow_hex": "#F39C12", # For reference
    "accent_red_hex": "#E74C3C",
    "accent_green_hex": "#2ECC71",
    "text_primary_obj": ft.Colors.WHITE,
    "text_secondary_hex": "#CCCCCC",
    "divider_border_hex": "#444444",
    # Gradients for reference, not used directly in ColorScheme/TextTheme
    "gradient_blue_teal_start_hex": "#00CED1",
    "gradient_blue_teal_end_hex": "#1ABC9C",
    "gradient_blue_purple_start_hex": "#3498DB",
    "gradient_blue_purple_end_hex": "#8E44AD",
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

# --- Light Text Theme ---
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
dark_text_theme = ft.TextTheme(
    headline_large=ft.TextStyle(font_family=FONT_FAMILY_JOSEFIN_SANS, weight=ft.FontWeight.BOLD, size=24, color=USER_SPEC_DARK_COLORS["text_primary_obj"]),
    headline_medium=ft.TextStyle(font_family=FONT_FAMILY_JOSEFIN_SANS, weight=ft.FontWeight.BOLD, size=20, color=USER_SPEC_DARK_COLORS["text_primary_obj"]),
    headline_small=ft.TextStyle(font_family=FONT_FAMILY_JOSEFIN_SANS, weight=ft.FontWeight.BOLD, size=18, color=USER_SPEC_DARK_COLORS["text_primary_obj"]),
    title_large=ft.TextStyle(font_family=FONT_FAMILY_JOSEFIN_SANS, weight=ft.FontWeight.BOLD, size=20, color=USER_SPEC_DARK_COLORS["text_primary_obj"]),
    title_medium=ft.TextStyle(font_family=FONT_FAMILY_JOSEFIN_SANS, weight=ft.FontWeight.BOLD, size=16, color=USER_SPEC_DARK_COLORS["text_primary_obj"]),
    title_small=ft.TextStyle(font_family=FONT_FAMILY_JOSEFIN_SANS, weight=ft.FontWeight.W_600, size=14, color=USER_SPEC_DARK_COLORS["text_primary_obj"]),
    body_large=ft.TextStyle(font_family=FONT_FAMILY_JOSEFIN_SANS, weight=ft.FontWeight.NORMAL, size=16, color=USER_SPEC_DARK_COLORS["text_primary_obj"]),
    body_medium=ft.TextStyle(font_family=FONT_FAMILY_JOSEFIN_SANS, weight=ft.FontWeight.NORMAL, size=14, color=USER_SPEC_DARK_COLORS["text_primary_obj"]),
    label_medium=ft.TextStyle(font_family=FONT_FAMILY_JOSEFIN_SANS, weight=ft.FontWeight.NORMAL, size=12, color=USER_SPEC_DARK_COLORS["text_secondary_hex"]), # Flet will parse this hex string
)

# --- Light Theme (Simplified) ---
light_theme = ft.Theme(
    color_scheme_seed=ft.Colors.BLUE_GREY,
    font_family=FONT_FAMILY_JOSEFIN_SANS,
    page_transitions=common_page_transitions,
    text_theme=light_text_theme,
    use_material3=True,
)

# --- Dark Theme (Using user-specified colors) ---
dark_theme_color_scheme = ft.ColorScheme(
    brightness=ft.Brightness.DARK,
    primary=ft.Color(USER_SPEC_DARK_COLORS["accent_blue_hex"]),
    on_primary=USER_SPEC_DARK_COLORS["text_primary_obj"], # Should be ft.Colors.WHITE
    surface=ft.Color(USER_SPEC_DARK_COLORS["primary_background_hex"]),
    on_surface=USER_SPEC_DARK_COLORS["text_primary_obj"], # Should be ft.Colors.WHITE
    background=ft.Color(USER_SPEC_DARK_COLORS["primary_background_hex"]),
    on_background=USER_SPEC_DARK_COLORS["text_primary_obj"], # Should be ft.Colors.WHITE
    error=ft.Color(USER_SPEC_DARK_COLORS["accent_red_hex"]),
    on_error=USER_SPEC_DARK_COLORS["text_primary_obj"], # Assuming white text on error color
    secondary=ft.Color(USER_SPEC_DARK_COLORS["accent_green_hex"]),
    on_secondary=USER_SPEC_DARK_COLORS["text_primary_obj"], # Assuming white text on secondary
    surface_variant=ft.Color(USER_SPEC_DARK_COLORS["secondary_background_hex"]),
    on_surface_variant=USER_SPEC_DARK_COLORS["text_secondary_hex"], # Flet will parse this hex string
    outline=ft.Color(USER_SPEC_DARK_COLORS["divider_border_hex"]),
)

dark_theme = ft.Theme(
    color_scheme=dark_theme_color_scheme,
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

ft.theme = ft.Theme(use_material3=True)

if __name__ == "__main__":
    print(f"Dark theme primary color: {dark_theme.color_scheme.primary}") #type: ignore
    print(f"Dark theme surface color: {dark_theme.color_scheme.surface}") #type: ignore
    print(f"Dark text theme label_medium color: {dark_text_theme.label_medium.color}") #type: ignore
    print(f"Light theme primary color from seed: {light_theme.color_scheme_seed}") #type: ignore
```
