from http import HTTPStatus
from logging import getLogger
from typing import Annotated, cast

from cumplo_common.database.firestore import firestore_client
from cumplo_common.models.configuration import Configuration
from cumplo_common.models.user import User
from fastapi import APIRouter
from fastapi.exceptions import HTTPException
from fastapi.requests import Request
from schemas.configurations import ConfigurationPayload
from utils.constants import MAX_CONFIGURATIONS

logger = getLogger(__name__)

router = APIRouter(prefix="/filters/configurations")


@router.get("", status_code=HTTPStatus.OK)
async def get_configurations(request: Request) -> list[Annotated[dict, Configuration]]:
    """Gets a list of existing configurations."""
    user = cast(User, request.state.user)
    return [configuration.model_dump(exclude_none=True) for configuration in user.configurations.values()]


@router.get("/{id_configuration}", status_code=HTTPStatus.OK)
async def get_single_configurations(request: Request, id_configuration: int) -> Annotated[dict, Configuration]:
    """
    Gets a single configuration.
    """
    user = cast(User, request.state.user)
    if not (configuration := user.configurations.get(id_configuration)):
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND)

    return configuration.model_dump(exclude_none=True)


@router.post("", status_code=HTTPStatus.CREATED)
async def post_configuration(request: Request, payload: ConfigurationPayload) -> Annotated[dict, Configuration]:
    """
    Creates a configuration.
    """
    user = cast(User, request.state.user)
    if len(user.configurations) >= MAX_CONFIGURATIONS:
        raise HTTPException(status_code=HTTPStatus.TOO_MANY_REQUESTS, detail="Max amount of configurations reached")

    id_configuration = max(user.configurations.keys(), default=0) + 1
    configuration = Configuration(id=id_configuration, **payload.model_dump(exclude_none=True))

    if configuration in user.configurations.values():
        raise HTTPException(status_code=HTTPStatus.CONFLICT, detail="Configuration already exists")

    firestore_client.put_configuration(user.id, configuration)
    return configuration.serialize()


@router.put("/{id_configuration}", status_code=HTTPStatus.NO_CONTENT)
async def put_configuration(request: Request, payload: ConfigurationPayload, id_configuration: int) -> None:
    """
    Updates a configuration.
    """
    user = cast(User, request.state.user)
    if not (configuration := user.configurations.get(id_configuration)):
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND)

    new_configuration = configuration.model_copy(update=payload.model_dump(exclude_none=True))
    if new_configuration in user.configurations.values():
        raise HTTPException(status_code=HTTPStatus.CONFLICT, detail="Configuration already exists")

    return firestore_client.put_configuration(user.id, configuration)


@router.delete("/{id_configuration}", status_code=HTTPStatus.NO_CONTENT)
async def delete_configuration(request: Request, id_configuration: int) -> None:
    """
    Deletes a configuration.
    """
    user = cast(User, request.state.user)
    if not (configuration := user.configurations.get(id_configuration)):
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND)

    return firestore_client.delete_configuration(user.id, configuration.id)
