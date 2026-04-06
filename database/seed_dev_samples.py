"""Dev seed charge points (shared by scripts/seed_dev_db.py and tests)."""

from __future__ import annotations

from database.models import ChargePoint, Connection


def get_dev_seed_charge_points() -> list[ChargePoint]:
    """Return the same sample rows the dev seed script inserts when the table is empty."""
    return [
        ChargePoint(
            id=10001,
            uuid="seed-demo-001",
            address="1000 Hilltop Cir",
            town="Baltimore",
            postcode="21250",
            country="US",
            latitude=39.2555,
            longitude=-76.7105,
            contact_email=None,
            number_of_points=4,
            price="$0.35/kWh",
            availability="Operational",
            membership_required=False,
            access_key_required=False,
            operator="Demo Energy",
            last_verified=None,
            connections=[
                Connection(
                    port_type="CCS",
                    power_kw=150.0,
                    voltage=400,
                    amps=375,
                    current_type="DC",
                    status="Operational",
                    quantity=2,
                ),
                Connection(
                    port_type="J1772",
                    power_kw=7.2,
                    voltage=240,
                    amps=30,
                    current_type="AC",
                    status="Operational",
                    quantity=2,
                ),
            ],
        ),
        ChargePoint(
            id=10002,
            uuid="seed-demo-002",
            address="1 Main St",
            town="Columbia",
            postcode="21044",
            country="US",
            latitude=39.2037,
            longitude=-76.8610,
            contact_email="support@example.com",
            number_of_points=2,
            price=None,
            availability="Operational",
            membership_required=True,
            access_key_required=False,
            operator="Other Op",
            last_verified=None,
            connections=[
                Connection(
                    port_type="CHAdeMO",
                    power_kw=50.0,
                    voltage=500,
                    amps=125,
                    current_type="DC",
                    status="Operational",
                    quantity=1,
                ),
            ],
        ),
    ]
