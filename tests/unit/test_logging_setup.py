"""setup_logging()'s three switches (master / console / file) and the
one-file-per-level layout."""

import json
import logging

import pytest
from pydantic import ValidationError

from app.core import logging as app_logging
from app.core.config import ConsoleLogConfig, FileLogConfig, LogConfig, settings


@pytest.fixture(autouse=True)
def _restore_logging():
    root = logging.getLogger()
    saved_handlers, saved_level = list(root.handlers), root.level
    yield
    for h in list(root.handlers):
        root.removeHandler(h)
        h.close()
    for h in saved_handlers:
        root.addHandler(h)
    root.setLevel(saved_level)
    logging.disable(logging.NOTSET)


def _apply(monkeypatch, **overrides):
    monkeypatch.setattr(settings, "logging", LogConfig(**overrides))
    app_logging.setup_logging()


def _flush():
    for h in logging.getLogger().handlers:
        h.flush()


def test_master_switch_off_silences_everything(monkeypatch, capsys):
    _apply(monkeypatch, enabled=False)
    log = logging.getLogger("t.master")
    log.error("boom")
    log.critical("worse")
    assert capsys.readouterr().out == ""
    assert not log.isEnabledFor(logging.CRITICAL)
    # Uvicorn's native loggers are not touched by the master switch
    assert logging.root.manager.disable == logging.NOTSET


def test_master_switch_back_on_after_off(monkeypatch, capsys):
    _apply(monkeypatch, enabled=False)
    _apply(monkeypatch, enabled=True)
    logging.getLogger("t.reenable").warning("hello")
    assert "hello" in capsys.readouterr().out


def test_console_on_writes_json_to_stdout(monkeypatch, capsys):
    _apply(monkeypatch, console=ConsoleLogConfig(enabled=True))
    logging.getLogger("t.console").info("visible", extra={"event": "t.visible"})
    line = capsys.readouterr().out.strip().splitlines()[-1]
    assert json.loads(line)["event"] == "t.visible"


def test_console_off_writes_nothing(monkeypatch, capsys):
    _apply(monkeypatch, console=ConsoleLogConfig(enabled=False))
    logging.getLogger("t.console").error("hidden")
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == ""  # no last-resort handler fallback


def test_file_off_creates_no_folder(monkeypatch, tmp_path):
    target = tmp_path / "logs"
    _apply(monkeypatch, file=FileLogConfig(enabled=False, path=str(target)))
    logging.getLogger("t.file").error("x")
    assert not target.exists()


def test_file_one_file_per_exact_level(monkeypatch, tmp_path):
    _apply(
        monkeypatch,
        level="DEBUG",
        console=ConsoleLogConfig(enabled=False),
        file=FileLogConfig(enabled=True, path=str(tmp_path)),
    )
    log = logging.getLogger("t.levels")
    log.debug("d-msg")
    log.info("i-msg")
    log.warning("w-msg")
    log.error("e-msg")
    log.critical("c-msg")
    _flush()

    def lines(name):
        return [
            json.loads(x)["message"]
            for x in (tmp_path / f"{name}.log").read_text(encoding="utf-8").splitlines()
        ]

    assert lines("debug") == ["d-msg"]
    assert lines("info") == ["i-msg"]
    assert lines("warning") == ["w-msg"]
    assert lines("error") == ["e-msg", "c-msg"]  # error also takes CRITICAL


def test_file_respects_root_level(monkeypatch, tmp_path):
    _apply(
        monkeypatch,
        level="INFO",
        file=FileLogConfig(enabled=True, path=str(tmp_path)),
    )
    log = logging.getLogger("t.gate")
    log.debug("never")
    log.info("kept")
    _flush()
    assert not (tmp_path / "debug.log").exists()
    assert (tmp_path / "info.log").exists()


def test_file_only_configured_levels(monkeypatch, tmp_path):
    _apply(
        monkeypatch,
        level="DEBUG",
        file=FileLogConfig(enabled=True, path=str(tmp_path), levels=["error"]),
    )
    log = logging.getLogger("t.only")
    log.info("i")
    log.error("e")
    _flush()
    assert {p.name for p in tmp_path.iterdir()} == {"error.log"}


def test_retention_days_is_the_rotation_backup_count(monkeypatch, tmp_path):
    _apply(
        monkeypatch,
        file=FileLogConfig(enabled=True, path=str(tmp_path), retention_days=3),
    )
    rotating = [
        h
        for h in logging.getLogger().handlers
        if isinstance(h, app_logging.TimedRotatingFileHandler)
    ]
    assert rotating and all(h.backupCount == 3 for h in rotating)


def test_file_levels_validated_and_normalised():
    assert FileLogConfig(levels=["INFO", "Error"]).levels == ["info", "error"]
    with pytest.raises(ValidationError):
        FileLogConfig(levels=["verbose"])
    with pytest.raises(ValidationError):
        FileLogConfig(retention_days=0)


def test_uvicorn_access_console_style_but_json_in_file(monkeypatch, tmp_path, capsys):
    _apply(
        monkeypatch,
        uvicorn_access=True,
        file=FileLogConfig(enabled=True, path=str(tmp_path)),
    )
    logging.getLogger("uvicorn.access").info(
        '%s - "%s %s HTTP/%s" %d', "127.0.0.1:5", "GET", "/x", "1.1", 307
    )
    # other loggers on the console still use the configured (JSON) formatter
    logging.getLogger("t.other").info("plain")
    _flush()

    out = capsys.readouterr().out.splitlines()
    access = [x for x in out if "127.0.0.1:5" in x][0]
    assert access.startswith("INFO:")
    assert '"GET /x HTTP/1.1" 307 Temporary Redirect' in access
    assert any(json.loads(x)["message"] == "plain" for x in out if x.startswith("{"))

    file_lines = (tmp_path / "info.log").read_text(encoding="utf-8").splitlines()
    rec = [json.loads(x) for x in file_lines if "127.0.0.1:5" in x][0]
    assert rec["logger"] == "uvicorn.access" and rec["message"].endswith("307")


def test_master_off_leaves_uvicorn_native_logger_working(monkeypatch):
    uv = logging.getLogger("uvicorn.access")
    saved = (list(uv.handlers), uv.propagate, uv.level)
    seen = []

    class _H(logging.Handler):
        def emit(self, record):
            seen.append(record.getMessage())

    uv.handlers[:] = [_H()]
    uv.propagate = False
    uv.setLevel(logging.INFO)
    try:
        _apply(monkeypatch, enabled=False)
        uv.info("native line")
        logging.getLogger("t.app").error("app line")
        assert seen == ["native line"]
    finally:
        uv.handlers[:] = saved[0]
        uv.propagate, level = saved[1], saved[2]
        uv.setLevel(level)
