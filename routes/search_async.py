"""
Async search route for USDA API.
"""
from fastapi import APIRouter, Query, HTTPException, Request
from typing import List

from helpers_async import _clean, _search_usda
from models import Suggestion

router = APIRouter(
    prefix="/search",
    tags=["search"],
)

@router.get("/", response_model=List[Suggestion], summary="Type-ahead food search")
async def search(
    request: Request,
    q: str = Query(..., min_length=1, description="Search text for ingredient"),
    limit: int = Query(10, gt=0, le=50, description="Max number of suggestions to return"),
) -> List[Suggestion]:
    """
    Perform a text search against USDA FoodData Central to retrieve
    ingredient suggestions. Returns a list of Suggestion objects.
    
    This endpoint is rate-limited to 1,000 requests per hour per IP address.
    """
    query = _clean(q)
    try:
        hits = await _search_usda(request, query, limit)
    except ValueError as e:
        raise HTTPException(status_code=502, detail=str(e))
    except HTTPException:
        # Re-raise HTTPExceptions (like 429 Too Many Requests)
        raise

    suggestions: List[Suggestion] = []
    for hit in hits:
        suggestions.append(Suggestion(
            fdc_id=hit.get("fdcId", 0),
            description=hit.get("description", ""),
            category=hit.get("foodCategory"),
            data_type=hit.get("dataType"),
        ))
    return suggestions