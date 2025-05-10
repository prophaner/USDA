from typing import List

from helpers import _clean, _search_usda
from models import Suggestion

def suggest(query: str, limit: int = 10) -> List[Suggestion]:
    """
    Return up to `limit` matching USDA suggestions for the given query.
    """
    cleaned = _clean(query)
    raw_list = _search_usda(cleaned, limit)
    return [
        Suggestion(
            fdc_id = item["fdcId"],
            description = item["description"].title(),
            category = item.get("foodCategory"),
            data_type=item.get("dataType", "Unknown"),
        )
        for item in raw_list
    ]
