from http import HTTPStatus
from logging import getLogger

from cumplo_common.database import firestore
from cumplo_common.models.user import User
from fastapi import APIRouter
from fastapi.exceptions import HTTPException

from cumplo_tailor.controllers import UsersController
from cumplo_tailor.utils.dictionary import update_dictionary

logger = getLogger(__name__)

router = APIRouter(prefix="/users")


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
    user = await UsersController.create(payload)
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

    firestore.client.users.delete(user)


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
    firestore.client.users.delete(user)


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
    firestore.client.disabled.delete(user)
