from http import HTTPStatus
from logging import getLogger
from typing import cast

from cumplo_common.database import firestore
from cumplo_common.integrations import CloudPubSub
from cumplo_common.models import PrivateEvent
from cumplo_common.models.credentials import Credentials
from cumplo_common.models.user import User
from fastapi import APIRouter
from fastapi.requests import Request

logger = getLogger(__name__)

router = APIRouter(prefix="/credentials")


@router.put("", status_code=HTTPStatus.NO_CONTENT)
def _upsert_credentials(request: Request, payload: dict) -> None:
    """Update or insert user credentials."""
    user = cast(User, request.state.user)

    # HACK: This is temporary. Eventually we will use the credentials to get the user's Cumplo ID
    user.credentials = Credentials.model_validate({**payload, "cumplo_id": "1"})

    firestore.client.users.put(user)
    CloudPubSub.publish(content=user.json(), topic=PrivateEvent.USER_CREDENTIALS_UPDATED, id_user=str(user.id))


@router.delete("", status_code=HTTPStatus.NO_CONTENT)
def _delete_credentials(request: Request) -> None:
    """Delete user credentials."""
    user = cast(User, request.state.user)
    user.credentials = None

    firestore.client.users.put(user)
    CloudPubSub.publish(content=user.json(), topic=PrivateEvent.USER_CREDENTIALS_UPDATED, id_user=str(user.id))
