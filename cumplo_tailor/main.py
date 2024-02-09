from logging import CRITICAL, DEBUG, basicConfig, getLogger

import google.cloud.logging
from cumplo_common.dependencies.authentication import authenticate
from cumplo_common.middlewares import PubSubMiddleware
from fastapi import Depends, FastAPI

from cumplo_tailor.routers import channels, filters
from cumplo_tailor.utils.constants import IS_TESTING, LOG_FORMAT

basicConfig(level=DEBUG, format=LOG_FORMAT)
logger = getLogger(__name__)

# NOTE: Mute noisy third-party loggers
for module in ("google", "urllib3", "werkzeug"):
    getLogger(module).setLevel(CRITICAL)

if not IS_TESTING:
    client = google.cloud.logging.Client()
    client.setup_logging(log_level=DEBUG)


app = FastAPI(dependencies=[Depends(authenticate)])
app.add_middleware(PubSubMiddleware)

app.include_router(filters.router)
app.include_router(channels.router)
