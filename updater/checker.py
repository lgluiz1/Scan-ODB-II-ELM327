"""GitHub Releases version checker, downloader, and in-place executable replacement.
"""
import os
import sys
import json
import re
import tempfile
import subprocess
import urllib.request
import urllib.error
from typing import Optional, Dict, Any, Tuple, Callable

from app.config import APP_VERSION, APP_NAME, GITHUB_RELEASES_API
from utils.logger import tech_logger


def parse_version_tuple(v_str: str) -> Tuple[int, ...]:
    """Parse a version string like 'v1.2.3' or '1.2.0' into an integer tuple (1, 2, 3)."""
    if not v_str:
        return (0, 0, 0)
    cleaned = re.sub(r'^[^\d]*', '', v_str.strip())
    parts = []
    for chunk in cleaned.split('.'):
        digits = re.match(r'^\d+', chunk)
        if digits:
            parts.append(int(digits.group(0)))
        else:
            break
    while len(parts) < 3:
        parts.append(0)
    return tuple(parts)


def check_for_updates(timeout_sec: float = 4.0) -> Optional[Dict[str, Any]]:
    """
    Queries GitHub Releases API to check for a newer version than APP_VERSION.
    Returns update dictionary if newer version is found, or None if up to date / error.
    """
    tech_logger.info(f"[UPDATER] Verificando atualizações em {GITHUB_RELEASES_API}...")
    try:
        req = urllib.request.Request(
            GITHUB_RELEASES_API,
            headers={
                "User-Agent": f"{APP_NAME}-AutoUpdater/{APP_VERSION}",
                "Accept": "application/vnd.github.v3+json"
            }
        )
        with urllib.request.urlopen(req, timeout=timeout_sec) as resp:
            if resp.status != 200:
                tech_logger.info(f"[UPDATER] Resposta da API: HTTP {resp.status}")
                return None
            data = json.loads(resp.read().decode("utf-8"))

        remote_tag = data.get("tag_name", "")
        remote_tuple = parse_version_tuple(remote_tag)
        local_tuple = parse_version_tuple(APP_VERSION)

        tech_logger.info(f"[UPDATER] Versão local: {APP_VERSION} ({local_tuple}), Versão remota: {remote_tag} ({remote_tuple})")

        if remote_tuple > local_tuple:
            # Look for an executable asset (.exe)
            download_url = None
            asset_name = "OBDScanner.exe"
            asset_size = 0

            for asset in data.get("assets", []):
                name = asset.get("name", "")
                if name.lower().endswith(".exe"):
                    download_url = asset.get("browser_download_url")
                    asset_name = name
                    asset_size = asset.get("size", 0)
                    break

            return {
                "has_update": True,
                "remote_version": remote_tag,
                "current_version": f"v{APP_VERSION}",
                "release_name": data.get("name") or remote_tag,
                "release_notes": data.get("body") or "Atualização com correções e novas funcionalidades.",
                "html_url": data.get("html_url", ""),
                "download_url": download_url,
                "asset_name": asset_name,
                "asset_size": asset_size,
            }
        else:
            tech_logger.info("[UPDATER] Aplicativo já está na versão mais recente.")
            return {
                "has_update": False,
                "remote_version": remote_tag or f"v{APP_VERSION}",
                "current_version": f"v{APP_VERSION}",
                "release_name": data.get("name", ""),
                "release_notes": data.get("body", ""),
                "html_url": data.get("html_url", "")
            }

    except urllib.error.HTTPError as e:
        if e.code == 404:
            tech_logger.info("[UPDATER] Nenhuma release pública encontrada no GitHub ainda.")
        else:
            tech_logger.warning(f"[UPDATER] Erro HTTP ao verificar release: {e.code} {e.reason}")
        return None
    except Exception as e:
        tech_logger.warning(f"[UPDATER] Falha ao verificar atualizações: {str(e)}")
        return None


def download_file(url: str, dest_path: str, progress_callback: Optional[Callable[[int, int], None]] = None) -> bool:
    """
    Downloads file from URL to dest_path in chunks, invoking progress_callback(received, total).
    """
    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": f"{APP_NAME}-AutoUpdater/{APP_VERSION}"}
        )
        with urllib.request.urlopen(req, timeout=30.0) as resp:
            total_size = int(resp.headers.get("content-length", 0))
            received = 0
            chunk_size = 64 * 1024  # 64 KB

            with open(dest_path, "wb") as f:
                while True:
                    chunk = resp.read(chunk_size)
                    if not chunk:
                        break
                    f.write(chunk)
                    received += len(chunk)
                    if progress_callback:
                        progress_callback(received, total_size)
        return True
    except Exception as e:
        tech_logger.error(f"[UPDATER] Erro no download da atualização: {str(e)}")
        return False


def apply_update_and_restart(new_binary_path: str) -> Tuple[bool, str]:
    """
    Creates a helper batch script to replace the current executable and relaunch it.
    Returns (True, "Restarting...") if standalone, or (False, "Running from source") if Python.
    """
    is_frozen = getattr(sys, "frozen", False)
    if not is_frozen:
        return False, "O aplicativo está rodando a partir do código-fonte Python. Para atualizar, faça 'git pull' ou baixe o novo .exe."

    current_exe = sys.executable
    if not os.path.exists(current_exe):
        return False, f"Executável de destino não localizado: {current_exe}"

    temp_dir = tempfile.gettempdir()
    bat_path = os.path.join(temp_dir, "obdscanner_updater.bat")

    # Batch script waits for current PID to terminate, overwrites exe, relaunches and self-destructs
    bat_content = f"""@echo off
setlocal
echo Aguardando fechamento do OBD Scanner...
timeout /t 1 /nobreak > nul

for /l %%i in (1, 1, 15) do (
    copy /y "{new_binary_path}" "{current_exe}" > nul 2>&1
    if not errorlevel 1 goto launch
    timeout /t 1 /nobreak > nul
)

:launch
del /f /q "{new_binary_path}" > nul 2>&1
start "" "{current_exe}"
del /f /q "%~f0" > nul 2>&1
exit
"""

    try:
        with open(bat_path, "w", encoding="utf-8") as f:
            f.write(bat_content)

        tech_logger.info(f"[UPDATER] Lançando script de substituição: {bat_path}")

        # CREATE_NO_WINDOW = 0x08000000 on Windows
        creationflags = 0x08000000 if sys.platform == "win32" else 0
        subprocess.Popen(["cmd.exe", "/c", bat_path], creationflags=creationflags)
        return True, "Atualização aplicada com sucesso. Reiniciando o aplicativo..."
    except Exception as e:
        tech_logger.error(f"[UPDATER] Falha ao criar/disparar script de atualização: {str(e)}")
        return False, f"Falha ao aplicar atualização: {str(e)}"
