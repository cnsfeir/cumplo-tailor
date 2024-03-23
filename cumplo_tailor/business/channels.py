from http import HTTPStatus
from typing import cast

from cumplo_common.models.channel import (
    ChannelType,
    IFTTTConfiguration,
    WebhookConfiguration,
    ChannelConfiguration,
)
from cumplo_common.models.user import User
from fastapi.exceptions import HTTPException


def validate(user: User, channel: ChannelConfiguration) -> None:
    """
    Validates that the user can add the channel based on the user's existing channels.

    Args:
        channel (ChannelConfiguration): The channel configuration to validate.

    Raises:
        HTTPException: When a the user already has a WhatsApp channel.
        HTTPException: When the user already has an IFTTT channel with the a different key.
        HTTPException: When the user already has a Webhook channel with the same URL.
    """
    match channel.type_:
        case ChannelType.WHATSAPP:
            if any(channel.type_ == ChannelType.WHATSAPP for channel in user.channels.values()):
                raise HTTPException(HTTPStatus.CONFLICT, detail="Only one WhatsApp channel is allowed")

        case ChannelType.IFTTT:
            channel = cast(IFTTTConfiguration, channel)
            ifttt_channels = (channel for channel in user.channels.values() if channel.type_ == ChannelType.IFTTT)
            if existing_channel := next(ifttt_channels, None):
                if cast(IFTTTConfiguration, existing_channel).key != channel.key:
                    raise HTTPException(HTTPStatus.CONFLICT, detail="Only one IFTTT key is allowed per user")

        case ChannelType.WEBHOOK:
            channel = cast(WebhookConfiguration, channel)
            for webhook_channel in filter(lambda channel: channel.type_ == ChannelType.WEBHOOK, user.channels.values()):
                if cast(WebhookConfiguration, webhook_channel).url == channel.url:
                    raise HTTPException(HTTPStatus.CONFLICT, detail="This webhook URL already exists")
