"""Thin Supabase REST (PostgREST) client wrapper.

We deliberately avoid a heavy SDK. PostgREST over httpx covers select/insert/upsert/
update, which is all the jobs need. The service_role key is used server-side and
bypasses RLS.
"""

from __future__ import annotations

from typing import Any

import httpx

from app.config import get_settings


class SupabaseClient:
    def __init__(self) -> None:
        settings = get_settings()
        self._base = settings.supabase_rest_url
        key = settings.supabase_service_role_key
        self._headers = {
            "apikey": key,
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        }
        self._client = httpx.Client(
            headers=self._headers, timeout=settings.request_timeout_seconds
        )

    # ---- reads ----
    def select(
        self,
        table: str,
        columns: str = "*",
        filters: dict[str, str] | None = None,
        limit: int | None = None,
    ) -> list[dict[str, Any]]:
        params: dict[str, Any] = {"select": columns}
        if filters:
            params.update(filters)
        if limit is not None:
            params["limit"] = str(limit)
        resp = self._client.get(f"{self._base}/{table}", params=params)
        resp.raise_for_status()
        return resp.json()

    # ---- writes ----
    def insert(self, table: str, rows: list[dict[str, Any]] | dict[str, Any]) -> list[dict]:
        resp = self._client.post(
            f"{self._base}/{table}",
            json=rows,
            headers={"Prefer": "return=representation"},
        )
        resp.raise_for_status()
        return resp.json()

    def upsert(
        self,
        table: str,
        rows: list[dict[str, Any]] | dict[str, Any],
        on_conflict: str,
    ) -> list[dict]:
        resp = self._client.post(
            f"{self._base}/{table}",
            params={"on_conflict": on_conflict},
            json=rows,
            headers={"Prefer": "return=representation,resolution=merge-duplicates"},
        )
        resp.raise_for_status()
        return resp.json()

    def update(
        self, table: str, patch: dict[str, Any], filters: dict[str, str]
    ) -> list[dict]:
        resp = self._client.patch(
            f"{self._base}/{table}",
            params=filters,
            json=patch,
            headers={"Prefer": "return=representation"},
        )
        resp.raise_for_status()
        return resp.json()

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "SupabaseClient":
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()
