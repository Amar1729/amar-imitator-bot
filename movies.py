#! /usr/bin/env python3

import logging
import datetime
from typing import List, Tuple

from telegram import error, Update, Poll
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CallbackContext, CommandHandler, MessageHandler, Filters
from telegram.ext import ConversationHandler

# local
from util import CREATOR_CHAT_ID, GROUP_CHAT_ID
from data import Movies


with open("movie_club.txt") as f:
    MOVIE_MEMBERS = []
    for line in f.readlines():
        first_name, username = line.strip().split(" ")
        MOVIE_MEMBERS.append((first_name, username))


def next_sunday() -> datetime.date:
    # datetime.date is always timezone-unaware
    d = datetime.datetime.now()
    d += datetime.timedelta(days=6-d.weekday())
    return datetime.date(year=d.year, month=d.month, day=d.day)


class MovieClub:
    def __init__(self, members: List[Tuple[str, str]]):
        self.members = members
        self._curr = 0

    def next(self):
        self._curr = (self._curr + 1) % len(self.members)

    def curr(self) -> str:
        return self.members[self._curr][1]

    def is_girl(self) -> bool:
        # LMAO

        # based on the order in movie_club.txt
        if self._curr in [3, 7]:
            return True

        return False


MOVIE_CLUB = MovieClub(MOVIE_MEMBERS)


def next(context: CallbackContext):
    MOVIE_CLUB.next()


def reply_info(update: Update, context: CallbackContext):
    current_person = MOVIE_CLUB.curr()
    gender = "sis" if MOVIE_CLUB.is_girl() else "bro"

    jobq = context.job_queue
    # Assumes there is always a job of this name in the queue (there should be)
    next_job = jobq.get_jobs_by_name("movie_reminder")[0]
    logging.info(next_job)

    context.bot.send_message(
        chat_id=update.effective_chat.id,
        reply_to_message_id=update.effective_message.message_id,
        text="\n".join([
            f"Up next for movies, my {gender} {current_person}'s on the docket!",
            f"I'll remind you on {next_job.next_t}! 🔪"
        ]),
    )


def movie_upcoming(update: Update, context: CallbackContext):
    context.bot.send_message(chat_id=update.effective_chat.id, text=MOVIE_CLUB.curr())


def movie_members(update: Update, context: CallbackContext):
    msg = ["Members:"] + [m[0] for m in MOVIE_CLUB.members]
    context.bot.send_message(chat_id=update.effective_chat.id, text="\n".join(msg))


def movie_next(update: Update, context: CallbackContext):
    if update.effective_chat.id == CREATOR_CHAT_ID:
        MOVIE_CLUB.next()
    else:
        context.bot.send_message(chat_id=update.effective_chat.id, text="Can't do that in this chat! Sorry.")


def _get_unseen(poll: Poll) -> List[str]:
    max_votes = poll.total_voter_count
    return [option.text for option in poll.options if option.voter_count == max_votes]


def _save_poll_movies(poll: Poll):
    movies = Movies()
    for unseen in _get_unseen(poll):
        logging.info(f"unseen: {unseen}")
        movies.insert(unseen)


def movie_save_poll(update: Update, context: CallbackContext) -> int:
    """
    Saves all 100% (unwatched) options from a movie poll.
    Requires this command message to be a REPLY to telegram poll.

    Will create an inline keyboard if the poll is not closed yet, with
    buttons to indicate when the poll has been closed (or cancel).
    """
    logging.info(f"received save_movies: {update.message.message_id}")
    try:
        assert update.message.reply_to_message
        assert update.message.reply_to_message.poll
    except AssertionError:
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            reply_to_message_id=update.effective_message.message_id,
            text="hey bestie! this command needs to be in reply to a poll!",
        )
        return ConversationHandler.END

    poll = update.message.reply_to_message.poll

    if poll.is_closed:
        _save_poll_movies(poll)

        context.bot.send_message(
            chat_id=update.effective_chat.id,
            reply_to_message_id=update.effective_message.message_id,
            # text="movies that each voter has not seen:\n" + "\n".join(unseen),
            text="Saved all 💯 unseen options!",
        )

        return ConversationHandler.END

    else:
        return _callback_poll_closed_helper(update, context)


def _callback_poll_closed_helper(update: Update, context: CallbackContext) -> int:
    reply_markup = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("Closed 👍", callback_data="1"),
            InlineKeyboardButton("Cancel 🚫", callback_data="0"),
        ]
    ])


    user = update.effective_message.reply_to_message.from_user.username

    # in reply to a user pressing "Closed" but the poll isn't closed yet (i.e. from a callback)
    if query := update.callback_query:
        query.answer()
        try:
            query.edit_message_text(
                f"This poll still hasn't been closed! Let me know when @{user} closes it.",
                reply_markup=reply_markup,
            )
        except error.BadRequest:
            # will throw telegram.error.BadRequest if the message_text has already been changed to this.
            # the error is not a problem, continuing to click Closed after actually closing the poll works.
            pass

        return 0

    # in reply to /save_movies command (no keyboard generated yet)
    else:
        update.message.reply_text(
            f"This poll hasn't been closed yet! @{user}, let me know when you've closed it, and I'll save the unseen choices.",
            reply_to_message_id=update.effective_message.reply_to_message.message_id,
            reply_markup=reply_markup,
        )

        return 0


def callback_poll_save(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    poll = query.message.reply_to_message.poll

    if not poll.is_closed:
        return _callback_poll_closed_helper(update, context)

    _save_poll_movies(poll)

    query.answer()
    query.edit_message_text(text="Saved all 💯 unseen options!")
    return ConversationHandler.END


def manual_poll_tag(update: Update, context: CallbackContext):
    """
    Tag-reply and pin a poll if a user replies to it and @'s me.
    """
    # TODO - check that we haven't replied to this poll before (will require "db" of some kind)
    poll = update.message.reply_to_message

    curr = poll.from_user.first_name
    dt = next_sunday()
    text=f"{curr}'s #movie choice {dt.strftime('%m/%d/%y')}"

    poll.pin()
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        reply_to_message_id=poll.message_id,
        text=text,
    )


def movie_reminder(context: CallbackContext):
    current_person = MOVIE_CLUB.curr()
    context.bot.send_message(
        chat_id=GROUP_CHAT_ID,
        text=f"beep boop {current_person}, I think it's your turn for movies. You got a poll for us this week?"
    )


def callback_poll_tag(update: Update, context: CallbackContext) -> int:
    """
    Tag and pin a poll via callback
    (from an inline keyboard query to user submitting the poll)
    """
    query = update.callback_query
    query.answer()

    curr = query.message.reply_to_message.from_user.first_name
    dt = next_sunday()
    text=f"{curr}'s #movie choice {dt.strftime('%m/%d/%y')}"

    query.edit_message_text(text=text)
    query.message.reply_to_message.pin()
    return ConversationHandler.END


def callback_poll_no(update: Update, context: CallbackContext) -> int:
    """
    Remove inline keyboard if user replies "no" to poll query
    """
    query = update.callback_query
    query.answer()
    query.delete_message()
    return ConversationHandler.END


def poll_query(update: Update, context: CallbackContext) -> int:
    """
    Create inline keyboard to ask a user submitting a poll if it's their
    movie choice
    """
    keyboard = [
        [
            InlineKeyboardButton("yes", callback_data="1"),
            InlineKeyboardButton("no", callback_data="0"),
        ]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text(
        "Is this your movie poll? I can tag and pin it for you!",
        reply_to_message_id=update.effective_message.message_id,
        reply_markup=reply_markup
    )

    return 0