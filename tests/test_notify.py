"""Tests for ntfy.sh notification integration."""

from unittest.mock import patch, MagicMock
from board_md.notify import send_notification


def test_send_builds_correct_request():
    """Verify the HTTP request is constructed properly."""
    with patch("board_md.notify.urllib.request.urlopen") as mock_urlopen:
        mock_resp = MagicMock()
        mock_resp.status = 200
        mock_resp.__enter__ = MagicMock(return_value=mock_resp)
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_resp

        result = send_notification("test-topic", "hello")
        assert result is True

        req = mock_urlopen.call_args[0][0]
        assert "ntfy.sh/test-topic" in req.full_url
        assert req.data == b"hello"
        assert req.get_header("Title") == "board.md"


def test_send_with_delay():
    with patch("board_md.notify.urllib.request.urlopen") as mock_urlopen:
        mock_resp = MagicMock()
        mock_resp.status = 200
        mock_resp.__enter__ = MagicMock(return_value=mock_resp)
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_resp

        send_notification("t", "msg", delay="30min")
        req = mock_urlopen.call_args[0][0]
        assert req.get_header("At") == "30min"


def test_send_failure_returns_false():
    with patch("board_md.notify.urllib.request.urlopen") as mock_urlopen:
        mock_urlopen.side_effect = Exception("network error")
        result = send_notification("t", "msg")
        assert result is False
