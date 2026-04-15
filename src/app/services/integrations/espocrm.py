from __future__ import annotations

import httpx

from app.config import Settings


class EspoCrmClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    @property
    def _headers(self) -> dict[str, str]:
        return {
            "Content-Type": "application/json",
            "X-Api-Key": self.settings.espocrm_api_key,
        }

    async def create_order_entity(self, payload: dict) -> dict:
        endpoint = f"{self.settings.espocrm_base_url.rstrip('/')}/api/v1/{self.settings.espocrm_order_entity}"
        order = payload["order"]
        customer = order["customer"]
        items_text = ", ".join([f'{item["sku"]} x{item["qty"]}' for item in order["items"]])
        np_data = payload.get("nova_poshta", {})

        description_lines = [
            f"Order UUID: {order['order_uuid']}",
            f"Source: {order.get('source_code') or '-'}",
            f"Customer: {customer['name']}",
            f"Phone: {customer['phone']}",
            f"Delivery: {customer['delivery_info']}",
            f"Items: {items_text}",
            f"Total: {order['total_amount']}",
        ]
        if np_data:
            description_lines.append(
                f"Nova Poshta: {np_data.get('city_name', '-')}, {np_data.get('warehouse_name', '-')}"
            )
            if np_data.get("tracking_number"):
                description_lines.append(f"TTN: {np_data['tracking_number']}")

        body = {
            "name": f"Order {order['order_uuid']}",
            "status": self.settings.espocrm_default_status,
            "description": "\n".join(description_lines),
        }

        async with httpx.AsyncClient(timeout=self.settings.crm_timeout_seconds) as client:
            response = await client.post(endpoint, headers=self._headers, json=body)
            response.raise_for_status()
            return response.json()

