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
from telegram.ext import ConversationHandler, CallbackQueryHandler

# local
import movies
import conversation
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


if __name__ == "__main__":
    logging.info(f"Allowing messages from: [{CREATOR_CHAT_ID}, {GROUP_CHAT_ID}]")

    updater = Updater(token=TOKEN)
    dispatcher = updater.dispatcher

    jobq = updater.job_queue
    jobq.run_daily(movies.movie_reminder, time=datetime.time(hour=19, tzinfo=TZ), days=(3,))
    jobq.run_daily(movies.next, time=datetime.time(hour=20, tzinfo=TZ), days=(6,))

    about_handler = CommandHandler("about", about)
    dispatcher.add_handler(about_handler)

    current_handler = CommandHandler("upcoming", movies.movie_upcoming)
    dispatcher.add_handler(current_handler)

    movie_next_handler = CommandHandler("next", movies.movie_next)
    dispatcher.add_handler(movie_next_handler)

    movie_members_handler = CommandHandler("members", movies.movie_members)
    dispatcher.add_handler(movie_members_handler)

    poll_handler = ConversationHandler(
        entry_points=[MessageHandler(Filters.chat(GROUP_CHAT_ID) & Filters.poll, movies.poll_query)],
        states={
            0: [
                CallbackQueryHandler(movies.callback_poll_tag, pattern="^1$"),
                CallbackQueryHandler(movies.callback_poll_no, pattern="^0$"),
            ],
        },
        fallbacks=[],
    )

    dispatcher.add_handler(poll_handler)

    chat_allowlist = Filters.chat(GROUP_CHAT_ID) | Filters.chat(CREATOR_CHAT_ID)

    msg_handler = MessageHandler(chat_allowlist & Filters.text & (~Filters.command), conversation.conversation_dispatch)
    dispatcher.add_handler(msg_handler)

    other_bot_handler = MessageHandler(chat_allowlist & Filters.text & Filters.reply, conversation.other_bot)
    dispatcher.add_handler(other_bot_handler)

    updater.start_polling()
    updater.idle()
