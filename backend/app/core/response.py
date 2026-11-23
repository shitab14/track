from typing import Generic, TypeVar, Optional, Any
from pydantic import BaseModel

T = TypeVar("T")

class ApiResponse(BaseModel, Generic[T]):
    """Standardized API response contract across all endpoints.
    
    Structure:
    - code: HTTP status code or domain status integer
    - message: Descriptive status message
    - data: Payload object, list, or null on error
    """
    code: int
    message: str
    data: Optional[T] = None

    @classmethod
    def success(cls, data: Any = None, message: str = "Success", code: int = 200) -> "ApiResponse[Any]":
        return cls(code=code, message=message, data=data)

    @classmethod
    def error(cls, message: str, code: int = 400) -> "ApiResponse[None]":
        return cls(code=code, message=message, data=None)
