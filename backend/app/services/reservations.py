from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict
from zoneinfo import ZoneInfo

from sqlalchemy import text

from app.core.database_pool import db_pool


class PropertyNotFoundError(Exception):
    """Raised when a property is not available to the current tenant."""

    pass


async def calculate_monthly_revenue(
    property_id: str,
    tenant_id: str,
    year: int,
    month: int,
) -> Dict[str, Any]:
    """
    Calculate revenue for a calendar month using the property's timezone.
    """

    property_query = text("""
        SELECT timezone
        FROM properties
            WHERE id = :property_id
          AND tenant_id = :tenant_id
    """)

    async with db_pool.get_session() as session:
        property_result = await session.execute(
            property_query,
            {
                "property_id": property_id,
                "tenant_id": tenant_id,
            },
        )

        property_row = property_result.fetchone()

        if property_row is None:
            raise PropertyNotFoundError(
                f"Property {property_id} was not found"
            )

        property_timezone = ZoneInfo(property_row.timezone)

        start_local = datetime(
            year,
            month,
            1,
            tzinfo=property_timezone,
        )

        if month == 12:
            end_local = datetime(
                year + 1,
                1,
                1,
                tzinfo=property_timezone,
            )
        else:
            end_local = datetime(
                year,
                month + 1,
                1,
                tzinfo=property_timezone,
            )

        start_utc = start_local.astimezone(timezone.utc)
        end_utc = end_local.astimezone(timezone.utc)

        revenue_query = text("""
            SELECT
                COALESCE(SUM(total_amount), 0) AS total_revenue,
                COUNT(*) AS reservation_count,
                COALESCE(MIN(currency), 'USD') AS currency
            FROM reservations
            WHERE property_id = :property_id
              AND tenant_id = :tenant_id
              AND check_in_date >= :start_utc
              AND check_in_date < :end_utc
        """)

        revenue_result = await session.execute(
            revenue_query,
            {
                "property_id": property_id,
                "tenant_id": tenant_id,
                "start_utc": start_utc,
                "end_utc": end_utc,
            },
        )

        revenue_row = revenue_result.fetchone()

    return {
        "property_id": property_id,
        "tenant_id": tenant_id,
        "year": year,
        "month": month,
        "total": str(Decimal(str(revenue_row.total_revenue))),
        "currency": revenue_row.currency,
        "count": revenue_row.reservation_count,
    }


async def calculate_total_revenue(
    property_id: str,
    tenant_id: str,
) -> Dict[str, Any]:
    """
    Aggregate all revenue for one property belonging to the tenant.
    """

    query = text("""
        SELECT
            property_id,
            SUM(total_amount) AS total_revenue,
            COUNT(*) AS reservation_count
        FROM reservations
        WHERE property_id = :property_id
          AND tenant_id = :tenant_id
        GROUP BY property_id
    """)

    async with db_pool.get_session() as session:
        result = await session.execute(
            query,
            {
                "property_id": property_id,
                "tenant_id": tenant_id,
            },
        )

        row = result.fetchone()

    if row:
        total_revenue = Decimal(str(row.total_revenue))

        return {
            "property_id": property_id,
            "tenant_id": tenant_id,
            "total": str(total_revenue),
            "currency": "USD",
            "count": row.reservation_count,
        }

    return {
        "property_id": property_id,
        "tenant_id": tenant_id,
        "total": "0.00",
        "currency": "USD",
        "count": 0,
    }