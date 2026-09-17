"""Domain schemas the generator knows how to produce.

Each domain maps to its canonical column list, an "id" column that messiness
injection leaves alone (duplicating/nulling a primary key would just be a
duplicate row, not a messy value), and a row-builder that fabricates one
record's worth of fake PII/business data.
"""
from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Callable

from faker import Faker

RowBuilder = Callable[[Faker, random.Random, int], dict]


@dataclass(frozen=True)
class Domain:
    fieldnames: list[str]
    id_field: str
    build_row: RowBuilder


def _build_ecommerce_order(fake: Faker, rng, index: int) -> dict:
    return {
        "order_id": f"ORD-{index:06d}",
        "customer_name": fake.name(),
        "customer_email": fake.email(),
        "order_date": fake.date_between(start_date="-1y", end_date="today").isoformat(),
        "product_sku": fake.bothify(text="SKU-????-####").upper(),
        "quantity": rng.randint(1, 10),
        "unit_price": round(rng.uniform(4.99, 299.99), 2),
        "order_status": rng.choice(["pending", "shipped", "delivered", "returned"]),
    }


def _build_hr_employee(fake: Faker, rng, index: int) -> dict:
    return {
        "employee_id": f"EMP-{index:06d}",
        "full_name": fake.name(),
        "email": fake.company_email(),
        "department": rng.choice(["engineering", "sales", "finance", "support", "hr"]),
        "hire_date": fake.date_between(start_date="-8y", end_date="today").isoformat(),
        "salary": rng.randint(45_000, 220_000),
        "manager_id": f"EMP-{rng.randint(0, index):06d}" if index else "",
    }


DOMAINS: dict[str, Domain] = {
    "ecommerce_orders": Domain(
        fieldnames=[
            "order_id",
            "customer_name",
            "customer_email",
            "order_date",
            "product_sku",
            "quantity",
            "unit_price",
            "order_status",
        ],
        id_field="order_id",
        build_row=_build_ecommerce_order,
    ),
    "hr_employees": Domain(
        fieldnames=[
            "employee_id",
            "full_name",
            "email",
            "department",
            "hire_date",
            "salary",
            "manager_id",
        ],
        id_field="employee_id",
        build_row=_build_hr_employee,
    ),
}
