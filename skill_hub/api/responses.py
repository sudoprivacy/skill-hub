"""API Response utilities"""

from typing import Any, Dict, Optional
from quart import jsonify


def success_response(
    data: Any = None,
    message: str = "Success",
    status_code: int = 200,
    meta: Optional[Dict[str, Any]] = None,
) -> tuple:
    """Create a standardized success response
    
    Args:
        data: Response data
        message: Success message
        status_code: HTTP status code
        meta: Additional metadata
        
    Returns:
        Tuple of (response, status_code)
    """
    response = {
        "success": True,
        "message": message,
        "data": data,
    }
    
    if meta:
        response["meta"] = meta
    
    return jsonify(response), status_code


def error_response(
    message: str = "An error occurred",
    status_code: int = 500,
    error_code: str = "INTERNAL_ERROR",
    details: Optional[Dict[str, Any]] = None,
) -> tuple:
    """Create a standardized error response
    
    Args:
        message: Error message
        status_code: HTTP status code
        error_code: Error code
        details: Additional error details
        
    Returns:
        Tuple of (response, status_code)
    """
    response = {
        "success": False,
        "error": {
            "code": error_code,
            "message": message,
        }
    }
    
    if details:
        response["error"]["details"] = details
    
    return jsonify(response), status_code


def paginated_response(
    items: list,
    total: int,
    page: int,
    per_page: int,
    message: str = "Success",
) -> tuple:
    """Create a paginated response
    
    Args:
        items: List of items for current page
        total: Total number of items
        page: Current page number (1-indexed)
        per_page: Number of items per page
        
    Returns:
        Tuple of (response, status_code)
    """
    total_pages = (total + per_page - 1) // per_page if per_page > 0 else 0
    
    meta = {
        "pagination": {
            "total": total,
            "count": len(items),
            "per_page": per_page,
            "current_page": page,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_previous": page > 1,
        }
    }
    
    return success_response(
        data=items,
        message=message,
        meta=meta,
    )
