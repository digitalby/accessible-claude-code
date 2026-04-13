from pathlib import Path

from accessible_claude_code.speech import DryRunBackend, SayBackend, SpdSayBackend, make_backend


def test_dry_run_writes_to_log(tmp_path: Path):
    log = tmp_path / "events.log"
    backend = DryRunBackend(log_path=log)
    backend.speak("hello")
    backend.speak("world")
    backend.stop()
    assert log.read_text(encoding="utf-8") == "hello\nworld\n"


def test_dry_run_creates_parent_dir(tmp_path: Path):
    log = tmp_path / "nested" / "dir" / "events.log"
    backend = DryRunBackend(log_path=log)
    backend.speak("hi")
    assert log.exists()


def test_make_backend_dry_run_returns_dry_run(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("ACC_LOG", str(tmp_path / "events.log"))
    backend = make_backend(dry_run=True)
    assert isinstance(backend, DryRunBackend)


def test_spd_say_rate_mapping():
    backend = SpdSayBackend(rate=180)
    assert backend.rate == 0
    backend = SpdSayBackend(rate=380)
    assert backend.rate == 100
    backend = SpdSayBackend(rate=80)
    assert backend.rate == -50


def test_say_backend_constructible():
    backend = SayBackend(rate=250)
    assert backend.rate == 250
