from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, Query

from app.core.auth import authenticate_request as get_current_user
from app.services.cache import get_revenue_summary
from app.services.reservations import PropertyNotFoundError


router = APIRouter()


@router.get("/dashboard/summary")
async def get_dashboard_summary(
    property_id: str,
    year: int = Query(..., ge=2000, le=2100),
    month: int = Query(..., ge=1, le=12),
    current_user: dict = Depends(get_current_user),
) -> Dict[str, Any]:
    tenant_id = getattr(current_user, "tenant_id", None)

    if not tenant_id:
        raise HTTPException(
            status_code=403,
            detail="Tenant context is required",
        )

    try:
        revenue_data = await get_revenue_summary(
            property_id=property_id,
            tenant_id=tenant_id,
            year=year,
            month=month,
        )
    except PropertyNotFoundError:
        raise HTTPException(
            status_code=404,
            detail="Property not found",
        )

    # Keep this conversion for now.
    # Decimal precision will be handled separately in Fix 4.
    total_revenue_float = float(revenue_data["total"])

    return {
        "property_id": revenue_data["property_id"],
        "total_revenue": total_revenue_float,
        "currency": revenue_data["currency"],
        "reservations_count": revenue_data["count"],
    }
