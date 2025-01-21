from http import HTTPStatus
from logging import getLogger

import ulid
from cumplo_common.database import firestore
from cumplo_common.integrations import CloudPubSub
from cumplo_common.models import PrivateEvent
from cumplo_common.models.user import User
from fastapi import APIRouter
from fastapi.exceptions import HTTPException

from cumplo_tailor.integrations import CloudCredentials
from cumplo_tailor.utils.dictionary import update_dictionary

logger = getLogger(__name__)

router = APIRouter(prefix="/users")

EVENT_PER_USER_UPDATE: dict[str, PrivateEvent] = {
    "filters": PrivateEvent.USER_FILTERS_UPDATED,
    "channels": PrivateEvent.USER_CHANNELS_UPDATED,
    "credentials": PrivateEvent.USER_CREDENTIALS_UPDATED,
}


@router.get("", status_code=HTTPStatus.OK)
def _list_users() -> list[dict]:
    """List the existing users."""
    return [user.json() for user in firestore.client.users.list()]


@router.get("/{id_user}", status_code=HTTPStatus.OK)
def _retrieve_user(id_user: str) -> dict:
    """
    Retrieve a single user.

    Raises:
        HTTPException: If the user is not found (404)

    """
    if not (user_ := firestore.client.users.get(id_user)):
        raise HTTPException(HTTPStatus.NOT_FOUND)

    return user_.json()


@router.post("", status_code=HTTPStatus.CREATED)
async def _create_user(payload: dict) -> dict:
    """Create a new user."""
    user = User.model_validate({**payload, "id": ulid.new(), "api_key": ""})
    user.api_key = await CloudCredentials.create_api_key(str(user.id))

    firestore.client.users.create(user)
    return user.json()


@router.patch("/{id_user}", status_code=HTTPStatus.OK)
def _update_user(payload: dict, id_user: str) -> dict:
    """
    Update a user.

    Raises:
        HTTPException: If the user is not found (404)

    """
    try:
        user = firestore.client.users.get(id_user)
    except KeyError:
        raise HTTPException(HTTPStatus.NOT_FOUND)  # noqa: B904

    data = update_dictionary(user.model_dump(), payload)
    new_user = User.model_validate(data)

    firestore.client.users.put(new_user)

    for key, topic in EVENT_PER_USER_UPDATE.items():
        if key in payload:
            CloudPubSub.publish(content=new_user.json(), topic=topic, id_user=str(new_user.id))

    return new_user.json()


@router.delete("/{id_user}", status_code=HTTPStatus.NO_CONTENT)
def _delete_user(id_user: str) -> None:
    """
    Delete a user.

    Raises:
        HTTPException: If the user is not found (404)

    """
    try:
        user = firestore.client.users.get(id_user)
    except KeyError:
        raise HTTPException(HTTPStatus.NOT_FOUND)  # noqa: B904

    firestore.client.users.delete(str(user.id))
    CloudPubSub.publish(content=user.json(), topic=PrivateEvent.USER_DELETED, id_user=str(user.id))


@router.patch("/{id_user}/disable", status_code=HTTPStatus.NO_CONTENT)
def _disable_user(id_user: str) -> None:
    """
    Disable a user.

    Raises:
        HTTPException: If the user is not found (404)

    """
    try:
        user = firestore.client.users.get(id_user)
    except KeyError:
        raise HTTPException(HTTPStatus.NOT_FOUND)  # noqa: B904

    firestore.client.disabled.put(user)
    firestore.client.users.delete(str(user.id))

    CloudPubSub.publish(content=user.json(), topic=PrivateEvent.USER_DELETED, id_user=str(user.id))


@router.patch("/{id_user}/enable", status_code=HTTPStatus.NO_CONTENT)
def _enable_user(id_user: str) -> None:
    """
    Enable a user.

    Raises:
        HTTPException: If the user is not found (404)

    """
    if not (user := firestore.client.disabled.get(id_user)):
        raise HTTPException(HTTPStatus.NOT_FOUND)

    firestore.client.users.put(user)
    firestore.client.disabled.delete(str(user.id))
