from typing import Any

from supabase import Client, create_client


class SupabaseService:
    """Thin wrapper around supabase-py for chat persistence + auth helpers.

    Holds a single client instance bound to the service role key, since the
    backend trusts itself. Frontend code uses the anon key from a separate
    client and lets RLS protect rows.
    """

    def __init__(self, url: str, service_key: str):
        self._client: Client = create_client(url, service_key)

    @property
    def client(self) -> Client:
        return self._client

    # --- chat sessions / messages ---

    def list_sessions(self, user_id: str, limit: int = 20) -> list[dict[str, Any]]:
        res = (
            self._client.table("chat_sessions")
            .select("*")
            .eq("user_id", user_id)
            .order("updated_at", desc=True)
            .limit(limit)
            .execute()
        )
        return res.data or []

    def create_session(self, user_id: str, title: str) -> dict[str, Any]:
        res = (
            self._client.table("chat_sessions")
            .insert({"user_id": user_id, "title": title})
            .execute()
        )
        return res.data[0] if res.data else {}

    def append_message(
        self, session_id: str, role: str, content: str, metadata: dict | None = None
    ) -> dict[str, Any]:
        res = (
            self._client.table("chat_messages")
            .insert(
                {
                    "session_id": session_id,
                    "role": role,
                    "content": content,
                    "metadata": metadata or {},
                }
            )
            .execute()
        )
        return res.data[0] if res.data else {}

    def get_history(self, session_id: str) -> list[dict[str, Any]]:
        res = (
            self._client.table("chat_messages")
            .select("*")
            .eq("session_id", session_id)
            .order("created_at")
            .execute()
        )
        return res.data or []

    # --- agent runs (telemetry) ---

    def record_agent_run(
        self,
        session_id: str | None,
        task: str,
        status: str,
        result: dict | None = None,
        provider: str | None = None,
        latency_ms: float | None = None,
    ) -> dict[str, Any]:
        res = (
            self._client.table("agent_runs")
            .insert(
                {
                    "session_id": session_id,
                    "task": task,
                    "status": status,
                    "result": result or {},
                    "provider": provider,
                    "latency_ms": latency_ms,
                }
            )
            .execute()
        )
        return res.data[0] if res.data else {}
