from http import HTTPStatus
from logging import getLogger
from typing import cast
from cumplo_common.database import firestore
from cumplo_common.models.channel import CHANNEL_CONFIGURATION_BY_TYPE, ChannelType
from cumplo_common.models.user import User
from fastapi import APIRouter
from fastapi.exceptions import HTTPException
from fastapi.requests import Request
from pydantic import ValidationError
from cumplo_tailor import business

logger = getLogger(__name__)

router = APIRouter(prefix="/channels")


@router.get("", status_code=HTTPStatus.OK)
def _get_channels(request: Request) -> list[dict]:
    """Gets a list of existing configurations."""
    user = cast(User, request.state.user)
    return list(channel.json() for channel in user.channels.values())


@router.get("/{id_channel}", status_code=HTTPStatus.OK)
def _get_single_channel(request: Request, id_channel: str) -> dict:
    """
    Gets a single channel configuration.
    """
    user = cast(User, request.state.user)
    if not (configuration := user.channels.get(id_channel)):
        raise HTTPException(HTTPStatus.NOT_FOUND)

    return configuration.json()


@router.post("/{channel_type}", status_code=HTTPStatus.CREATED)
def _post_channel(request: Request, channel_type: ChannelType, payload: dict) -> dict:
    """
    Creates a new channel configuration.
    """
    user = cast(User, request.state.user)

    try:
        channel = CHANNEL_CONFIGURATION_BY_TYPE[channel_type].model_validate(payload)
    except ValidationError as error:
        raise HTTPException(HTTPStatus.UNPROCESSABLE_ENTITY, detail=error.errors()) from error

    business.channels.validate(user, channel)

    firestore.client.channels.put(str(user.id), channel)
    return channel.json()


# NOTE: Eventually, there will be a channel with multiple fields.
# When this happens, a new class for this payload will be needed so the user can send partial updates.
# For now, the payload is simply the ChannelConfiguration class.


@router.patch("/{id_channel}", status_code=HTTPStatus.OK)
def _patch_channel(request: Request, id_channel: str, payload: dict) -> dict:
    """
    Updates a channel configuration.
    """
    user = cast(User, request.state.user)
    if not (channel := user.channels.get(id_channel)):
        raise HTTPException(HTTPStatus.NOT_FOUND)

    try:
        new_channel = CHANNEL_CONFIGURATION_BY_TYPE[channel.type_].model_validate({**channel.model_dump(), **payload})
    except ValidationError as error:
        raise HTTPException(HTTPStatus.UNPROCESSABLE_ENTITY, detail=error.errors()) from error

    if new_channel == channel:
        raise HTTPException(HTTPStatus.BAD_REQUEST, detail="Nothing to update")

    if new_channel in user.channels.values():
        raise HTTPException(HTTPStatus.CONFLICT, detail="The updated Channel already exists")

    firestore.client.channels.put(str(user.id), new_channel)
    return new_channel.json()


@router.delete("/{id_channel}", status_code=HTTPStatus.NO_CONTENT)
def _delete_channel(request: Request, id_channel: str) -> None:
    """
    Soft-deletes a channel configuration.
    """
    user = cast(User, request.state.user)
    if not user.channels.get(id_channel):
        raise HTTPException(HTTPStatus.NOT_FOUND)

    return firestore.client.channels.delete(str(user.id), id_channel)
