from logging import getLogger

from cumplo_common.models.channel import CHANNEL_CONFIGURATION_BY_TYPE, ChannelConfiguration, ChannelType
from pydantic import TypeAdapter

logger = getLogger(__name__)


class ChannelConfigurationFactory:
    @staticmethod
    def create_channel_configuration(channel_type: ChannelType, payload: dict) -> ChannelConfiguration | None:
        """
        Creates a new ChannelConfiguration class.
        """
        try:
            return TypeAdapter(CHANNEL_CONFIGURATION_BY_TYPE[channel_type]).validate_python(payload)

        except ValueError:
            logger.warning(f"Invalid payload for channel type '{channel_type}': {payload}")

        return None
