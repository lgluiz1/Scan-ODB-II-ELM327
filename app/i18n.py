"""Internationalization (i18n) helper for ODBScan II desktop application.
Automatically detects system language (Portuguese or English).
"""
import locale
from typing import Dict

# Dictionary of translations
STRINGS: Dict[str, Dict[str, str]] = {
    "app_title": {
        "pt": "⚡ ODBScan II",
        "en": "⚡ ODBScan II",
    },
    "app_desc": {
        "pt": "Scanner Automotivo Universal (SAE J1979 / CAN)",
        "en": "Universal Automotive Scanner (SAE J1979 / CAN)",
    },
    "port": {
        "pt": "Porta:",
        "en": "Port:",
    },
    "baudrate": {
        "pt": "Velocidade:",
        "en": "Baudrate:",
    },
    "connect": {
        "pt": "🔌 CONECTAR",
        "en": "🔌 CONNECT",
    },
    "disconnect": {
        "pt": "⏹️ DESCONECTAR",
        "en": "⏹️ DISCONNECT",
    },
    "status_adapter": {
        "pt": "Adaptador ELM327",
        "en": "ELM327 Adapter",
    },
    "status_ecu": {
        "pt": "Comunicação ECU",
        "en": "ECU Comm",
    },
    "status_battery": {
        "pt": "Tensão Bateria",
        "en": "Battery Voltage",
    },
    "disconnected": {
        "pt": "Desconectado",
        "en": "Disconnected",
    },
    "connected": {
        "pt": "Conectado",
        "en": "Connected",
    },
    "tab_dtc": {
        "pt": "🔍 Leitor de Falhas (DTC)",
        "en": "🔍 Fault Codes (DTC)",
    },
    "tab_lambda": {
        "pt": "📈 Osciloscópio Lambda (O2)",
        "en": "📈 Lambda (O2) Scope",
    },
    "tab_blackbox": {
        "pt": "🚗 Telemetria & Viagem",
        "en": "🚗 Telemetry & Trip",
    },
    "tab_patterns": {
        "pt": "📊 Padrões Operacionais",
        "en": "📊 Operating Patterns",
    },
    "tab_history": {
        "pt": "📁 Histórico DTC",
        "en": "📁 DTC History",
    },
    "tab_trips": {
        "pt": "🗺️ Viagens Salvas",
        "en": "🗺️ Saved Trips",
    },
    "tab_events": {
        "pt": "⚠️ Eventos Críticos",
        "en": "⚠️ Critical Events",
    },
    "tab_terminal": {
        "pt": "💻 Terminal OBD2",
        "en": "💻 OBD2 Terminal",
    },
    "btn_update": {
        "pt": "🔄 Atualizações",
        "en": "🔄 Updates",
    },
    "developer_credit": {
        "pt": "👨‍💻 Desenvolvido e criado por Luiz Gustavo",
        "en": "👨‍💻 Developed and created by Luiz Gustavo",
    },
    "ready_to_connect": {
        "pt": "Pronto para conectar ao adaptador ELM327.",
        "en": "Ready to connect to ELM327 adapter.",
    },
}

_CURRENT_LANG = None


def get_current_language() -> str:
    """Detects system language: 'en' or 'pt'."""
    global _CURRENT_LANG
    if _CURRENT_LANG is not None:
        return _CURRENT_LANG

    try:
        loc = locale.getlocale()[0]
        if not loc:
            import os
            loc = os.environ.get("LANG", "") or os.environ.get("LANGUAGE", "")
        if loc and loc.lower().startswith("en"):
            _CURRENT_LANG = "en"
            return "en"
    except Exception:
        pass

    _CURRENT_LANG = "pt"
    return "pt"


def set_current_language(lang: str):
    global _CURRENT_LANG
    _CURRENT_LANG = "en" if lang.startswith("en") else "pt"


def tr(key: str, default: str = "") -> str:
    """Translates a key into current language string."""
    lang = get_current_language()
    item = STRINGS.get(key)
    if not item:
        return default or key
    return item.get(lang, item.get("pt", default or key))
