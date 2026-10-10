"""
Formatting utilities for Telegram bot messages.

Converts AI-generated text and raw Markdown into clean, elegant,
mobile-friendly Telegram HTML with emojis and zero raw asterisks (* or **).
"""

from __future__ import annotations

import html
import re

# Number emoji map for clean lists
NUMBER_EMOJIS = {
    "1": "1️⃣",
    "2": "2️⃣",
    "3": "3️⃣",
    "4": "4️⃣",
    "5": "5️⃣",
    "6": "6️⃣",
    "7": "7️⃣",
    "8": "8️⃣",
    "9": "9️⃣",
    "10": "🔟",
}

# Known metadata field patterns and their clean emoji replacements
FIELD_REPLACEMENTS = [
    (r"Store(?:\s*Name)?:", "🏪 <b>Store:</b>"),
    (r"Deal(?:\s*Price)?:", "💰 <b>Deal:</b>"),
    (r"Price:", "💰 <b>Price:</b>"),
    (r"Qty(?:\s*Left|\s*Available)?:", "📦 <b>Qty:</b>"),
    (r"Quantity(?:\s*Left|\s*Available)?:", "📦 <b>Qty:</b>"),
    (r"Units(?:\s*Left|\s*Remaining)?:", "📦 <b>Units:</b>"),
    (r"Expiry(?:\s*Date)?:", "⏰ <b>Expiry:</b>"),
    (r"Pickup(?:\s*Window|\s*Hours)?:", "🕒 <b>Pickup:</b>"),
    (r"Action(?:\s*Plan)?:", "⚡ <b>Action:</b>"),
    (r"Category:", "🏷️ <b>Category:</b>"),
    (r"Batch(?:\s*Code)?:", "🔖 <b>Batch:</b>"),
    (r"Status:", "📌 <b>Status:</b>"),
    (r"Partner:", "🤝 <b>Partner:</b>"),
    (r"Address:", "📍 <b>Address:</b>"),
    (r"Hours:", "🕒 <b>Hours:</b>"),
    (r"Contact:", "📞 <b>Contact:</b>"),
]


def clean_telegram_text(text: str) -> str:
    """
    Transform raw markdown or AI output into clean Telegram HTML:
    - Replaces **1. Item** or 1. Item with 1️⃣ <b>Item</b>
    - Standardizes bullet fields (* **Store:** ...) with neat emojis
    - Converts **bold** to <b>bold</b>
    - Converts *italic* / _italic_ to <i>italic</i>
    - Converts `code` to <code>code</code>
    - Converts ~strikethrough~ to <s>strikethrough</s>
    - Strips ALL dangling asterisks (** or *) so no random stars appear
    - Normalizes line breaks for clean mobile reading
    """
    if not text:
        return ""

    # Normalize line endings
    s = text.replace("\r\n", "\n").replace("\r", "\n")

    # Replace markdown header hashtags: ### Title -> <b>Title</b>
    s = re.sub(r"^[ \t]*#{1,6}[ \t]+(.+)$", r"<b>\1</b>", s, flags=re.MULTILINE)

    # Standardize numbered list headers: **1. Product Name** -> 1️⃣ <b>Product Name</b>
    def _replace_num_header(match: re.Match) -> str:
        num = match.group(1)
        title = match.group(2).strip().rstrip(":")
        title = re.sub(r"^\*+|\*+$", "", title).strip()
        badge = NUMBER_EMOJIS.get(num, f"{num}.")
        return f"\n{badge} <b>{title}</b>"

    s = re.sub(
        r"(?:^|\n)\s*(?:\*\*)?(\d{1,2})\.\s*(.*?)(?:\*\*)?(?=\n|$)",
        _replace_num_header,
        s,
    )

    # Standardize known metadata fields
    for pattern, repl in FIELD_REPLACEMENTS:
        s = re.sub(
            rf"^[ \t]*[\*\-•]?[ \t]*(?:\*\*)?{pattern}(?:\*\*)?[ \t]*",
            f"{repl} ",
            s,
            flags=re.MULTILINE | re.IGNORECASE,
        )

    # Convert strikethrough ~text~ -> <s>text</s>
    s = re.sub(r"~([^~\n]+)~", r"<s>\1</s>", s)

    # Convert **bold** -> <b>bold</b>
    s = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s)

    # Convert backticks `code` -> <code>code</code>
    s = re.sub(r"`([^`\n]+)`", r"<code>\1</code>", s)

    # Convert bullets (* or -) at start of lines into clean dot bullets
    s = re.sub(r"^[ \t]*[\*\-][ \t]+", "• ", s, flags=re.MULTILINE)

    # Convert remaining single asterisks or underscores: *word* / _word_ -> <i>word</i>
    s = re.sub(r"(?<!\w)\*([^\*\n]+?)\*(?!\w)", r"<i>\1</i>", s)
    s = re.sub(r"(?<!\w)_([^_\n]+?)_(?!\w)", r"<i>\1</i>", s)

    # Strip any remaining dangling asterisks (never leave random stars in UI)
    s = s.replace("**", "").replace("*", "")

    # Sanitize brackets like [DEMO] without URLs
    s = s.replace("[DEMO]", "(DEMO)").replace("[demo]", "(demo)")

    # Clean up empty tags and normalize spacing
    s = re.sub(r"<[bi]>(\s*)</[bi]>", r"\1", s)
    s = re.sub(r"\n{3,}", "\n\n", s)

    return s.strip()


def strip_all_tags(text: str) -> str:
    """Strip all HTML and markdown markers for foolproof plain-text fallback."""
    if not text:
        return ""
    # Strip HTML tags
    s = re.sub(r"<[^>]+>", "", text)
    # Strip markdown markers
    s = s.replace("**", "").replace("*", "").replace("`", "").replace("~", "")
    return s.strip()
