# Upstream tracking

`accessible-claude-code` is a user-space workaround. The correct long-term fix is for Claude Code to ship a `--screen-reader` mode that uses Ink's built-in screen-reader hooks. This document tracks the relevant upstream threads.

## anthropics/claude-code

- **[#11002](https://github.com/anthropics/claude-code/issues/11002)** — Add a `--screen-reader` mode for better accessibility with NVDA and JAWS. **Open, unimplemented.** Primary upstream tracking issue.
- **[#13848](https://github.com/anthropics/claude-code/issues/13848)** — Disable animated activity indicator (light sensitivity + screen reader spam). Open.
- **[#247](https://github.com/anthropics/claude-code/issues/247)** — Screen Reader Accessibility for Unicode Symbols. Open.
- **[#15509](https://github.com/anthropics/claude-code/issues/15509)** — `--no-ansi` flag. Closed: not planned.
- **[#14488](https://github.com/anthropics/claude-code/issues/14488)** — Accessibility features signal. Closed: not planned.

Do **not** open new issues about screen-reader support upstream: #11002 already covers the core ask and new dupes dilute the signal. Comment on #11002 with links to this project instead.

## Ink (vadimdemedes/ink)

- `useIsScreenReaderEnabled()` hook — detects screen reader presence. Source: [ink npm](https://www.npmjs.com/package/ink).
- `aria-*` props on `<Box>` and `<Text>` — let app authors provide semantic labels.

Claude Code does not currently use either. A minimal upstream PR would:

1. Wire `useIsScreenReaderEnabled` into the root component.
2. Branch: when screen reader is detected (or `--screen-reader` flag is passed), skip the spinner, suppress in-place redraws, and emit assistant output as line-oriented plain text.
3. Reuse the existing `--output-format text` path under the hood.

## How accessible-claude-code fits

This project is the user-space workaround that exists until #11002 lands. Once upstream ships a `--screen-reader` mode, this wrapper becomes redundant for Claude Code itself but remains useful for other Ink-based TUIs (and any non-Ink TUI that redraws in place).
