# Terminal Screen Reader Landscape (research archive)

This document archives the research done before building `accessible-claude-code`, per the archival practice of keeping exploration findings durable. Dates: research conducted April 2026.

## Claude Code's current accessibility state

Claude Code has no built-in flags, settings, or modes for screen reader users. The CLI is built on [Ink](https://github.com/vadimdemedes/ink) (React-for-CLI), which uses ANSI escapes and redraws character cells. Screen readers cannot follow cursor-based repaints, so:

- ANSI formatting causes distorted speech output and screen reader freezes.
- Spinners and animated updates spam TTS.
- Streaming token reveal overwhelms accessibility APIs.
- Hard newlines break text wrapping for low-vision users with large fonts.

Upstream issues:

| Issue | Title | Status |
|---|---|---|
| [#11002](https://github.com/anthropics/claude-code/issues/11002) | Add `--screen-reader` mode for NVDA/JAWS | **open** |
| [#13848](https://github.com/anthropics/claude-code/issues/13848) | Disable animated activity indicator | open |
| [#247](https://github.com/anthropics/claude-code/issues/247) | Unicode symbol accessibility | open |
| [#15509](https://github.com/anthropics/claude-code/issues/15509) | `--no-ansi` flag | closed: not planned |
| [#14488](https://github.com/anthropics/claude-code/issues/14488) | Accessibility features signal | closed: not planned |

`--print` / `--output-format stream-json/text` exist but are not positioned as accessibility-friendly and not documented as such. Ink exposes `useIsScreenReaderEnabled` and `aria-*` props on `Box`/`Text` ([npm](https://www.npmjs.com/package/ink)), but Claude Code does not currently use them.

An unofficial community tool exists: [claude-sonar](https://github.com/vylasaven/claude-sonar) (MCP-based).

## Platform landscape

### macOS

VoiceOver works tolerably in Terminal.app and iTerm2 for static line-oriented output. iTerm2 has explicit VoiceOver hooks and is the community-recommended choice over Terminal.app. Neither handles TUI redraws: VO reads the AX tree of the character grid, so cursor-based repaints cause stale or jumbled speech. Warp has no meaningful a11y story. Blind macOS terminal users commonly rely on [TDSR](https://github.com/tspivey/tdsr) instead of VO for terminal work.

References:
- [iTerm2 for Mac — a very decent terminal replacement (iaccessibility.net)](https://iaccessibility.net/iterm2-for-mac-a-very-decent-terminal-replacement/)
- [iTerm2 features](https://iterm2.com/features.html)
- [VoiceOver User Guide for Mac](https://support.apple.com/guide/voiceover/welcome/mac)

### Windows

Strongest platform. Windows Terminal exposes a UIA TextPattern provider (landed ~2020, matured since). NVDA and Narrator read line-oriented output from cmd, PowerShell, and Windows Terminal reliably. NVDA 2025.x documents Windows Console review mode. TUI apps remain problematic on full-screen redraws.

References:
- [NVDA 2025.3 User Guide](https://download.nvaccess.org/releases/2025.3/documentation/userGuide.html)
- [NVDA GitHub](https://github.com/nvaccess/nvda/)
- [Pinokio terminal UIA accessibility issue #1049](https://github.com/pinokiocomputer/pinokio/issues/1049)

### Linux

- **[Emacspeak](https://github.com/tvraman/emacspeak)** (T.V. Raman): actively maintained, the richest audio experience but Emacs-bound.
- **Speakup**: kernel module, TTY-console only, still maintained.
- **[Fenrir](https://github.com/chrys87/fenrir)**: Python, works in TTY and in xterm via a PTY driver, actively maintained, the closest thing to a modern general-purpose console reader.
- **YASR**: C, PTY-based, effectively unmaintained upstream but still shipped in Debian.
- **BRLTTY**: braille standard, active.
- **Orca**: GUI only.

References:
- [List of Linux Screen Readers](https://linuxaccessibility.com/wiki/List_of_Linux_Screen_Readers)
- [Emacspeak on opensource.com](https://opensource.com/life/16/6/emacspeak-brings-linux-blind)
- [Speakup FAQ](http://www.linux-speakup.org/faq.html)

### Android — Termux + TalkBack

Does not work meaningfully. Termux renders into a custom `View`, not `EditText`, so TalkBack sees nothing. Open issues:
- [termux-app#1797](https://github.com/termux/termux-app/issues/1797)
- [termux-app#4175](https://github.com/termux/termux-app/issues/4175)
- [termux-app#4304](https://github.com/termux/termux-app/issues/4304)
- [termux-app PR #4104](https://github.com/termux/termux-app/pull/4104) — partial reading-mode hooks

Practical workaround: SSH from Termux into a Linux box running Fenrir or TDSR. Or run `espeak` manually in Termux.

### iOS — a-Shell, iSH, Blink Shell, Terminus

All poor. Blink Shell has the most effort but [AppleVis threads](https://applevis.com/forum/ios-ipados/ssh-terminal-ios-12) document that typed characters aren't announced and its gestures conflict with VO. a-Shell and iSH have no documented VO support. In practice blind iOS users SSH out to a server running a real console screen reader.

## PTY-sniffing prior art (the right architectural layer)

- **[TDSR](https://github.com/tspivey/tdsr)**: Python, spawns a PTY, feeds output through `pyte` (headless VT emulator), speaks diffs via `say`/`espeak`. macOS + Linux. The canonical architecture and the model for this project.
- **[tui-use](https://github.com/onesuper/tui-use)** and **[termwright](https://github.com/fcoury/termwright)**: agent-oriented PTY observers using headless xterm/pyte. Not accessibility tools but share the right primitive.
- **[vim-accessibility](https://github.com/luffah/vim-accessibility)**: vim-specific, not general.

Key insight: ANSI-stripping pipes fail on full-screen TUIs. You must run a VT emulator and diff cell grids. That's what pyte and this project do.

## Shell-level TTS (insufficient for TUIs)

Ad-hoc patterns exist — piping to `say` (macOS), `espeak` or `spd-say` (Linux speech-dispatcher). [Speech Dispatcher](https://wiki.archlinux.org/title/Speech_dispatcher) is the correct Linux abstraction. Nothing like "oh-my-zsh-a11y" exists. None of these reach inside a TUI process, which is why this project takes the PTY approach instead.

## Why this project exists

The gap between (1) upstream Claude Code acknowledging but not implementing screen reader support and (2) the absence of any PTY-based wrapper targeting Ink specifically means that blind developers who want to use Claude Code today have no workable option. `accessible-claude-code` fills that gap as a small, focused PoC with a clear upgrade path to upstream adoption via `--screen-reader` mode and Ink's `useIsScreenReaderEnabled` hook.
