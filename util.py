#! /usr/bin/env python3

"""
Read from local (sensitive) files.
"""


with open("token") as f:
    TOKEN = f.read().strip()

with open("creator_chat_id.txt") as f:
    CREATOR_CHAT_ID = int(f.read().strip())

with open("group_chat_id.txt") as f:
    GROUP_CHAT_ID = int(f.read().strip())
