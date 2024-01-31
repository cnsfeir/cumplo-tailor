from http import HTTPStatus
from logging import getLogger
from typing import Annotated, cast

from business.channels import ChannelConfigurationFactory
from cumplo_common.database.firestore import firestore_client
from cumplo_common.models.channel import ChannelConfiguration, ChannelType
from cumplo_common.models.user import User
from fastapi import APIRouter
from fastapi.exceptions import HTTPException
from fastapi.requests import Request

logger = getLogger(__name__)

router = APIRouter(prefix="/channels")


@router.post("/{channel_type}", status_code=HTTPStatus.CREATED)
async def get_configurations(
    request: Request, channel_type: ChannelType, payload: dict
) -> Annotated[dict, ChannelConfiguration]:
    """Posts a new channel configuration."""
    user = cast(User, request.state.user)
    if not (configuration := ChannelConfigurationFactory.create_channel_configuration(channel_type, payload)):
        raise HTTPException(HTTPStatus.UNPROCESSABLE_ENTITY)

    firestore_client.put_channel(user.id, configuration)
    return configuration.model_dump(exclude_none=True)


# TODO: Add a is_active field to the channel configuration, so we can deactivate it (soft delete)
# TODO: Make the PATCH endpopint for the configuration
# TODO: Make the DELETE endpoint for the configuration
