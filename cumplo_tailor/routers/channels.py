from http import HTTPStatus
from logging import getLogger
from typing import cast

import ulid
from cumplo_common.database import firestore
from cumplo_common.integrations.cloud_pubsub import CloudPubSub
from cumplo_common.models import PrivateEvent
from cumplo_common.models.channel import CHANNEL_CONFIGURATION_BY_TYPE, ChannelType
from cumplo_common.models.user import User
from fastapi import APIRouter
from fastapi.exceptions import HTTPException
from fastapi.requests import Request

from cumplo_tailor.controllers import ChannelsController
from cumplo_tailor.utils.dictionary import update_dictionary

logger = getLogger(__name__)

router = APIRouter(prefix="/channels")


@router.get("", status_code=HTTPStatus.OK)
def _list_channels(request: Request) -> list[dict]:
    """List the existing channel configurations."""
    user = cast(User, request.state.user)
    return [channel.json() for channel in user.channels.values()]


@router.get("/{id_channel}", status_code=HTTPStatus.OK)
def _retrieve_channel(request: Request, id_channel: str) -> dict:
    """
    Retrieve a single channel configuration.

    Raises:
        HTTPException: If the channel is not found (404)

    """
    user = cast(User, request.state.user)
    if not (configuration := user.channels.get(id_channel)):
        raise HTTPException(HTTPStatus.NOT_FOUND)

    return configuration.json()


@router.post("/{channel_type}", status_code=HTTPStatus.CREATED)
def _post_channel(request: Request, channel_type: ChannelType, payload: dict) -> dict:
    """
    Create a new channel configuration.

    Raises:
        HTTPException: If the channel already exists (409)

    """
    user = cast(User, request.state.user)

    channel = CHANNEL_CONFIGURATION_BY_TYPE[channel_type].model_validate({"id": ulid.new(), **payload})
    ChannelsController.validate(user, channel)

    if channel in user.channels.values():
        raise HTTPException(HTTPStatus.CONFLICT, detail="The Channel already exists")

    user.channels[str(channel.id)] = channel
    firestore.client.users.put(user)
    CloudPubSub.publish(content=user.json(), topic=PrivateEvent.USER_CHANNELS_UPDATED, id_user=str(user.id))

    return channel.json()


@router.patch("/{id_channel}", status_code=HTTPStatus.OK)
def _update_channel(request: Request, id_channel: str, payload: dict) -> dict:
    """
    Update a channel configuration.

    Raises:
        HTTPException: If the channel is not found (404)
        HTTPException: If there are no changes to update (400)
        HTTPException: If the updated channel already exists (409)

    """
    user = cast(User, request.state.user)
    if not (channel := user.channels.get(id_channel)):
        raise HTTPException(HTTPStatus.NOT_FOUND)

    data = update_dictionary(channel.model_dump(), payload)
    new_channel = CHANNEL_CONFIGURATION_BY_TYPE[channel.type_].model_validate(data)

    if new_channel == channel:
        raise HTTPException(HTTPStatus.BAD_REQUEST, detail="Nothing to update")

    if new_channel in user.channels.values():
        raise HTTPException(HTTPStatus.CONFLICT, detail="The updated Channel already exists")

    ChannelsController.validate(user, new_channel)

    user.channels[str(new_channel.id)] = new_channel
    firestore.client.users.put(user)
    CloudPubSub.publish(content=user.json(), topic=PrivateEvent.USER_CHANNELS_UPDATED, id_user=str(user.id))

    return new_channel.json()


@router.delete("/{id_channel}", status_code=HTTPStatus.NO_CONTENT)
def _delete_channel(request: Request, id_channel: str) -> None:
    """
    Delete a channel configuration.

    Raises:
        HTTPException: If the channel is not found (404)

    """
    user = cast(User, request.state.user)
    if not user.channels.get(id_channel):
        raise HTTPException(HTTPStatus.NOT_FOUND)

    del user.channels[id_channel]
    firestore.client.users.put(user)
    CloudPubSub.publish(content=user.json(), topic=PrivateEvent.USER_CHANNELS_UPDATED, id_user=str(user.id))
