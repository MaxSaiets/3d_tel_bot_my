from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

import httpx

from app.config import Settings


@dataclass
class NovaPoshtaCreateTtnInput:
    city_ref: str
    warehouse_ref: str
    recipient_name: str
    recipient_phone: str
    cost: float
    weight: float = 1.0
    seats_amount: int = 1
    description: str = "Order from Telegram bot"


class NovaPoshtaClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    async def _request(self, model_name: str, called_method: str, method_properties: dict) -> dict:
        if not self.settings.nova_poshta_api_key:
            raise ValueError("NOVA_POSHTA_API_KEY is not configured")

        payload = {
            "apiKey": self.settings.nova_poshta_api_key,
            "modelName": model_name,
            "calledMethod": called_method,
            "methodProperties": method_properties,
        }
        async with httpx.AsyncClient(timeout=self.settings.crm_timeout_seconds) as client:
            response = await client.post(self.settings.nova_poshta_api_url, json=payload)
            response.raise_for_status()
            data = response.json()

        if not data.get("success"):
            errors = data.get("errors") or ["Nova Poshta request failed"]
            raise ValueError("; ".join(errors))
        return data

    async def search_cities(self, query: str, limit: int = 20) -> list[dict]:
        data = await self._request(
            "Address",
            "searchSettlements",
            {"CityName": query, "Limit": str(limit), "Page": "1"},
        )
        addresses = data.get("data", [{}])[0].get("Addresses", [])
        return addresses

    async def search_warehouses(self, city_ref: str, query: str | None = None, limit: int = 20) -> list[dict]:
        method_props: dict[str, str] = {"CityRef": city_ref, "Limit": str(limit), "Page": "1", "Language": "UA"}
        if query:
            method_props["FindByString"] = query
        data = await self._request("AddressGeneral", "getWarehouses", method_props)
        return data.get("data", [])

    async def create_ttn(self, ttn_input: NovaPoshtaCreateTtnInput) -> dict:
        required = [
            self.settings.np_sender_ref,
            self.settings.np_sender_contact_ref,
            self.settings.np_sender_address_ref,
            self.settings.np_sender_city_ref,
            self.settings.np_sender_phone,
        ]
        if any(not value for value in required):
            raise ValueError(
                "NP sender settings are missing. Configure NP_SENDER_REF, NP_SENDER_CONTACT_REF, "
                "NP_SENDER_ADDRESS_REF, NP_SENDER_CITY_REF, NP_SENDER_PHONE."
            )

        recipient_contact = await self._request(
            "CounterpartyGeneral",
            "save",
            {
                "FirstName": ttn_input.recipient_name,
                "LastName": ttn_input.recipient_name,
                "Phone": ttn_input.recipient_phone,
                "CounterpartyType": "PrivatePerson",
                "CounterpartyProperty": "Recipient",
            },
        )
        recipient_ref = recipient_contact["data"][0]["Ref"]

        recipient_contact_person = await self._request(
            "CounterpartyGeneral",
            "getCounterpartyContactPersons",
            {"Ref": recipient_ref, "Page": "1"},
        )
        recipient_contact_ref = recipient_contact_person["data"][0]["Ref"]

        doc = await self._request(
            "InternetDocument",
            "save",
            {
                "PayerType": "Recipient",
                "PaymentMethod": "Cash",
                "DateTime": datetime.now().strftime("%d.%m.%Y"),
                "CargoType": "Cargo",
                "Weight": str(ttn_input.weight),
                "ServiceType": "WarehouseWarehouse",
                "SeatsAmount": str(ttn_input.seats_amount),
                "Description": ttn_input.description,
                "Cost": str(ttn_input.cost),
                "CitySender": self.settings.np_sender_city_ref,
                "Sender": self.settings.np_sender_ref,
                "SenderAddress": self.settings.np_sender_address_ref,
                "ContactSender": self.settings.np_sender_contact_ref,
                "SendersPhone": self.settings.np_sender_phone,
                "CityRecipient": ttn_input.city_ref,
                "Recipient": recipient_ref,
                "RecipientAddress": ttn_input.warehouse_ref,
                "ContactRecipient": recipient_contact_ref,
                "RecipientsPhone": ttn_input.recipient_phone,
            },
        )
        return doc.get("data", [{}])[0]
