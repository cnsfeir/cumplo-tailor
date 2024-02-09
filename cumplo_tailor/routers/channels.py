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

logger = getLogger(__name__)

router = APIRouter(prefix="/channels")


@router.get("", status_code=HTTPStatus.OK)
def _get_channels(request: Request) -> list[dict]:
    """Gets a list of existing configurations."""
    user = cast(User, request.state.user)
    return list(channel.json() for channel in user.channels.values())


@router.get("/{channel_type}", status_code=HTTPStatus.OK)
def _get_single_channel(request: Request, channel_type: ChannelType) -> dict:
    """
    Gets a single channel configuration.
    """
    user = cast(User, request.state.user)
    if not (configuration := user.channels.get(channel_type)):
        raise HTTPException(HTTPStatus.NOT_FOUND)

    return configuration.json()


@router.post("/{channel_type}", status_code=HTTPStatus.CREATED)
def _post_channel(request: Request, channel_type: ChannelType, payload: dict) -> dict:
    """
    Creates a new channel configuration.
    """
    user = cast(User, request.state.user)
    if channel_type in user.channels.keys():
        raise HTTPException(HTTPStatus.CONFLICT, detail="Channel already exists")

    try:
        channel = CHANNEL_CONFIGURATION_BY_TYPE[channel_type].model_validate(payload)
    except ValidationError as error:
        raise HTTPException(HTTPStatus.UNPROCESSABLE_ENTITY, detail=error.errors()) from error

    firestore.client.channels.put(str(user.id), channel)
    return channel.json()


# NOTE: Eventually, there will be a channel with multiple fields.
# When this happens, a new class for this payload will be needed so the user can send partial updates.
# For now, the payload is simply the ChannelConfiguration class.


@router.patch("/{channel_type}", status_code=HTTPStatus.CREATED)
def _patch_channel(request: Request, channel_type: ChannelType, payload: dict) -> dict:
    """
    Updates a channel configuration.
    """
    print("ELPAYLOAD", payload)
    user = cast(User, request.state.user)
    if not (channel := user.channels.get(channel_type)):
        raise HTTPException(HTTPStatus.NOT_FOUND)

    try:
        new_channel = CHANNEL_CONFIGURATION_BY_TYPE[channel_type].model_validate({**channel.model_dump(), **payload})
    except ValidationError as error:
        raise HTTPException(HTTPStatus.UNPROCESSABLE_ENTITY, detail=error.errors()) from error

    if new_channel in user.channels.values():
        raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail="Nothing to update")

    firestore.client.channels.put(str(user.id), new_channel)
    return new_channel.json()


@router.delete("/{channel_type}", status_code=HTTPStatus.NO_CONTENT)
def _delete_channel(request: Request, channel_type: ChannelType) -> None:
    """
    Soft-deletes a channel configuration.
    """
    user = cast(User, request.state.user)
    if not user.channels.get(channel_type):
        raise HTTPException(HTTPStatus.NOT_FOUND)

    return firestore.client.channels.delete(str(user.id), channel_type)
