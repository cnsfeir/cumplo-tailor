from collections.abc import Iterable
from http import HTTPStatus
from typing import cast

from cumplo_common.models.channel import (
    ChannelConfiguration,
    ChannelType,
    IFTTTConfiguration,
    WebhookConfiguration,
    WhatsappConfiguration,
)
from cumplo_common.models.user import User
from fastapi.exceptions import HTTPException

from cumplo_tailor.utils.constants import MAX_WEBHOOKS


class ChannelsController:
    """Controller for the channels."""

    @staticmethod
    def _filter(user: User, exclude: ChannelConfiguration, channel_type: ChannelType) -> Iterable[ChannelConfiguration]:
        """
        Filter the user's channels by type excluding the specified channel.

        Args:
            user (User): The user to filter the channels from.
            exclude (ChannelConfiguration): The channel to exclude from the results.
            channel_type (ChannelType): The type of channel to filter.

        Returns:
            Iterable[ChannelConfiguration]: The user's channels of the specified type.

        """
        return filter(lambda c: c.type_ == channel_type and c.id != exclude.id, user.channels.values())

    @classmethod
    def _validate_webhook_channels(cls, user: User, channel: WebhookConfiguration) -> None:
        """
        Validate the user can add the channel based on the user's existing channels.

        Raises:
            HTTPException: When the max amount of webhooks is reached (409)
            HTTPException: When the webhook URL already exists (409)

        """
        webhook_channels = cls._filter(user, exclude=channel, channel_type=ChannelType.WEBHOOK)
        if len(list(webhook_channels)) >= MAX_WEBHOOKS:
            raise HTTPException(HTTPStatus.CONFLICT, detail="Max amount of webhooks reached")

        for webhook_channel in webhook_channels:
            if cast(WebhookConfiguration, webhook_channel).url == channel.url:
                raise HTTPException(HTTPStatus.CONFLICT, detail="This webhook URL already exists")

    @classmethod
    def _validate_whatsapp_channels(cls, user: User, channel: WhatsappConfiguration) -> None:
        """
        Validate the user can add the channel based on the user's existing channels.

        Raises:
            HTTPException: When the user already has a WhatsApp channel (400)

        """
        whatsapp_channels = cls._filter(user, exclude=channel, channel_type=ChannelType.WHATSAPP)
        if any(whatsapp_channels):
            raise HTTPException(HTTPStatus.BAD_REQUEST, detail="Only one WhatsApp channel is allowed")

    @classmethod
    def _validate_ifttt_channels(cls, user: User, channel: IFTTTConfiguration) -> None:
        """
        Validate the user can add the channel based on the user's existing channels.

        Raises:
            HTTPException: When the user already has an IFTTT channel with a different key (409)
            HTTPException: When the user already has an IFTTT channel with the same event (409)

        """
        for ifttt_channel in cls._filter(user, exclude=channel, channel_type=ChannelType.IFTTT):
            ifttt_channel = cast(IFTTTConfiguration, ifttt_channel)
            if ifttt_channel.key != channel.key:
                raise HTTPException(HTTPStatus.BAD_REQUEST, detail="Only one IFTTT key is allowed per user")
            if ifttt_channel.event == channel.event:
                raise HTTPException(HTTPStatus.CONFLICT, detail="This IFTTT event already exists")

    @classmethod
    def validate(cls, user: User, channel: ChannelConfiguration) -> None:
        """Validate the user can add the channel based on the user's existing channels."""
        match channel.type_:
            case ChannelType.WHATSAPP:
                channel = cast(WhatsappConfiguration, channel)
                cls._validate_whatsapp_channels(user, channel)

            case ChannelType.IFTTT:
                channel = cast(IFTTTConfiguration, channel)
                cls._validate_ifttt_channels(user, channel)

            case ChannelType.WEBHOOK:
                channel = cast(WebhookConfiguration, channel)
                cls._validate_webhook_channels(user, channel)
