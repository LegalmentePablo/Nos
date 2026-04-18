from local_assistant.actions.app_resolver import AppResolver


def _resolver() -> AppResolver:
    whitelist = {
        "discord": "start discord",
        "chrome": "start chrome",
        "visual studio code": "start code",
    }
    aliases = {
        "google chorme": "chrome",
    }
    return AppResolver(whitelist, aliases)


def test_exact_match() -> None:
    resolver = _resolver()
    assert resolver.resolve("discord") == "discord"


def test_alias_match() -> None:
    resolver = _resolver()
    assert resolver.resolve("google chorme") == "chrome"


def test_subset_inference() -> None:
    resolver = _resolver()
    assert resolver.resolve("ahora google chrome") == "chrome"


def test_typo_inference() -> None:
    resolver = _resolver()
    assert resolver.resolve("chorme") == "chrome"


def test_command_wrapper_is_ignored() -> None:
    resolver = _resolver()
    assert resolver.resolve("por favor abre chrome") == "chrome"


def test_streaming_phonetic_confusion_still_resolves() -> None:
    resolver = _resolver()
    assert resolver.resolve("Aurekron") == "chrome"


def test_punctuation_normalization() -> None:
    resolver = _resolver()
    assert resolver.resolve("Visual Studio Code.") == "visual studio code"
