from app.utils.deeplink import normalize_source_code


def test_normalize_source_code_valid() -> None:
    assert normalize_source_code("yt_video_01") == "yt_video_01"


def test_normalize_source_code_invalid_symbols() -> None:
    assert normalize_source_code("yt video 01!") is None


def test_normalize_source_code_empty() -> None:
    assert normalize_source_code("   ") is None

