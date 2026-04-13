from __future__ import annotations

import argparse
import fcntl
import os
import pty
import select
import signal
import struct
import sys
import termios
import time
import tty
from typing import Dict, List, Optional

from .screen import ScreenModel
from .speech import Backend, make_backend

CTRL_BACKSLASH = b"\x1c"
CTRL_RBRACKET = b"\x1d"
DEBOUNCE_SEC = 0.3
READ_CHUNK = 4096


def _get_winsize(fd: int) -> tuple[int, int]:
    try:
        s = fcntl.ioctl(fd, termios.TIOCGWINSZ, b"\x00" * 8)
        rows, cols, _, _ = struct.unpack("hhhh", s)
        if rows == 0 or cols == 0:
            return 40, 120
        return rows, cols
    except OSError:
        return 40, 120


def _set_winsize(fd: int, rows: int, cols: int) -> None:
    s = struct.pack("hhhh", rows, cols, 0, 0)
    try:
        fcntl.ioctl(fd, termios.TIOCSWINSZ, s)
    except OSError:
        pass


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="acc",
        description="PTY screen-reader wrapper for TUIs (Claude Code, Ink, etc.)",
    )
    parser.add_argument("--rate", type=int, default=300, help="speech rate in words per minute")
    parser.add_argument("--no-speak", action="store_true", help="log events to $ACC_LOG instead of speaking")
    parser.add_argument("command", nargs=argparse.REMAINDER, help="command to wrap (e.g. claude)")
    args = parser.parse_args(argv)

    if not args.command:
        parser.error("missing command (e.g., `acc claude`)")

    stdin_fd = sys.stdin.fileno()
    stdin_is_tty = os.isatty(stdin_fd)
    rows, cols = _get_winsize(stdin_fd) if stdin_is_tty else (40, 120)
    screen = ScreenModel(cols=cols, rows=rows)
    backend = make_backend(rate=args.rate, dry_run=args.no_speak)

    pid, master_fd = pty.fork()
    if pid == 0:
        try:
            os.execvp(args.command[0], args.command)
        except FileNotFoundError:
            os.write(2, f"acc: command not found: {args.command[0]}\n".encode())
            os._exit(127)

    _set_winsize(master_fd, rows, cols)

    old_tty = termios.tcgetattr(stdin_fd) if stdin_is_tty else None
    try:
        if stdin_is_tty:
            tty.setraw(stdin_fd)
        _main_loop(master_fd, stdin_fd, screen, backend, stdin_is_tty=stdin_is_tty)
    finally:
        if old_tty is not None:
            termios.tcsetattr(stdin_fd, termios.TCSADRAIN, old_tty)
        backend.stop()

    _, status = os.waitpid(pid, 0)
    if os.WIFEXITED(status):
        return os.WEXITSTATUS(status)
    return 1


def _main_loop(
    master_fd: int,
    stdin_fd: int,
    screen: ScreenModel,
    backend: Backend,
    stdin_is_tty: bool = True,
) -> None:
    pending: Dict[int, str] = {}
    last_event_ts = 0.0
    last_utterance = ""

    if stdin_is_tty:
        def on_winch(signum, frame):  # type: ignore[no-untyped-def]
            r, c = _get_winsize(stdin_fd)
            _set_winsize(master_fd, r, c)
            screen.resize(cols=c, rows=r)

        signal.signal(signal.SIGWINCH, on_winch)

    watched = [master_fd, stdin_fd] if stdin_is_tty else [master_fd]

    while True:
        try:
            readable, _, _ = select.select(watched, [], [], 0.05)
        except (OSError, select.error):
            break
        except InterruptedError:
            continue

        if master_fd in readable:
            try:
                data = os.read(master_fd, READ_CHUNK)
            except OSError:
                break
            if not data:
                break
            os.write(1, data)
            for ev in screen.feed(data):
                text = ev.text.strip()
                if text:
                    pending[ev.row] = text
                else:
                    pending.pop(ev.row, None)
                last_event_ts = time.monotonic()

        if stdin_fd in readable:
            try:
                data = os.read(stdin_fd, 1024)
            except OSError:
                break
            if not data:
                break
            if data == CTRL_BACKSLASH:
                backend.stop()
                continue
            if data == CTRL_RBRACKET:
                if last_utterance:
                    backend.speak(last_utterance)
                continue
            try:
                os.write(master_fd, data)
            except OSError:
                break

        if pending and (time.monotonic() - last_event_ts) > DEBOUNCE_SEC:
            text = " ".join(v for _, v in sorted(pending.items()) if v)
            pending.clear()
            if text and text != last_utterance:
                backend.speak(text)
                last_utterance = text

    if pending:
        text = " ".join(v for _, v in sorted(pending.items()) if v)
        if text and text != last_utterance:
            backend.speak(text)
