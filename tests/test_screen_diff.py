from accessible_claude_code.screen import Event, ScreenModel, _is_spinner_change, _strip_spinners


def test_empty_feed_produces_no_events():
    sm = ScreenModel(cols=20, rows=3)
    assert sm.feed(b"") == []


def test_hello_world_appears_as_event():
    sm = ScreenModel(cols=20, rows=3)
    events = sm.feed(b"hello world\r\n")
    assert any("hello world" in e.text for e in events)


def test_streaming_append_emits_latest_line():
    sm = ScreenModel(cols=20, rows=3)
    sm.feed(b"Hel")
    events = sm.feed(b"lo")
    assert any(e.text == "Hello" for e in events)


def test_spinner_only_frame_is_suppressed():
    sm = ScreenModel(cols=10, rows=3)
    sm.feed("⠋".encode("utf-8"))
    events = sm.feed("\r".encode("utf-8") + "⠙".encode("utf-8"))
    assert events == []


def test_spinner_plus_text_change_is_not_suppressed():
    sm = ScreenModel(cols=20, rows=3)
    sm.feed("⠋ working".encode("utf-8"))
    events = sm.feed(("\r" + "⠙ done").encode("utf-8"))
    assert any("done" in e.text for e in events)


def test_is_spinner_change_ignores_only_spinner_chars():
    assert _is_spinner_change("⠋", "⠙")
    assert _is_spinner_change("⠋ loading", "⠙ loading")
    assert not _is_spinner_change("hello", "world")


def test_strip_spinners_removes_known_frames():
    assert _strip_spinners("⠋⠙⠹") == ""
    assert _strip_spinners("⠋ hello") == "hello"


def test_resize_resets_prev_display():
    sm = ScreenModel(cols=20, rows=3)
    sm.feed(b"hello")
    sm.resize(cols=30, rows=5)
    events = sm.feed(b"world\r\n")
    assert any("world" in e.text for e in events)


def test_event_has_row_index():
    sm = ScreenModel(cols=20, rows=3)
    events = sm.feed(b"line one\r\nline two\r\n")
    rows = {e.row for e in events}
    assert 0 in rows
    assert 1 in rows
