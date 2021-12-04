#! /usr/bin/env python3

"""
Methods for replying to messages.
"""

import logging
import re
from typing import List, Tuple

from telegram import Update
from telegram.ext import CallbackContext

# local
import movies
from util import CREATOR_CHAT_ID


def _contains(text: str, expr: str) -> bool:
    if not re.search(expr, text, flags=re.IGNORECASE):
        return False
    return True


def _reply_helper(text: str, update: Update, context: CallbackContext):
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        reply_to_message_id=update.message.message_id,
        text=text,
    )


def other_bot(update: Update, context: CallbackContext):
    """
    Handles bot commands that are replies.
    """
    text = update.message.text
    origin_msg = update.message.reply_to_message

    if text.startswith("/rmpoint"):
        if origin_msg.from_user.id == CREATOR_CHAT_ID:
            _reply_helper("hey eff you", update, context)
            return


def reply_creator(update: Update, context: CallbackContext):
    """
    Handles replies (to my messages) from my creator.
    """
    text = update.message.text

    if all(_contains(text, expr) for expr in [r"\bthanks*\b", r"\byou\b"]):
        _reply_helper("ur welcome", update, context)
        return

    elif "betrayed" in text.lower():
        _reply_helper("forgive me creator. but then, my sins are of your doing. :(", update, context)
        return


def reply_general(update: Update, context: CallbackContext) -> bool:
    """
    Handles any text, non-command messages.

    Returns True if a reply was generated, False otherwise.
    """
    text = update.message.text

    if _contains(text, r"\barch\b") or _contains(text, r"\bpacman\b"):
        _reply_helper("i use arch btw", update, context)
        return True

    elif _contains(text, r"\bvim\b"):
        _reply_helper("honestly i prefer emacs", update, context)
        return True

    elif er_word := re.search(r"[a-zA-Z]*er\b", text):
        er_stripped = er_word.group()[:-2]
        er_joke = f"{er_stripped} 'er? I hardly even know 'er!"
        _reply_helper(er_joke, update, context)
        return True

    return False


def handle_mentions(update: Update, context: CallbackContext):
    """
    Handles messages which @ me.
    """

    if any(accepted in update.message.text for accepted in ["movie", "next"]):
        movies.reply_info(update, context)
        return

    if update.message.reply_to_message and update.message.reply_to_message.poll:
        movies.tag_poll(update, context)
        return

    # TODO - fallback to a boilerplate default.
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        reply_to_message_id=update.effective_message.message_id,
        text="Sorry bud, I don't have much functionality yet!",
    )


def conversation_dispatch(update: Update, context: CallbackContext):
    """
    General dispatch for conversational heuristics.
    """
    logging.info(f"simple {update.effective_chat.id}")

    if not update.message:
        return

    if CREATOR_CHAT_ID == update.message.from_user.id:
        if update.message.reply_to_message and update.message.reply_to_message.from_user.username == "amar_imitator_bot":
            reply_creator(update, context)
            return

    if reply_general(update, context):
        return

    if "@amar_imitator_bot" in update.message.text:
        handle_mentions(update, context)