"""Inline keyboard buttons for the Telegram bot."""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_main_menu() -> InlineKeyboardMarkup:
    """Get the main menu inline keyboard."""
    keyboard = [
        [
            InlineKeyboardButton(text="🏥 Health", callback_data="cmd_health"),
            InlineKeyboardButton(text="📚 Labs", callback_data="cmd_labs"),
        ],
        [
            InlineKeyboardButton(text="📊 Scores", callback_data="cmd_scores"),
            InlineKeyboardButton(text="❓ Help", callback_data="cmd_help"),
        ],
        [
            InlineKeyboardButton(text="🔄 Sync Data", callback_data="cmd_sync"),
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_lab_scores_keyboard(labs: list) -> InlineKeyboardMarkup:
    """Get inline keyboard with lab buttons for scores."""
    keyboard = []
    row = []
    for lab in labs[:6]:  # Show first 6 labs
        lab_id = lab.get("id", "?")
        row.append(
            InlineKeyboardButton(
                text=f"Lab {lab_id}",
                callback_data=f"scores_{lab_id}"
            )
        )
        if len(row) == 2:  # 2 buttons per row
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    return InlineKeyboardMarkup(inline_keyboard=keyboard)
