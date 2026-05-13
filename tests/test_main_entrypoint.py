from __future__ import annotations

import main


def test_main_entrypoint_reuses_app_main() -> None:
    assert callable(main.main)
