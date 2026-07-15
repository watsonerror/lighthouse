"""In-memory session persistence (spec 6: state decoupling).

Agents are stateless; all session state lives in the harness. This is the reference in-memory
store — a production harness would back it with a database.
"""

from __future__ import annotations

from .ledger import ContextLedger


class SessionStore:
    """Persists :class:`ContextLedger` state keyed by session id."""

    def __init__(self) -> None:
        self._sessions: dict[str, ContextLedger] = {}

    def save(self, ledger: ContextLedger) -> None:
        self._sessions[ledger.session_id] = ledger

    def get(self, session_id: str) -> ContextLedger:
        return self._sessions[session_id]

    def has(self, session_id: str) -> bool:
        return session_id in self._sessions

    def all(self) -> list[ContextLedger]:
        return list(self._sessions.values())
