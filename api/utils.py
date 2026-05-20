from typing import Any, Dict
from uuid import uuid4

from rest_framework.response import Response

from api.services.gemini_facade import GeminiService


def error_response(code: str, detail: str, status_code: int, fields: Dict[str, Any] | None = None) -> Response:
    payload = {
        "code": code,
        "detail": detail,
        "fields": fields or {},
        "trace_id": str(uuid4()),
    }
    return Response(payload, status=status_code)
