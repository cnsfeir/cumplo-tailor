from collections.abc import Iterable
from http import HTTPStatus
from typing import cast

from cumplo_common.models.channel import ChannelConfiguration, ChannelType, IFTTTConfiguration, WebhookConfiguration
from cumplo_common.models.user import User
from fastapi.exceptions import HTTPException


def _filter_channels(
    user: User, channel: ChannelConfiguration, channel_type: ChannelType
) -> Iterable[ChannelConfiguration]:
    """
    Filters the user's channels by type excluding the specified channel.

    Args:
        user (User): The user to filter the channels from.
        channel_type (ChannelType): The type of channel to filter.
        channel (ChannelConfiguration): The channel to exclude from the results.

    Returns:
        Iterable[ChannelConfiguration]: The user's channels of the specified type.
    """
    return filter(lambda c: c.type_ == channel_type and c.id != channel.id, user.channels.values())


def validate(user: User, channel: ChannelConfiguration) -> None:
    """
    Validates that the user can add the channel based on the user's existing channels.

    Args:
        channel (ChannelConfiguration): The channel configuration to validate.

    Raises:
        HTTPException: When a the user already has a WhatsApp channel.
        HTTPException: When the user already has an IFTTT channel with the a different key.
        HTTPException: When the user already has an IFTTT channel with the same event.
        HTTPException: When the user already has a Webhook channel with the same URL.
    """
    match channel.type_:
        case ChannelType.WHATSAPP:
            if any(_filter_channels(user, channel, ChannelType.WHATSAPP)):
                raise HTTPException(HTTPStatus.BAD_REQUEST, detail="Only one WhatsApp channel is allowed")

        case ChannelType.IFTTT:
            channel = cast(IFTTTConfiguration, channel)
            for ifttt_channel in _filter_channels(user, channel, ChannelType.IFTTT):
                ifttt_channel = cast(IFTTTConfiguration, ifttt_channel)
                if ifttt_channel.key != channel.key:
                    raise HTTPException(HTTPStatus.BAD_REQUEST, detail="Only one IFTTT key is allowed per user")
                if ifttt_channel.event == channel.event:
                    raise HTTPException(HTTPStatus.CONFLICT, detail="This IFTTT event already exists")

        case ChannelType.WEBHOOK:
            channel = cast(WebhookConfiguration, channel)
            for webhook_channel in _filter_channels(user, channel, ChannelType.WEBHOOK):
                if cast(WebhookConfiguration, webhook_channel).url == channel.url:
                    raise HTTPException(HTTPStatus.CONFLICT, detail="This webhook URL already exists")
