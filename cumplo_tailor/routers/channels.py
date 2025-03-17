from http import HTTPStatus
from logging import getLogger
from typing import cast

import ulid
from cumplo_common.database import firestore
from cumplo_common.models.channel import (
    ALL_EVENTS,
    CHANNEL_CONFIGURATION_BY_TYPE,
    ChannelType,
    IFTTTConfiguration,
    PublicEvent,
    WebhookConfiguration,
)
from cumplo_common.models.user import User
from fastapi import APIRouter
from fastapi.exceptions import HTTPException
from fastapi.requests import Request

from cumplo_tailor.controllers import ChannelsController

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
def _create_channel(request: Request, channel_type: ChannelType, payload: dict) -> dict:
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

    return channel.json()


@router.patch("/whatsapp", status_code=HTTPStatus.OK)
def _update_whatsapp_channel(request: Request, payload: dict) -> dict:
    """
    Update the WhatsApp channel phone number.

    Raises:
        HTTPException: If no WhatsApp channel exists (404)
        HTTPException: If phone number is missing from payload (400)
        HTTPException: If phone number is unchanged (400)

    """
    user = cast(User, request.state.user)

    # Find the WhatsApp channel
    channel = next((channel for channel in user.channels.values() if channel.type_ == ChannelType.WHATSAPP), None)
    if not channel:
        raise HTTPException(HTTPStatus.NOT_FOUND)

    if not (phone_number := payload.get("phone_number")):
        raise HTTPException(HTTPStatus.BAD_REQUEST)

    if phone_number == channel.phone_number:
        raise HTTPException(HTTPStatus.CONFLICT)

    # Update only the phone number
    channel.phone_number = str(phone_number)

    user.channels[str(channel.id)] = channel
    firestore.client.users.put(user)

    return channel.json()


@router.patch("/webhook/{id_channel}", status_code=HTTPStatus.OK)
def _update_webhook_channel(request: Request, id_channel: str, payload: dict) -> dict:
    """
    Update the webhook channel URL.

    Raises:
        HTTPException: If no webhook channel exists (404)
        HTTPException: If URL is missing from payload (400)
        HTTPException: If URL is unchanged (400)

    """
    user = cast(User, request.state.user)

    # Find the webhook channel
    if not (channel := user.channels.get(id_channel)):
        raise HTTPException(HTTPStatus.NOT_FOUND)

    if channel.type_ != ChannelType.WEBHOOK:
        raise HTTPException(HTTPStatus.BAD_REQUEST)

    channel = cast(WebhookConfiguration, channel)

    if not (url := payload.get("url")):
        raise HTTPException(HTTPStatus.BAD_REQUEST)

    if url == channel.url:
        raise HTTPException(HTTPStatus.CONFLICT)

    # Update only the URL
    channel.url = str(url)

    user.channels[str(channel.id)] = channel
    firestore.client.users.put(user)

    return channel.json()


@router.patch("/ifttt/{id_channel}", status_code=HTTPStatus.OK)
def _update_ifttt_channel(request: Request, id_channel: str, payload: dict) -> dict:
    """
    Update the IFTTT channel event.

    Raises:
        HTTPException: If no IFTTT channel exists (404)
        HTTPException: If key is missing from payload (400)
        HTTPException: If key is unchanged (400)

    """
    user = cast(User, request.state.user)

    # Find the IFTTT channel
    if not (channel := user.channels.get(id_channel)):
        raise HTTPException(HTTPStatus.NOT_FOUND)

    if channel.type_ != ChannelType.IFTTT:
        raise HTTPException(HTTPStatus.BAD_REQUEST)

    channel = cast(IFTTTConfiguration, channel)

    if not (event := payload.get("event")):
        raise HTTPException(HTTPStatus.BAD_REQUEST)

    if event == channel.event:
        raise HTTPException(HTTPStatus.CONFLICT)

    # Update only the event
    channel.event = str(event)

    user.channels[str(channel.id)] = channel
    firestore.client.users.put(user)

    return channel.json()


@router.post("/{id_channel}/events/{event}", status_code=HTTPStatus.NO_CONTENT)
def _enable_channel_event(request: Request, id_channel: str, event: PublicEvent) -> None:
    """
    Enable an event for a specific channel.

    Raises:
        HTTPException: If the channel is not found (404)
        HTTPException: If the event is already enabled (409)

    """
    user = cast(User, request.state.user)
    if not (channel := user.channels.get(id_channel)):
        raise HTTPException(HTTPStatus.NOT_FOUND)

    if channel.enabled_events == ALL_EVENTS or event in channel.enabled_events:
        raise HTTPException(HTTPStatus.CONFLICT, detail="Event is already enabled")

    if channel.enabled_events == ALL_EVENTS:
        # NOTE: If all events are enabled, remove from disabled_events
        channel.disabled_events.discard(event)

    elif isinstance(channel.enabled_events, set):
        # NOTE: Otherwise add to enabled_events
        channel.enabled_events.add(event)

    firestore.client.users.put(user)


@router.delete("/{id_channel}/events/{event}", status_code=HTTPStatus.NO_CONTENT)
def _disable_channel_event(request: Request, id_channel: str, event: PublicEvent) -> None:
    """
    Disable an event for a specific channel.

    Raises:
        HTTPException: If the channel is not found (404)
        HTTPException: If the event is already disabled (409)

    """
    user = cast(User, request.state.user)
    if not (channel := user.channels.get(id_channel)):
        raise HTTPException(HTTPStatus.NOT_FOUND)

    if channel.enabled_events != ALL_EVENTS and event not in channel.enabled_events:
        raise HTTPException(HTTPStatus.CONFLICT, detail="Event is already disabled")

    if channel.enabled_events == ALL_EVENTS:
        # NOTE: If all events are enabled, add to disabled_events
        if event in channel.disabled_events:
            raise HTTPException(HTTPStatus.CONFLICT, detail="Event is already disabled")
        channel.disabled_events.add(event)

        # NOTE: Reset to empty sets if all possible events are disabled
        if len(channel.disabled_events) == len(PublicEvent):
            channel.enabled_events = set()
            channel.disabled_events = set()

    elif isinstance(channel.enabled_events, set):
        # NOTE: Otherwise remove from enabled_events
        channel.enabled_events.discard(event)

    firestore.client.users.put(user)


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
