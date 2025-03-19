from http import HTTPStatus
from logging import getLogger
from typing import cast

from cumplo_common.database import firestore
from cumplo_common.models.user import User
from fastapi import APIRouter
from fastapi.requests import Request

logger = getLogger(__name__)

router = APIRouter(prefix="/users")


@router.delete("/me", status_code=HTTPStatus.NO_CONTENT)
def _delete_user(request: Request) -> None:
    """Delete a user."""
    user = cast(User, request.state.user)
    firestore.client.users.delete(str(user.id))


@router.put("/me/disable", status_code=HTTPStatus.NO_CONTENT)
def _disable_user(request: Request) -> None:
    """Disable a user."""
    user = cast(User, request.state.user)

    firestore.client.disabled.put(user)
    firestore.client.users.delete(str(user.id))
