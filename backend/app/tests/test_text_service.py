from app.services.text_service import limit_text, normalize_whitespace


def test_normalize_whitespace_collapses_spaces_and_newlines() -> None:
    assert normalize_whitespace(" Python\n\n  SQL\tAWS ") == "Python SQL AWS"


def test_limit_text_keeps_short_text_unchanged() -> None:
    assert limit_text("short", 10) == "short"


def test_limit_text_truncates_with_ellipsis() -> None:
    assert limit_text("abcdefghijklmnopqrstuvwxyz", 10) == "abcdefg..."
