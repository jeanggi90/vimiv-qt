# vim: ft=python fileencoding=utf-8 sw=4 et sts=4

# This file is part of vimiv.
# Copyright 2017-2019 Christian Karl (karlch) <karlch at protonmail dot com>
# License: GNU GPL v3, see the "LICENSE" and "AUTHORS" files for details.

"""Functions to read and write command history."""

import collections
import os
from typing import List

from vimiv.commands import argtypes
from vimiv.utils import xdg


def read():
    """Read command history from file."""
    filename = xdg.join_vimiv_data("history")
    # Create empty history file
    if not os.path.isfile(filename):
        with open(filename, "w") as f:
            f.write("")
        return []
    # Read from file
    history = []
    with open(filename) as f:
        for line in f.readlines():
            history.append(line.rstrip("\n"))
    return history


def write(commands: List[str]):
    """Write command history to file.

    Args:
        commands: List of commands.
    """
    filename = xdg.join_vimiv_data("history")
    with open(filename, "w") as f:
        for command in commands:
            f.write(command + "\n")


class History(collections.deque):
    """Store and interact with command line history.

    Implemented as a deque which stores the commands in the history.

    Attributes:
        _index: Index of the currently %% command.
        _max_items: Integer defining the maximum amount of items to store.
        _temporary_element_stored: Bool telling if a temporary text stored in
            history during cycle.
    """

    def __init__(self, commands, max_items=100):
        super().__init__(commands, maxlen=max_items)
        self._index = 0
        self._temporary_element_stored = False
        self._substr_matches: List[str] = []

    def update(self, command: str):
        """Update history with a new command.

        Args:
            command: New command to be inserted.
        """
        self.reset()
        if command in self:
            self.remove(command)
        self.appendleft(command)

    def reset(self):
        """Reset history when command was run."""
        self._index = 0
        if self._temporary_element_stored:
            self.popleft()
            self._temporary_element_stored = False
            self._substr_matches = []

    def cycle(self, direction: argtypes.HistoryDirection, text: str):
        """Cycle through command history.

        Called from the command line by the history command.

        Args:
            direction: HistoryDirection element.
            text: Current text in the command line.
        Returns:
            The received command string to set in the command line.
        """
        if not self:
            return ""
        if not self._temporary_element_stored:
            self.appendleft(text)
            self._temporary_element_stored = True
        if direction == direction.Next:
            self._index = (self._index + 1) % len(self)
        else:
            self._index = (self._index - 1) % len(self)
        return self[self._index]

    def substr_cycle(self, direction: argtypes.HistoryDirection, text: str):
        """Cycle through command history with substring matching.

        Called from the command line by the history-substr-search command.

        Args:
            direction: HistoryDirection element.
            text: Current text in the command line used as substring.
        Returns:
            The received command string to set in the command line.
        """
        if not self:
            return ""
        if not self._temporary_element_stored:
            self.appendleft(text)
            self._temporary_element_stored = True
            for command in self:
                if text in command:
                    self._substr_matches.append(command)
        if direction == direction.Next:
            self._index = (self._index + 1) % len(self._substr_matches)
        else:
            self._index = (self._index - 1) % len(self._substr_matches)
        return self._substr_matches[self._index]
