"""Tests for notification dispatcher + plugin backends."""

from unittest.mock import patch, MagicMock
from board_md import notify


def test_send_ntfy():
    """ntfy plugin constructs correct HTTP request."""
    with patch("board_md.plugins.ntfy.urllib.request.urlopen") as mock_urlopen:
        mock_resp = MagicMock()
        mock_resp.status = 200
        mock_resp.__enter__ = MagicMock(return_value=mock_resp)
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_resp

        config = {"notify_backend": "ntfy", "ntfy_topic": "test-topic"}
        result = notify.send(config, "hello")
        assert result is True

        req = mock_urlopen.call_args[0][0]
        assert "ntfy.sh/test-topic" in req.full_url
        assert req.data == b"hello"
        assert req.get_header("Title") == "board.md"


def test_send_ntfy_with_delay():
    with patch("board_md.plugins.ntfy.urllib.request.urlopen") as mock_urlopen:
        mock_resp = MagicMock()
        mock_resp.status = 200
        mock_resp.__enter__ = MagicMock(return_value=mock_resp)
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_resp

        config = {"notify_backend": "ntfy", "ntfy_topic": "t"}
        notify.send(config, "msg", delay="30min")
        req = mock_urlopen.call_args[0][0]
        assert req.get_header("At") == "30min"


def test_send_ntfy_failure():
    with patch("board_md.plugins.ntfy.urllib.request.urlopen") as mock_urlopen:
        mock_urlopen.side_effect = OSError("network error")
        config = {"notify_backend": "ntfy", "ntfy_topic": "t"}
        result = notify.send(config, "msg")
        assert result is False


def test_send_feishu():
    """feishu plugin sends correct JSON payload."""
    with patch("board_md.plugins.feishu.urllib.request.urlopen") as mock_urlopen:
        mock_resp = MagicMock()
        mock_resp.read.return_value = b'{"code": 0}'
        mock_resp.__enter__ = MagicMock(return_value=mock_resp)
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_resp

        config = {
            "notify_backend": "feishu",
            "feishu_webhook": "https://open.feishu.cn/open-apis/bot/v2/hook/xxx",
        }
        result = notify.send(config, "task due!")
        assert result is True

        req = mock_urlopen.call_args[0][0]
        assert req.get_header("Content-type") == "application/json"


def test_send_feishu_failure():
    with patch("board_md.plugins.feishu.urllib.request.urlopen") as mock_urlopen:
        mock_urlopen.side_effect = OSError("connection refused")
        config = {
            "notify_backend": "feishu",
            "feishu_webhook": "https://open.feishu.cn/open-apis/bot/v2/hook/xxx",
        }
        result = notify.send(config, "msg")
        assert result is False


def test_send_missing_config():
    """Should return False when required config is missing."""
    assert notify.send({"notify_backend": "ntfy"}, "msg") is False
    assert notify.send({"notify_backend": "feishu"}, "msg") is False


def test_send_unknown_backend():
    assert notify.send({"notify_backend": "telegram"}, "msg") is False
