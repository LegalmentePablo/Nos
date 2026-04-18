from local_assistant.intent_router import IntentRouter
from local_assistant.models import IntentName


def test_open_app_route() -> None:
    router = IntentRouter()

    result = router.route("abre discord")

    assert result.name == IntentName.OPEN_APP
    assert result.params["app"].lower() == "discord"
    assert result.confidence >= 0.9


def test_google_route() -> None:
    router = IntentRouter()

    result = router.route("busca en google mejores teclados")

    assert result.name == IntentName.SEARCH_GOOGLE
    assert "mejores teclados" in result.params["query"].lower()


def test_unknown_route() -> None:
    router = IntentRouter()

    result = router.route("organiza mi tarde de hoy")

    assert result.name == IntentName.UNKNOWN
    assert result.confidence == 0.0
