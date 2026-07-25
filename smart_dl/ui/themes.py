"""CLI themes — color schemes for Rich console output."""

THEMES = {
    "default": {
        "name": "Default",
        "border": "cyan",
        "header": "bold magenta",
        "success": "bold green",
        "warning": "yellow",
        "error": "bold red",
        "info": "dim",
        "accent": "bold cyan",
        "bar_complete": "bold green",
        "bar_pulse": "cyan",
        "progress": "cyan",
    },
    "dracula": {
        "name": "Dracula",
        "border": "magenta",
        "header": "bold magenta",
        "success": "bold green",
        "warning": "yellow",
        "error": "bold red",
        "info": "dim",
        "accent": "bold pink",
        "bar_complete": "bold green",
        "bar_pulse": "magenta",
        "progress": "magenta",
    },
    "catppuccin": {
        "name": "Catppuccin Mocha",
        "border": "mauve",
        "header": "bold mauve",
        "success": "bold green",
        "warning": "yellow",
        "error": "bold red",
        "info": "dim",
        "accent": "bold lavender",
        "bar_complete": "bold green",
        "bar_pulse": "mauve",
        "progress": "mauve",
    },
    "one-dark": {
        "name": "One Dark Pro",
        "border": "blue",
        "header": "bold blue",
        "success": "bold green",
        "warning": "yellow",
        "error": "bold red",
        "info": "dim",
        "accent": "bold cyan",
        "bar_complete": "bold green",
        "bar_pulse": "blue",
        "progress": "blue",
    },
    "nord": {
        "name": "Nord",
        "border": "cyan",
        "header": "bold cyan",
        "success": "bold green",
        "warning": "yellow",
        "error": "bold red",
        "info": "dim",
        "accent": "bold blue",
        "bar_complete": "bold green",
        "bar_pulse": "cyan",
        "progress": "cyan",
    },
    "tokyonight": {
        "name": "Tokyo Night",
        "border": "blue",
        "header": "bold blue",
        "success": "bold green",
        "warning": "yellow",
        "error": "bold red",
        "info": "dim",
        "accent": "bold magenta",
        "bar_complete": "bold green",
        "bar_pulse": "blue",
        "progress": "blue",
    },
    "gruvbox": {
        "name": "Gruvbox",
        "border": "yellow",
        "header": "bold yellow",
        "success": "bold green",
        "warning": "yellow",
        "error": "bold red",
        "info": "dim",
        "accent": "bold orange",
        "bar_complete": "bold green",
        "bar_pulse": "yellow",
        "progress": "yellow",
    },
    "solarized": {
        "name": "Solarized",
        "border": "cyan",
        "header": "bold cyan",
        "success": "bold green",
        "warning": "yellow",
        "error": "bold red",
        "info": "dim",
        "accent": "bold blue",
        "bar_complete": "bold green",
        "bar_pulse": "cyan",
        "progress": "cyan",
    },
    "monokai": {
        "name": "Monokai",
        "border": "yellow",
        "header": "bold yellow",
        "success": "bold green",
        "warning": "yellow",
        "error": "bold red",
        "info": "dim",
        "accent": "bold magenta",
        "bar_complete": "bold green",
        "bar_pulse": "yellow",
        "progress": "yellow",
    },
    "eink": {
        "name": "E-Ink",
        "border": "white",
        "header": "bold white",
        "success": "bold white",
        "warning": "white",
        "error": "bold white",
        "info": "dim",
        "accent": "bold white",
        "bar_complete": "bold white",
        "bar_pulse": "white",
        "progress": "white",
    },
    "green-on-black": {
        "name": "Green on Black",
        "border": "green",
        "header": "bold green",
        "success": "bold green",
        "warning": "green",
        "error": "bold red",
        "info": "dim green",
        "accent": "bold green",
        "bar_complete": "bold green",
        "bar_pulse": "green",
        "progress": "green",
    },
    "persian": {
        "name": "Persian Green",
        "border": "green",
        "header": "bold green",
        "success": "bold green",
        "warning": "yellow",
        "error": "bold red",
        "info": "dim",
        "accent": "bold cyan",
        "bar_complete": "bold green",
        "bar_pulse": "green",
        "progress": "green",
    },
}


_current_theme = "default"


def set_theme(name: str):
    """Set the active theme."""
    global _current_theme
    if name in THEMES:
        _current_theme = name


def get_theme() -> dict:
    """Get the current theme."""
    return THEMES.get(_current_theme, THEMES["default"])


def get_theme_name() -> str:
    """Get the current theme name."""
    return _current_theme


def list_themes() -> list:
    """List all available themes."""
    return [(k, v["name"]) for k, v in THEMES.items()]


def apply_theme_to_style(style_key: str) -> str:
    """Get a style string from the current theme."""
    theme = get_theme()
    return theme.get(style_key, "white")
