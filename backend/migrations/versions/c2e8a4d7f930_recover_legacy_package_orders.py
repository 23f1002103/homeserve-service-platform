"""recover package orders created before the parent model

Revision ID: c2e8a4d7f930
Revises: b7d3e4f1a820
Create Date: 2026-11-16 23:00:00.000000

"""
from collections import defaultdict
from decimal import Decimal

from alembic import op
import sqlalchemy as sa


revision = "c2e8a4d7f930"
down_revision = "b7d3e4f1a820"
branch_labels = None
depends_on = None


def package_status(statuses):
    if statuses and all(status == "cancelled" for status in statuses):
        return "cancelled"
    if statuses and all(status == "completed" for status in statuses):
        return "completed"
    if any(status == "completed" for status in statuses):
        return "partially_completed"
    if statuses and all(status == "accepted" for status in statuses):
        return "assigned"
    if any(status == "accepted" for status in statuses):
        return "partially_assigned"
    if statuses and all(status == "payment_pending" for status in statuses):
        return "payment_pending"
    return "pending"


def upgrade():
    bind = op.get_bind()
    metadata = sa.MetaData()
    requests = sa.Table("service_requests", metadata, autoload_with=bind)
    payments = sa.Table("payments", metadata, autoload_with=bind)
    orders = sa.Table("package_orders", metadata, autoload_with=bind)

    orphan_rows = bind.execute(
        sa.select(
            requests.c.id,
            requests.c.customer_id,
            requests.c.service_package_id,
            requests.c.scheduled_for,
            requests.c.service_address,
            requests.c.status,
            requests.c.created_at,
        ).where(
            requests.c.service_package_id.is_not(None),
            requests.c.package_order_id.is_(None),
        )
    ).mappings().all()

    groups = defaultdict(list)
    for row in orphan_rows:
        key = (
            row["customer_id"],
            row["service_package_id"],
            row["scheduled_for"],
            row["service_address"],
        )
        groups[key].append(row)

    for (customer_id, package_id, _scheduled, _address), rows in groups.items():
        request_ids = [row["id"] for row in rows]
        amounts = bind.execute(
            sa.select(payments.c.amount).where(
                payments.c.service_request_id.in_(request_ids)
            )
        ).scalars().all()
        result = bind.execute(
            orders.insert().values(
                customer_id=customer_id,
                service_package_id=package_id,
                total_amount=sum(amounts, Decimal("0.00")),
                status=package_status([row["status"] for row in rows]),
                created_at=min(row["created_at"] for row in rows),
            )
        )
        order_id = result.inserted_primary_key[0]
        bind.execute(
            requests.update()
            .where(requests.c.id.in_(request_ids))
            .values(package_order_id=order_id)
        )


def downgrade():
    # Recovered parent links are valid package-order data and are intentionally
    # retained if this data-only migration is downgraded.
    pass
