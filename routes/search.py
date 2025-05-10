from fastapi import APIRouter, Query, HTTPException
from typing import List

from helpers import _clean, _search_usda
from models import Suggestion

router = APIRouter(
    prefix="/search",
    tags=["search"],
)

@router.get("/", response_model=List[Suggestion], summary="Type-ahead food search")
def search(
    q: str = Query(..., min_length=1, description="Search text for ingredient"),
    limit: int = Query(10, gt=0, le=50, description="Max number of suggestions to return"),
) -> List[Suggestion]:
    """
    Perform a text search against USDA FoodData Central to retrieve
    ingredient suggestions. Returns a list of Suggestion objects.
    """
    query = _clean(q)
    try:
        hits = _search_usda(query, limit)
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))

    suggestions: List[Suggestion] = []
    for hit in hits:
        suggestions.append(Suggestion(
            fdc_id=hit.get("fdcId", 0),
            description=hit.get("description", ""),
            category=hit.get("foodCategory"),
            data_type=hit.get("dataType"),
        ))
    return suggestions
