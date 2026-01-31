"""
Centralized Theme Configuration for Catalyst-Meraki Migration Tool

Provides Cisco-inspired professional styling for the entire application.
"""

from tkinter import ttk


class Colors:
    """Color palette - Cisco-inspired professional theme."""

    # Primary Brand Colors
    PRIMARY = "#049FD9"        # Cisco Teal
    PRIMARY_HOVER = "#037DAF"  # Darker teal for hover
    PRIMARY_ACTIVE = "#026890" # Even darker for active/pressed
    SECONDARY = "#1E4471"      # Navy for headers

    # Backgrounds
    BG_MAIN = "#F8F9FA"        # Clean white-gray background
    BG_CARD = "#FFFFFF"        # Pure white for cards/inputs
    BG_INPUT = "#FFFFFF"       # White input fields
    BORDER = "#DEE2E6"         # Subtle borders

    # Text
    TEXT_PRIMARY = "#1A202C"   # Dark text for readability
    TEXT_SECONDARY = "#6B7280" # Muted secondary text
    TEXT_BUTTON = "#FFFFFF"    # White text on buttons

    # Semantic (Status Indicators)
    SUCCESS = "#10B981"        # Modern green
    SUCCESS_BG = "#D1FAE5"     # Light green background
    WARNING = "#F59E0B"        # Orange for warnings
    WARNING_BG = "#FEF3C7"     # Light orange background
    ERROR = "#EF4444"          # Red for errors/mismatches
    ERROR_BG = "#FEE2E2"       # Light red background


class Fonts:
    """Font definitions for consistent typography."""

    FAMILY = "Segoe UI"        # Windows professional font
    FAMILY_FALLBACK = "Arial"

    SIZE_SMALL = 9
    SIZE_NORMAL = 10
    SIZE_LARGE = 12
    SIZE_HEADER = 14

    # Pre-built font tuples
    NORMAL = (FAMILY, SIZE_NORMAL)
    BOLD = (FAMILY, SIZE_NORMAL, "bold")
    HEADER = (FAMILY, SIZE_HEADER, "bold")
    LARGE = (FAMILY, SIZE_LARGE)
    LARGE_BOLD = (FAMILY, SIZE_LARGE, "bold")
    SMALL = (FAMILY, SIZE_SMALL)
    ITALIC = (FAMILY, SIZE_SMALL, "italic")


class Spacing:
    """Consistent spacing scale."""

    XS = 2
    SM = 5
    MD = 10
    LG = 15
    XL = 20


def apply_theme(root):
    """
    Apply the Cisco-inspired theme to the application.

    Args:
        root: The Tk root window

    Returns:
        ttk.Style: The configured style object
    """
    style = ttk.Style()

    # Use clam theme as base (cleaner than default)
    style.theme_use('clam')

    # Configure base frame
    style.configure("TFrame", background=Colors.BG_MAIN)

    # Configure labels
    style.configure("TLabel",
                    background=Colors.BG_MAIN,
                    foreground=Colors.TEXT_PRIMARY,
                    font=Fonts.NORMAL)

    # Header labels
    style.configure("Header.TLabel",
                    font=Fonts.HEADER,
                    foreground=Colors.SECONDARY,
                    background=Colors.BG_MAIN)

    # Subheader labels
    style.configure("Subheader.TLabel",
                    font=Fonts.BOLD,
                    foreground=Colors.TEXT_PRIMARY,
                    background=Colors.BG_MAIN)

    # Secondary/muted labels
    style.configure("Secondary.TLabel",
                    font=Fonts.SMALL,
                    foreground=Colors.TEXT_SECONDARY,
                    background=Colors.BG_MAIN)

    # LabelFrames (card-like containers)
    style.configure("TLabelframe",
                    background=Colors.BG_CARD,
                    foreground=Colors.TEXT_PRIMARY,
                    bordercolor=Colors.BORDER,
                    relief="solid",
                    borderwidth=1)
    style.configure("TLabelframe.Label",
                    background=Colors.BG_CARD,
                    foreground=Colors.SECONDARY,
                    font=Fonts.BOLD)

    # Card frame (white background)
    style.configure("Card.TFrame",
                    background=Colors.BG_CARD)
    style.configure("Card.TLabel",
                    background=Colors.BG_CARD,
                    foreground=Colors.TEXT_PRIMARY,
                    font=Fonts.NORMAL)

    # Primary buttons (teal)
    style.configure("Primary.TButton",
                    font=Fonts.BOLD,
                    padding=(Spacing.MD, Spacing.SM),
                    background=Colors.PRIMARY,
                    foreground=Colors.TEXT_BUTTON)
    style.map("Primary.TButton",
              background=[("active", Colors.PRIMARY_HOVER),
                         ("pressed", Colors.PRIMARY_ACTIVE),
                         ("!disabled", Colors.PRIMARY)],
              foreground=[("!disabled", Colors.TEXT_BUTTON)])

    # Secondary buttons (default style but consistent)
    style.configure("Secondary.TButton",
                    font=Fonts.NORMAL,
                    padding=(Spacing.SM, Spacing.XS))

    # Entry fields
    style.configure("TEntry",
                    fieldbackground=Colors.BG_INPUT,
                    foreground=Colors.TEXT_PRIMARY,
                    padding=Spacing.SM,
                    bordercolor=Colors.BORDER)
    style.map("TEntry",
              bordercolor=[("focus", Colors.PRIMARY)])

    # Combobox
    style.configure("TCombobox",
                    fieldbackground=Colors.BG_INPUT,
                    foreground=Colors.TEXT_PRIMARY,
                    padding=Spacing.SM,
                    bordercolor=Colors.BORDER)

    # Notebook (tabs)
    style.configure("TNotebook",
                    background=Colors.BG_MAIN,
                    bordercolor=Colors.BORDER)
    style.configure("TNotebook.Tab",
                    font=Fonts.NORMAL,
                    padding=(Spacing.MD, Spacing.SM),
                    background=Colors.BG_MAIN,
                    foreground=Colors.TEXT_SECONDARY)
    style.map("TNotebook.Tab",
              background=[("selected", Colors.BG_CARD)],
              foreground=[("selected", Colors.PRIMARY)],
              expand=[("selected", [1, 1, 1, 0])])

    # Treeview
    style.configure("Treeview",
                    font=Fonts.NORMAL,
                    rowheight=28,
                    background=Colors.BG_CARD,
                    fieldbackground=Colors.BG_CARD,
                    foreground=Colors.TEXT_PRIMARY,
                    bordercolor=Colors.BORDER)
    style.configure("Treeview.Heading",
                    font=Fonts.BOLD,
                    background=Colors.SECONDARY,
                    foreground=Colors.TEXT_BUTTON,
                    padding=(Spacing.SM, Spacing.XS))
    style.map("Treeview.Heading",
              background=[("active", Colors.PRIMARY_HOVER)])
    style.map("Treeview",
              background=[("selected", Colors.PRIMARY)],
              foreground=[("selected", Colors.TEXT_BUTTON)])

    # Radiobuttons
    style.configure("TRadiobutton",
                    background=Colors.BG_MAIN,
                    foreground=Colors.TEXT_PRIMARY,
                    font=Fonts.NORMAL)
    style.configure("Card.TRadiobutton",
                    background=Colors.BG_CARD,
                    foreground=Colors.TEXT_PRIMARY,
                    font=Fonts.NORMAL)

    # Checkbuttons
    style.configure("TCheckbutton",
                    background=Colors.BG_MAIN,
                    foreground=Colors.TEXT_PRIMARY,
                    font=Fonts.NORMAL)

    # PanedWindow
    style.configure("TPanedwindow",
                    background=Colors.BG_MAIN)

    # Scrollbar
    style.configure("TScrollbar",
                    background=Colors.BG_MAIN,
                    troughcolor=Colors.BG_CARD,
                    bordercolor=Colors.BORDER,
                    arrowcolor=Colors.TEXT_SECONDARY)

    # Progressbar
    style.configure("TProgressbar",
                    background=Colors.PRIMARY,
                    troughcolor=Colors.BG_CARD,
                    bordercolor=Colors.BORDER)

    return style


def configure_treeview_tags(treeview):
    """
    Configure standard status tags for a Treeview widget.

    Args:
        treeview: The ttk.Treeview widget to configure
    """
    treeview.tag_configure('match', background=Colors.SUCCESS_BG)
    treeview.tag_configure('mismatch', background=Colors.ERROR_BG)
    treeview.tag_configure('not_found', background=Colors.WARNING_BG)
    treeview.tag_configure('warning', background=Colors.WARNING_BG)
