import builtins

from sip_indoor_station.media.gstreamer_check import (
    REQUIRED_GSTREAMER_ELEMENTS,
    GStreamerCheckResult,
    check_required_elements,
)


def test_gstreamer_check_result_reports_missing_elements_clearly() -> None:
    result = GStreamerCheckResult(False, ["webrtcbin", "opusenc"])
    try:
        result.assert_available()
    except RuntimeError as exc:
        assert "webrtcbin" in str(exc)
        assert "opusenc" in str(exc)
    else:
        raise AssertionError("expected RuntimeError")


def test_gstreamer_check_includes_pcmu_and_pcma_elements() -> None:
    assert "nicesrc" in REQUIRED_GSTREAMER_ELEMENTS
    assert "nicesink" in REQUIRED_GSTREAMER_ELEMENTS
    assert "rtppcmudepay" in REQUIRED_GSTREAMER_ELEMENTS
    assert "rtppcmupay" in REQUIRED_GSTREAMER_ELEMENTS
    assert "mulawdec" in REQUIRED_GSTREAMER_ELEMENTS
    assert "mulawenc" in REQUIRED_GSTREAMER_ELEMENTS
    assert "rtppcmadepay" in REQUIRED_GSTREAMER_ELEMENTS
    assert "rtppcmapay" in REQUIRED_GSTREAMER_ELEMENTS
    assert "alawdec" in REQUIRED_GSTREAMER_ELEMENTS
    assert "alawenc" in REQUIRED_GSTREAMER_ELEMENTS


def test_gstreamer_check_reports_import_failure(monkeypatch) -> None:
    real_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == "gi":
            raise ImportError("no gi")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    result = check_required_elements(["webrtcbin"])
    assert result.available is False
    assert result.missing == ["webrtcbin"]
    assert "PyGObject/GStreamer import failed" in (result.error or "")
