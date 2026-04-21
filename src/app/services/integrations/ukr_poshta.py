from __future__ import annotations

import httpx

from app.config import Settings


class UkrPoshtaAddressClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    @property
    def _headers(self) -> dict[str, str]:
        if not self.settings.ukr_poshta_bearer:
            raise ValueError("UKR_POSHTA_BEARER is not configured")
        return {
            "Authorization": f"Bearer {self.settings.ukr_poshta_bearer}",
            "Accept": "application/json",
        }

    async def _request(self, path: str, params: dict[str, str]) -> dict:
        async with httpx.AsyncClient(timeout=self.settings.crm_timeout_seconds) as client:
            response = await client.get(
                f"{self.settings.ukr_poshta_api_url.rstrip('/')}/{path.lstrip('/')}",
                params=params,
                headers=self._headers,
            )
            response.raise_for_status()
            return response.json()

    @staticmethod
    def _extract_entries(payload: dict) -> list[dict]:
        entries = payload.get("Entries") or payload.get("entries") or {}
        items = entries.get("Entry") or entries.get("entry") or []
        if isinstance(items, dict):
            return [items]
        if isinstance(items, list):
            return items
        return []

    async def search_postoffices(self, postcode: str, query: str | None = None) -> list[dict]:
        payload = await self._request(
            "get_postoffices_by_postcode_cityid_cityvpzid",
            {"postcode": postcode},
        )
        items = self._extract_entries(payload)

        normalized: list[dict] = []
        search = (query or "").strip().lower()
        for item in items:
            office = {
                "id": str(item.get("POSTOFFICE_ID") or item.get("ID") or ""),
                "postcode": str(item.get("POSTCODE") or item.get("POSTINDEX") or postcode),
                "city": str(item.get("CITY_UA_VPZ") or item.get("CITY_UA") or ""),
                "name": str(item.get("POSTOFFICE_UA") or item.get("PO_SHORT") or ""),
                "address": str(item.get("STREET_UA_VPZ") or item.get("ADDRESS") or ""),
                "phone": str(item.get("PHONE") or ""),
                "type": str(item.get("TYPE_LONG") or item.get("TYPE_ACRONYM") or ""),
            }

            haystack = " ".join(
                [
                    office["postcode"],
                    office["city"],
                    office["name"],
                    office["address"],
                    office["type"],
                ]
            ).lower()
            if search and search not in haystack:
                continue
            normalized.append(office)

        return normalized
