from unittest.mock import Mock, patch

import pytest

from local_assistant.llm.ollama_client import OllamaClient


def test_chat_success_parses_response() -> None:
    client = OllamaClient(host="http://localhost:11434", model="qwen")

    fake_response = Mock()
    fake_response.raise_for_status = Mock()
    fake_response.json = Mock(return_value={"response": " hola "})

    with patch(
        "local_assistant.llm.ollama_client.requests.post", return_value=fake_response
    ) as post:
        reply = client.chat("test")

    assert reply == "hola"
    post.assert_called_once()


def test_chat_raises_on_http_error() -> None:
    client = OllamaClient(host="http://localhost:11434", model="qwen")

    fake_response = Mock()
    fake_response.raise_for_status = Mock(side_effect=RuntimeError("boom"))

    with patch("local_assistant.llm.ollama_client.requests.post", return_value=fake_response):
        with pytest.raises(RuntimeError):
            client.chat("test")
