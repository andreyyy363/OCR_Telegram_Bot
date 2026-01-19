"""
Helper utility functions for the OCR Telegram Bot.
"""
import os
import re


def sanitize_filename(filename: str) -> str:
    """
    Sanitize a filename to prevent path traversal and remove unsafe characters.

    Preserves the original extension but strips any directory components and
    replaces disallowed characters in the basename with underscores.

    :param filename: The original filename
    :return: Sanitized filename safe for filesystem use
    """
    # Normalize separators and drop any directory components
    safe = filename.replace("\\", "/").split("/")[-1].strip()

    # Split into basename and extension to preserve the original extension
    base, ext = os.path.splitext(safe)

    # Avoid hidden files and trim whitespace
    base = base.lstrip('.').strip()

    # Allow alphanumerics, space, dot, dash and underscore; replace others
    base = re.sub(r"[^A-Za-z0-9._ -]", "_", base)

    # Collapse consecutive spaces/underscores to a single underscore
    base = re.sub(r"[ _]+", "_", base).strip("_")

    # Ensure non-empty basename
    if not base:
        base = "file"

    # Limit basename length to avoid excessively long filenames
    if len(base) > 100:
        base = base[:100]

    return f"{base}{ext}"
