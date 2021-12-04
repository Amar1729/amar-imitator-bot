#! /usr/bin/env python3

"""
about - short info for this bot
upcoming - show next person for movie club dictator
next - iterate through movie club members
members - show all movie club members
"""

import datetime
import logging

from telegram import Update
from telegram.ext import Updater, CallbackContext, CommandHandler, MessageHandler, Filters

# local
import movies
from util import TOKEN, CREATOR_CHAT_ID, GROUP_CHAT_ID, TZ


logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)


def about(update: Update, context: CallbackContext):
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="\n".join([
            "I replicate my creator in one of his primary chats.",
            "Check out my page!",
            "https://github.com/Amar1729",
        ]))


def simple_reply(update: Update, context: CallbackContext):
    if "@amar_imitator_bot" not in update.message.text:
        return

    if any(accepted in update.message.text for accepted in ["movie", "next"]):
        movies.reply_info(update, context)
        return

    if update.message.reply_to_message and update.message.reply_to_message.poll:
        movies.tag_poll(update, context)
        return

    context.bot.send_message(
        chat_id=update.effective_chat.id,
        reply_to_message_id=update.effective_message.message_id,
        text="Sorry bud, I don't have much functionality yet!",
    )


def echo(update: Update, context: CallbackContext):
    logging.info(update.effective_user.username)
    # logging.info(dir(update.effective_chat))
    logging.info(update.effective_user)
    context.bot.send_message(chat_id=update.effective_chat.id, text=update.message.text)


if __name__ == "__main__":
    updater = Updater(token=TOKEN)
    dispatcher = updater.dispatcher

    jobq = updater.job_queue
    jobq.run_daily(movies.movie_reminder, time=datetime.time(hour=19, tzinfo=TZ), days=(3,))

    about_handler = CommandHandler("about", about)
    dispatcher.add_handler(about_handler)

    current_handler = CommandHandler("upcoming", movies.movie_upcoming)
    dispatcher.add_handler(current_handler)

    movie_next_handler = CommandHandler("next", movies.movie_next)
    dispatcher.add_handler(movie_next_handler)

    movie_members_handler = CommandHandler("members", movies.movie_members)
    dispatcher.add_handler(movie_members_handler)

    chat_allowlist = Filters.chat(GROUP_CHAT_ID) & Filters.chat(CREATOR_CHAT_ID)

    simple_handler = MessageHandler(chat_allowlist & Filters.text & (~Filters.command), simple_reply)
    dispatcher.add_handler(simple_handler)

    echo_handler = MessageHandler(Filters.chat(CREATOR_CHAT_ID) & Filters.text & (~Filters.command), echo)
    dispatcher.add_handler(echo_handler)

    updater.start_polling()
    updater.idle()
