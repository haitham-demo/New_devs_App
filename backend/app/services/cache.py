import json
import os
from typing import Any, Dict

import redis.asyncio as redis


# Initialize Redis client (typically configured centrally).
redis_client = redis.Redis.from_url(
    os.getenv("REDIS_URL", "redis://localhost:6379/0")
)


async def get_revenue_summary(
    property_id: str,
    tenant_id: str,
    year: int,
    month: int,
) -> Dict[str, Any]:
    """
    Fetch monthly revenue while keeping cached data isolated by tenant,
    property, year, and month.
    """

    cache_key = (
        f"revenue:v2:{tenant_id}:{property_id}:{year}:{month}"
    )

    cached = await redis_client.get(cache_key)

    if cached is not None:
        return json.loads(cached)

    from app.services.reservations import calculate_monthly_revenue

    result = await calculate_monthly_revenue(
        property_id=property_id,
        tenant_id=tenant_id,
        year=year,
        month=month,
    )

    # Cache the result for 5 minutes.
    await redis_client.setex(
        cache_key,
        300,
        json.dumps(result),
    )

    return result