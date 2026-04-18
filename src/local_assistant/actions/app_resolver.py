from __future__ import annotations

import re
from difflib import SequenceMatcher


class AppResolver:
    _STOPWORDS = {
        "app",
        "aplicacion",
        "programa",
        "el",
        "la",
        "ahora",
        "por",
        "favor",
        "abre",
        "abrir",
        "inicia",
        "iniciar",
        "ejecuta",
    }

    _PHONETIC_ALIASES = {
        # Common Spanish STT confusions for "chrome" in live speech.
        "kron": "chrome",
        "cron": "chrome",
        "crom": "chrome",
        "krom": "chrome",
        "aurekron": "chrome",
        "aurekrom": "chrome",
        "aurecron": "chrome",
    }

    def __init__(self, whitelist: dict[str, str], aliases: dict[str, str]) -> None:
        self._whitelist = whitelist
        self._aliases = aliases

    def normalize(self, spoken_text: str) -> str:
        cleaned = spoken_text.lower().strip()
        cleaned = re.sub(r"[^\w\s-]", " ", cleaned)
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        tokens = [token for token in cleaned.split(" ") if token and token not in self._STOPWORDS]
        return " ".join(tokens).strip()

    def resolve(self, spoken_app: str) -> str | None:
        normalized_spoken = self.normalize(spoken_app)
        if not normalized_spoken:
            return None

        normalized_whitelist: dict[str, str] = {
            self.normalize(key): key for key in self._whitelist
        }

        alias_candidate = self._PHONETIC_ALIASES.get(normalized_spoken)
        if alias_candidate and alias_candidate in normalized_whitelist:
            return normalized_whitelist[alias_candidate]

        if normalized_spoken in normalized_whitelist:
            return normalized_whitelist[normalized_spoken]

        if normalized_spoken in self._whitelist:
            return normalized_spoken

        normalized_aliases: dict[str, str] = {
            self.normalize(k): self.normalize(v) for k, v in self._aliases.items()
        }
        alias_target = normalized_aliases.get(normalized_spoken)
        if alias_target and alias_target in normalized_whitelist:
            return normalized_whitelist[alias_target]

        spoken_tokens = set(normalized_spoken.split())
        best_key: str | None = None
        best_score = 0.0

        for normalized_key, original_key in normalized_whitelist.items():
            key_tokens = set(normalized_key.split())
            if not key_tokens:
                continue

            overlap = len(spoken_tokens & key_tokens) / len(key_tokens)
            subset_bonus = 0.2 if key_tokens.issubset(spoken_tokens) else 0.0
            similarity = SequenceMatcher(None, normalized_spoken, normalized_key).ratio()
            score = 0.6 * similarity + 0.4 * overlap + subset_bonus

            if score > best_score:
                best_score = score
                best_key = original_key

        if best_key is not None and best_score >= 0.7:
            return best_key

        # Fallback for single-token typos where token overlap is naturally low.
        if len(spoken_tokens) == 1:
            best_key = None
            best_similarity = 0.0
            for normalized_key, original_key in normalized_whitelist.items():
                similarity = SequenceMatcher(None, normalized_spoken, normalized_key).ratio()
                if similarity > best_similarity:
                    best_similarity = similarity
                    best_key = original_key
            if best_key is not None and best_similarity >= 0.75:
                return best_key

        return None
