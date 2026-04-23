from __future__ import annotations

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from app.utils.responses import error_payload


def install_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content=error_payload(
                error="http_error",
                detail=exc.detail,
                request_id=getattr(request.state, "request_id", None),
            ),
            headers=exc.headers,
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        return JSONResponse(
            status_code=422,
            content=error_payload(
                error="validation_error",
                detail=exc.errors(),
                request_id=getattr(request.state, "request_id", None),
            ),
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        return JSONResponse(
            status_code=500,
            content=error_payload(
                error="internal_error",
                detail="Unexpected error",
                request_id=getattr(request.state, "request_id", None),
            ),
        )
