from __future__ import annotations

import os
import subprocess
import webbrowser
from pathlib import Path
from urllib.parse import quote_plus

from ..config import AssistantConfig
from ..models import AssistantReply, IntentName, IntentResult


class WindowsActionExecutor:
    def __init__(self, config: AssistantConfig) -> None:
        self._config = config

    def execute(self, intent: IntentResult) -> AssistantReply:
        if intent.name == IntentName.OPEN_APP:
            return self._open_app(intent.params.get("app", ""))
        if intent.name == IntentName.SEARCH_GOOGLE:
            query = quote_plus(intent.params.get("query", ""))
            return self._open_url(
                f"https://www.google.com/search?q={query}",
                "Busqueda en Google abierta",
            )
        if intent.name == IntentName.SEARCH_YOUTUBE:
            query = quote_plus(intent.params.get("query", ""))
            return self._open_url(
                f"https://www.youtube.com/results?search_query={query}",
                "Busqueda en YouTube abierta",
            )
        if intent.name == IntentName.PLAY_SPOTIFY:
            query = intent.params.get("query", "")
            return self._open_url(
                f"https://open.spotify.com/search/{quote_plus(query)}",
                "Busqueda de Spotify abierta",
            )
        if intent.name == IntentName.MEDIA_PAUSE:
            return self._media_key("playpause")
        if intent.name == IntentName.MEDIA_NEXT:
            return self._media_key("nexttrack")
        if intent.name == IntentName.OPEN_FOLDER:
            return self._open_folder(intent.params.get("folder", ""))

        return AssistantReply(text="No tengo una accion local para ese comando.", source="actions")

    def _open_app(self, app_name: str) -> AssistantReply:
        key = app_name.lower().strip()
        command = self._config.app_whitelist.get(key)
        if not command:
            return AssistantReply(
                text=f"La app '{app_name}' no esta en la lista blanca.", source="actions"
            )

        if self._config.dry_run:
            return AssistantReply(text=f"[dry-run] Abriria: {command}", source="actions")

        subprocess.Popen(command, shell=True)
        return AssistantReply(text=f"Abriendo {app_name}.", source="actions")

    def _open_folder(self, folder_name: str) -> AssistantReply:
        key = folder_name.lower().strip()
        folder = self._config.folder_whitelist.get(key)
        if not folder:
            return AssistantReply(
                text=f"La carpeta '{folder_name}' no esta en la lista blanca.", source="actions"
            )

        path = Path(os.path.expandvars(folder)).expanduser()
        if not path.exists():
            return AssistantReply(text=f"La ruta no existe: {path}", source="actions")

        if self._config.dry_run:
            return AssistantReply(text=f"[dry-run] Abriria carpeta: {path}", source="actions")

        subprocess.Popen(["explorer", str(path)])
        return AssistantReply(text=f"Abriendo carpeta {folder_name}.", source="actions")

    def _media_key(self, key: str) -> AssistantReply:
        # PowerShell call to send media key events on Windows.
        script = (
            "Add-Type -AssemblyName System.Windows.Forms;"
            "$wshell = New-Object -ComObject wscript.shell;"
            "$wshell.SendKeys('{"
            + ("MEDIA_PLAY_PAUSE" if key == "playpause" else "MEDIA_NEXT")
            + "}')"
        )

        if self._config.dry_run:
            return AssistantReply(
                text=f"[dry-run] Enviaria tecla multimedia: {key}", source="actions"
            )

        subprocess.run(["powershell", "-NoProfile", "-Command", script], check=False)
        return AssistantReply(text="Comando multimedia enviado.", source="actions")

    def _open_url(self, url: str, message: str) -> AssistantReply:
        if self._config.dry_run:
            return AssistantReply(text=f"[dry-run] Abriria URL: {url}", source="actions")

        webbrowser.open(url)
        return AssistantReply(text=message, source="actions")
