"""
Handlers package for OCR Telegram Bot.
"""
from .start import start, handle_interface_language_choice
from .menu import handle_menu_navigation, handle_info
from .files import handle_files
from .delivery import handle_text_delivery_choice

__all__ = [
    'start',
    'handle_interface_language_choice',
    'handle_menu_navigation',
    'handle_info',
    'handle_files',
    'handle_text_delivery_choice',
]
