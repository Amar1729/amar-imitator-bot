#! /usr/bin/env python3

import logging
import datetime
from typing import List, Tuple

from telegram import Update
from telegram.ext import Updater, CallbackContext, CommandHandler, MessageHandler, Filters

# local
from util import CREATOR_CHAT_ID, GROUP_CHAT_ID


with open("movie_club.txt") as f:
    MOVIE_MEMBERS = []
    for line in f.readlines():
        first_name, username = line.strip().split(" ")
        MOVIE_MEMBERS.append((first_name, username))


def next_thursday() -> datetime.datetime:
    # assume timezone for now?
    d = datetime.datetime.now()

    d = d + datetime.timedelta(hours=19 - d.hour)

    if d.weekday() != 3:
        d = d + datetime.timedelta(days=1)

    return d


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


def reply_info(update: Update, context: CallbackContext):
    current_person = MOVIE_CLUB.curr()
    gender = "sis" if MOVIE_CLUB.is_girl() else "bro"

    jobq = context.job_queue
    next_job = jobq.jobs()[0]
    logging.info(next_job)

    context.bot.send_message(
        chat_id=update.effective_chat.id,
        reply_to_message_id=update.effective_message.message_id,
        text="\n".join([
            f"Up next for movies, my {gender} {current_person}'s on the docket!",
            f"I'll remind you on {next_job.next_t}! :knife:"
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


def tag_poll(update: Update, context: CallbackContext):
    # TODO - also pin the poll
    # TODO - check that we haven't replied to this poll before (will require "db" of some kind)
    poll = update.message.reply_to_message

    curr = poll.from_user.first_name
    dt = next_sunday()

    text=f"{curr}'s #movie choice {dt.strftime('%m/%d/%y')}"
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
