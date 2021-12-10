#! /usr/bin/env python3

"""
quick/dirty "database" for amar imitator bot
"""

import pickle
import json

from typing import List, Optional


def _load():
    try:
        with open("mem.pickle", "rb") as f:
            data = pickle.load(f)
    except FileNotFoundError:
        data = {}

    return data


def _save(key, dct):
    full_data = _load()
    full_data[key] = dct

    with open("mem.pickle", "wb") as f:
        pickle.dump(full_data, f)


class Movies:
    def __init__(self):
        self.movies = _load().get("movies")
        if not self.movies:
            self.movies = []

    def _save(self):
        _save("movies", self.movies)

    def all(self) -> List[str]:
        return self.movies

    def insert(self, title: str):
        """
        Insert a movie title.
        Does not check if title already is in list.
        """
        self.movies.append(title)
        self._save()


class Users:
    def __init__(self):
        with open("movie_club.json") as f:
            self.members = json.load(f)

    def _save(self):
        with open("movie_club.json", "w") as f:
            json.dump(self.members, f)

    def next(self):
        idx, _ = next(filter(lambda e: e[1]["current"], enumerate(self.members)))
        self.members[idx] = False
        idx = (idx + 1) % len(self.members)
        self.members[idx] = True

        self._save()

    def curr(self) -> str:
        person = next(filter(lambda m: m["current"], self.members))
        return person["username"]

    def is_girl(self) -> bool:
        idx, _ = next(filter(lambda e: e[1]["current"], enumerate(self.members)))
        if idx in [3, 7]:
            return True
        return False