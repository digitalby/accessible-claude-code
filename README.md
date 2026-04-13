# accessible-claude-code

A tiny PTY wrapper that makes [Claude Code](https://github.com/anthropics/claude-code) (and other [Ink](https://github.com/vadimdemedes/ink)-based TUIs) usable with a screen reader.

## The problem

Claude Code's UI is built on Ink, which renders React components as ANSI escape sequences and repaints character cells in place. This is exactly the pattern that defeats screen readers: VoiceOver, NVDA, Narrator, and TalkBack all read the terminal's visible character grid, and they cannot tell a spinner frame flip apart from new content arriving. The result is stale or jumbled speech, spinners that spam TTS, and sessions that are effectively unusable for blind developers.

Upstream tracking: [anthropics/claude-code#11002](https://github.com/anthropics/claude-code/issues/11002) is open and unimplemented.

## What this does

`acc` forks your target process under a PTY, runs its output through a headless VT emulator ([`pyte`](https://github.com/selectel/pyte)), and diffs the cell grid on every flush. Instead of shoveling raw ANSI at the screen reader, it emits one clean, linearized stream of semantic events and speaks them via a pluggable backend (`say` on macOS, `spd-say` on Linux).

Architecture borrowed from [TDSR](https://github.com/tspivey/tdsr), the canonical terminal screen reader for macOS and Linux. This is a narrower, Claude-Code-first tool in the same tradition.

## Status

Alpha. Proof of concept. macOS first, Linux tested via CI.

## Install

```
git clone https://github.com/digitalby/accessible-claude-code
cd accessible-claude-code
python3 -m venv .venv
. .venv/bin/activate
pip install -e .
```

## Usage

```
acc claude            # wrap Claude Code
acc bash              # wrap any shell or TUI for experimentation
acc --rate 320 claude # speed up speech
acc --no-speak claude # dry run, log events instead of speaking
```

### Hotkeys

| Key | Action |
|---|---|
| `Ctrl-\` | Stop current speech (barge-in) |
| `Ctrl-]` | Re-read last assistant utterance |

All other keystrokes are forwarded to the child process unchanged.

## Why not a bash/zsh rc-file hook?

A shell hook can pipe line-oriented command output to `say` or `espeak`. It cannot reach inside a TUI process, because Ink (and `vim`, `htop`, `lazygit`, `fzf`, Claude Code) take over the terminal, put it in raw mode, and repaint cells directly. The shell never sees a stream of lines. The only layer where linearization is possible is a PTY in the middle that runs a headless VT emulator and emits semantic diffs. That is what this tool does.

## Scope

**In scope for the PoC:** macOS + `say`, Claude Code's streaming assistant output, spinner suppression, re-read hotkey.

**Out of scope, tracked as issues:** Windows SAPI backend, Linux `speech-dispatcher` end-to-end, iTerm2 VoiceOver hinting, Termux/Android TalkBack, iOS (Blink / a-Shell / iSH), Linux terminal screen-reader interop, streaming rate tuning.

## Prior art

- [TDSR](https://github.com/tspivey/tdsr) — general macOS/Linux terminal screen reader
- [Fenrir](https://github.com/chrys87/fenrir) — Linux PTY-based screen reader
- [Emacspeak](https://github.com/tvraman/emacspeak) — T.V. Raman's audio desktop
- [Ink's `useIsScreenReaderEnabled`](https://github.com/vadimdemedes/ink) — the upstream-side hook Claude Code would need to wire up

## License

MIT
