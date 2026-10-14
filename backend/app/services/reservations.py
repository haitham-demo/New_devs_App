from datetime import datetime
from decimal import Decimal
from typing import Any, Dict

from sqlalchemy import text

from app.core.database_pool import db_pool


async def calculate_monthly_revenue(
    property_id: str,
    month: int,
    year: int,
    db_session=None,
) -> Decimal:
    """
    Calculate revenue for a specific month.

    This function will be corrected separately when fixing monthly reporting
    and timezone handling.
    """

    start_date = datetime(year, month, 1)

    if month < 12:
        end_date = datetime(year, month + 1, 1)
    else:
        end_date = datetime(year + 1, 1, 1)

    print(
        f"DEBUG: Querying revenue for {property_id} "
        f"from {start_date} to {end_date}"
    )

    return Decimal("0")


async def calculate_total_revenue(
    property_id: str,
    tenant_id: str,
) -> Dict[str, Any]:
    """Calculate total revenue using the real PostgreSQL database."""

    query = text(
        """
        SELECT
            property_id,
            COALESCE(SUM(total_amount), 0) AS total_revenue,
            COUNT(*) AS reservation_count
        FROM reservations
        WHERE property_id = :property_id
          AND tenant_id = :tenant_id
        GROUP BY property_id
        """
    )

    async with db_pool.get_session() as session:
        result = await session.execute(
            query,
            {
                "property_id": property_id,
                "tenant_id": tenant_id,
            },
        )

        row = result.fetchone()

    if row is None:
        return {
            "property_id": property_id,
            "tenant_id": tenant_id,
            "total": "0.00",
            "currency": "USD",
            "count": 0,
        }

    total_revenue = Decimal(str(row.total_revenue))

    return {
        "property_id": property_id,
        "tenant_id": tenant_id,
        "total": str(total_revenue),
        "currency": "USD",
        "count": row.reservation_count,
    }