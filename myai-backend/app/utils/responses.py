from __future__ import annotations

from app.schemas.common import APIError, APIMeta, APIResponse


def success_response(data, *, request_id: str | None = None, provider: str | None = None, model: str | None = None, warnings: list[str] | None = None) -> APIResponse:
    meta: APIMeta | None = None
    if request_id or provider or model or warnings:
        meta = APIMeta(
            request_id=request_id,
            provider=provider,
            model=model,
            warnings=warnings or [],
        )
    return APIResponse(data=data, meta=meta)


def error_payload(*, error: str, detail: object | None = None, request_id: str | None = None) -> dict[str, object | None]:
    payload = APIError(error=error, detail=detail, request_id=request_id)
    return payload.model_dump()
