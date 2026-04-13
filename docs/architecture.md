# Architecture

```
        keystrokes                       rendered output
user  ───────────►  acc (PTY master)  ───────────────►  terminal (sighted view)
                         │                                     ▲
                         ▼                                     │
                    pty.fork() ──────────►  child (claude, bash, ...)
                         │
                         ▼
                   ScreenModel (pyte VT emulator)
                         │
                         ▼
                   frame diff + spinner suppression
                         │
                         ▼
                   debounce (0.3s)
                         │
                         ▼
                   Backend.speak()  ─►  say / spd-say / dry run log
```

## Why a PTY

Ink, vim, htop, fzf, lazygit, and Claude Code all take over the terminal, enter raw mode, and repaint cells directly via ANSI escapes. A shell rc hook cannot see a stream of lines because the shell never sees one. The only layer where linearization is possible is a PTY between the user's terminal and the child, running a headless VT emulator and emitting semantic diffs.

## Why pyte

`pyte` is the only mature off-the-shelf headless VT100/xterm emulator in any ecosystem. It maintains a cell grid, a scrollback history, and an attribute model. TDSR, fenrir, and tui-use all build on it (or on similar custom implementations). Reimplementing VT parsing is out of scope for a PoC.

## Diff algorithm (v0.1)

On every chunk read from the PTY master:

1. Feed bytes to `pyte.Stream`, which advances `pyte.Screen`.
2. Take `screen.display` (list of row strings, padded to width).
3. Right-strip each row and compare to the previous snapshot.
4. For each row where `prev != curr`:
   - If `_strip_spinners(prev) == _strip_spinners(curr)`, it's a spinner-only change. Skip.
   - Otherwise emit `Event(row, curr)`.

The main loop keeps a `pending: dict[row, text]` that gets overwritten on subsequent events for the same row. A debounce timer (0.3s) waits for streaming output to settle before speaking, so a line that grows `Hel → Hello → Hello, world` produces exactly one utterance.

## Known limitations (PoC)

- Scrollback rolling will re-emit row 0 repeatedly when multiple lines scroll off the top. Acceptable for v0.1; a scroll-aware diff is a follow-up issue.
- Attribute changes (color, bold) are ignored. Only plain text is extracted.
- Wide characters and combining marks are handled only as well as pyte handles them.
- Claude Code's input box at the bottom of the screen will trigger events when the prompt redraws. The debounce and `last_utterance` dedupe mostly hide this.
