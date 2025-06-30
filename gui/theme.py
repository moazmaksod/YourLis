import flet as ft

# Define font paths
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

# Light Theme
light_theme = ft.Theme(
    color_scheme=ft.ColorScheme(
        on_surface=light_text_color, # Still useful for other elements that might use on_surface
    ),
    color_scheme_seed=ft.Colors.BLUE_GREY,
    font_family=FONT_FAMILY_JOSEFIN_SANS, # Default font family for controls not using TextTheme
    page_transitions=common_page_transitions,
    text_theme=light_text_theme, # Assign specific light text theme
    use_material3=True,
)

# Dark Theme
dark_theme = ft.Theme(
    color_scheme=ft.ColorScheme(
        on_surface=dark_text_color, # Still useful
    ),
    color_scheme_seed=ft.Colors.BLUE_GREY,
    font_family=FONT_FAMILY_JOSEFIN_SANS, # Default font family
    page_transitions=common_page_transitions,
    text_theme=dark_text_theme, # Assign specific dark text theme
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

# Ensure Flet uses Material 3 design system by default for any implicit theme use
# This line might be redundant if page.theme is always set, but harmless.
ft.theme = ft.Theme(use_material3=True)

if __name__ == "__main__":
    # Example of how to print theme details (for debugging)
    print("Light Theme Color Scheme:", light_theme.color_scheme)
    print("Light Theme Text Theme Body Medium Color:", light_theme.text_theme.body_medium.color) #type: ignore
    print("Dark Theme Color Scheme:", dark_theme.color_scheme)
    print("Dark Theme Text Theme Body Medium Color:", dark_theme.text_theme.body_medium.color) #type: ignore
    print("App Fonts:", app_fonts)
