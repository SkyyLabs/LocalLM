from __future__ import annotations

import app


def test_extra_cli_arguments_are_rejected(monkeypatch) -> None:
    monkeypatch.setattr("sys.argv", ["main.py", "summarize", "--file", "data/private/doc.txt"])

    try:
        app.main()
    except SystemExit as exc:
        assert exc.code == 2
    else:
        raise AssertionError("Expected direct CLI arguments to be rejected.")
