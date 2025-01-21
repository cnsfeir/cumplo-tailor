import json
from http import HTTPStatus
from logging import DEBUG, ERROR, basicConfig, getLogger

import google.cloud.logging
from cumplo_common.dependencies import authenticate, is_admin
from fastapi import Depends, FastAPI
from fastapi.encoders import jsonable_encoder
from fastapi.requests import Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from cumplo_tailor.routers import channels, credentials, filters, users
from cumplo_tailor.utils.constants import IS_TESTING, LOG_FORMAT

# NOTE: Mute noisy third-party loggers
for module in ("google", "urllib3", "werkzeug", "googleapiclient"):
    getLogger(module).setLevel(ERROR)

getLogger("cumplo_common").setLevel(DEBUG)

if IS_TESTING:
    basicConfig(level=DEBUG, format=LOG_FORMAT)
else:
    client = google.cloud.logging.Client()
    client.setup_logging(log_level=DEBUG)

app = FastAPI(dependencies=[Depends(authenticate)])


@app.exception_handler(ValidationError)
async def _validation_error_handler(_request: Request, error: ValidationError) -> JSONResponse:  # noqa: RUF029
    """Format ValidationError as a JSON response."""
    content = json.loads(jsonable_encoder(error.json()))
    return JSONResponse(status_code=HTTPStatus.UNPROCESSABLE_ENTITY, content=content)


app.include_router(users.private.router, dependencies=[Depends(is_admin)])
app.include_router(users.public.router)
app.include_router(filters.router)
app.include_router(channels.router)
app.include_router(credentials.router)
