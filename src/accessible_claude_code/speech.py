from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path
from typing import Optional, Protocol


class Backend(Protocol):
    def speak(self, text: str) -> None: ...
    def stop(self) -> None: ...


class SayBackend:
    def __init__(self, rate: int = 300) -> None:
        self.rate = rate
        self._proc: Optional[subprocess.Popen] = None

    def speak(self, text: str) -> None:
        self.stop()
        self._proc = subprocess.Popen(
            ["say", "-r", str(self.rate), text],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    def stop(self) -> None:
        if self._proc and self._proc.poll() is None:
            self._proc.terminate()
        self._proc = None


class SpdSayBackend:
    def __init__(self, rate: int = 300) -> None:
        self.rate = max(-100, min(100, int((rate - 180) / 2)))
        self._proc: Optional[subprocess.Popen] = None

    def speak(self, text: str) -> None:
        self.stop()
        self._proc = subprocess.Popen(
            ["spd-say", "-r", str(self.rate), text],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    def stop(self) -> None:
        if self._proc and self._proc.poll() is None:
            self._proc.terminate()
        self._proc = None


class DryRunBackend:
    def __init__(self, log_path: Optional[Path] = None) -> None:
        self.log_path = log_path or Path(os.environ.get("ACC_LOG", "/tmp/acc-events.log"))
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

    def speak(self, text: str) -> None:
        with self.log_path.open("a", encoding="utf-8") as f:
            f.write(text + "\n")

    def stop(self) -> None:
        pass


def make_backend(rate: int = 300, dry_run: bool = False) -> Backend:
    if dry_run:
        return DryRunBackend()
    if shutil.which("say"):
        return SayBackend(rate=rate)
    if shutil.which("spd-say"):
        return SpdSayBackend(rate=rate)
    return DryRunBackend()
