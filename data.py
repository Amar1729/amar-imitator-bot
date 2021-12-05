#! /usr/bin/env python3

"""
quick/dirty "database" for amar imitator bot
"""

import pickle

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