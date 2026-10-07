"""UI Widgets package.
"""
from ui.widgets.status_badge import StatusBadge
from ui.widgets.dtc_card import DTCCard
from ui.widgets.terminal_view import TerminalView
from ui.widgets.history_view import HistoryView
from ui.widgets.blackbox_view import BlackboxView
from ui.widgets.trip_history_view import TripHistoryView
from ui.widgets.events_view import EventsView
from ui.widgets.patterns_view import PatternsView
from ui.widgets.lambda_view import LambdaView

__all__ = [
    "StatusBadge",
    "DTCCard",
    "TerminalView",
    "HistoryView",
    "BlackboxView",
    "TripHistoryView",
    "EventsView",
    "PatternsView",
    "LambdaView"
]
