from __future__ import annotations

from dataclasses import dataclass
from typing import List

import pyte

SPINNER_CHARS = set("⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏|/-\\◐◓◑◒◴◵◶◷◜◝◞◟⣾⣽⣻⢿⡿⣟⣯⣷")


@dataclass
class Event:
    row: int
    text: str


class ScreenModel:
    def __init__(self, cols: int = 120, rows: int = 40) -> None:
        self.cols = cols
        self.rows = rows
        self.screen = pyte.Screen(cols, rows)
        self.stream = pyte.Stream(self.screen)
        self.prev_display: List[str] = [""] * rows

    def resize(self, cols: int, rows: int) -> None:
        self.cols = cols
        self.rows = rows
        self.screen.resize(lines=rows, columns=cols)
        self.prev_display = [""] * rows

    def feed(self, data: bytes) -> List[Event]:
        text = data.decode("utf-8", errors="replace")
        self.stream.feed(text)
        curr = [row.rstrip() for row in self.screen.display]
        while len(curr) < self.rows:
            curr.append("")
        events = _diff(self.prev_display, curr)
        self.prev_display = curr
        return events


def _diff(prev: List[str], curr: List[str]) -> List[Event]:
    events: List[Event] = []
    for row, (p, c) in enumerate(zip(prev, curr)):
        if p == c:
            continue
        if _is_spinner_change(p, c):
            continue
        events.append(Event(row=row, text=c))
    return events


def _strip_spinners(s: str) -> str:
    return "".join(ch for ch in s if ch not in SPINNER_CHARS).strip()


def _is_spinner_change(prev: str, curr: str) -> bool:
    return _strip_spinners(prev) == _strip_spinners(curr)
