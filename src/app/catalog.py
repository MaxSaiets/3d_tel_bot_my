from __future__ import annotations

from decimal import Decimal
from typing import TypedDict


class ProductSpec(TypedDict):
    sku: str
    title: str
    short_title: str
    subtitle: str
    description: str
    price: str
    unit_label: str
    badges: list[str]
    features: list[str]
    accent: str
    images: list[str]


PRODUCTS: dict[str, ProductSpec] = {
    "signal_fishing": {
        "sku": "signal_fishing",
        "title": "Сигналізатор клювання механічний",
        "short_title": "Сигналізатор клювання",
        "subtitle": "Компактний рибальський аксесуар для вудлищ і фідера",
        "description": (
            "Механічний сигналізатор для рибалки. Підходить для фідерної й донної ловлі, "
            "має надійне різьбове кріплення, помітний під час клювання та простий у використанні."
        ),
        "price": "120.00",
        "unit_label": "за шт.",
        "badges": ["Хіт продажів", "Оплата при отриманні"],
        "features": [
            "Регульоване навантаження",
            "Стандартне різьбове кріплення",
            "Помітний рух навіть при делікатному клюванні",
            "Підходить для денного і вечірнього використання",
        ],
        "accent": "#14532d",
        "images": [
            "https://ireland.apollo.olxcdn.com:443/v1/files/udyvz394go613-UA/image",
            "https://ireland.apollo.olxcdn.com:443/v1/files/zqaxpvx3vtku2-UA/image",
            "https://ireland.apollo.olxcdn.com:443/v1/files/n5t141bpaeb21-UA/image",
        ],
    },
    "hoodie_black": {
        "sku": "hoodie_black",
        "title": "Худі Black",
        "short_title": "Худі Black",
        "subtitle": "Базове тепле худі для щоденного носіння",
        "description": (
            "Практичне худі з м'якого матеріалу на щодень. Добре підходить для прохолодної погоди, "
            "риболовлі, поїздок і casual-стилю."
        ),
        "price": "890.00",
        "unit_label": "за шт.",
        "badges": ["Новинка", "Універсальний подарунок"],
        "features": [
            "Класичний чорний колір",
            "Капюшон і містка кишеня",
            "Комфортний крій",
            "Підійде для щоденного використання",
        ],
        "accent": "#1f2937",
        "images": [],
    },
    "cap_white": {
        "sku": "cap_white",
        "title": "Кепка White",
        "short_title": "Кепка White",
        "subtitle": "Легка кепка для сонячної погоди та виїздів на природу",
        "description": (
            "Біла кепка для щоденного носіння, прогулянок і риболовлі. Легка, практична та добре "
            "поєднується з базовим одягом."
        ),
        "price": "320.00",
        "unit_label": "за шт.",
        "badges": ["Літній фаворит", "Легка посадка"],
        "features": [
            "Світлий універсальний колір",
            "Комфортна посадка",
            "Захист від сонця",
            "Підходить для активного відпочинку",
        ],
        "accent": "#9a3412",
        "images": [],
    },
    "sticker_pack": {
        "sku": "sticker_pack",
        "title": "Набір стікерів",
        "short_title": "Стікери",
        "subtitle": "Комплект декоративних стікерів для коробок, тубусів і подарунків",
        "description": (
            "Невеликий набір стікерів для пакування, подарунків або персоналізації речей. Зручно "
            "додавати до основного замовлення як недорогу позицію."
        ),
        "price": "90.00",
        "unit_label": "за набір",
        "badges": ["Додайте до замовлення", "Бюджетний подарунок"],
        "features": [
            "Зручне доповнення до основного товару",
            "Підходить для подарункового пакування",
            "Легка вага",
            "Приємна дрібниця до замовлення",
        ],
        "accent": "#7c2d12",
        "images": [],
    },
}


def get_product(sku: str) -> ProductSpec | None:
    return PRODUCTS.get(sku)


def get_product_price(sku: str) -> Decimal | None:
    product = get_product(sku)
    if not product:
        return None
    return Decimal(product["price"])


def get_product_name(sku: str) -> str:
    product = get_product(sku)
    return product["short_title"] if product else sku


def list_catalog_items() -> list[dict]:
    items: list[dict] = []
    for product in PRODUCTS.values():
        items.append(
            {
                "sku": product["sku"],
                "title": product["title"],
                "short_title": product["short_title"],
                "subtitle": product["subtitle"],
                "description": product["description"],
                "price": product["price"],
                "unit_label": product["unit_label"],
                "badges": product["badges"],
                "features": product["features"],
                "accent": product["accent"],
                "images": product["images"],
            }
        )
    return items
