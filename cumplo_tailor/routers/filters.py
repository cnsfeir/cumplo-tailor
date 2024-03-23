from http import HTTPStatus
from logging import getLogger
from typing import cast

from cumplo_common.database import firestore
from cumplo_common.models.filter_configuration import FilterConfiguration
from cumplo_common.models.user import User
from fastapi import APIRouter
from fastapi.exceptions import HTTPException
from fastapi.requests import Request
from pydantic import ValidationError

from cumplo_tailor.schemas.filters import FilterConfigurationPayload
from cumplo_tailor.utils.constants import MAX_CONFIGURATIONS

logger = getLogger(__name__)

router = APIRouter(prefix="/filters")


@router.get("", status_code=HTTPStatus.OK)
def _get_filters(request: Request) -> list[dict]:
    """Gets a list of existing filters configurations."""
    user = cast(User, request.state.user)
    return [filter_.json() for filter_ in user.filters.values()]


@router.get("/{id_filter}", status_code=HTTPStatus.OK)
def _get_single_filter(request: Request, id_filter: str) -> dict:
    """
    Gets a single filter configuration.
    """
    user = cast(User, request.state.user)
    if not (filter_ := user.filters.get(id_filter)):
        raise HTTPException(HTTPStatus.NOT_FOUND)

    return filter_.json()


@router.post("", status_code=HTTPStatus.CREATED)
def _post_filter(request: Request, payload: FilterConfigurationPayload) -> dict:
    """
    Creates a new filter configuration.
    """
    user = cast(User, request.state.user)
    if len(user.filters) >= MAX_CONFIGURATIONS:
        raise HTTPException(HTTPStatus.TOO_MANY_REQUESTS, detail="Max amount of filters reached")

    if (filter_ := payload.to_filter()) in user.filters.values():
        raise HTTPException(HTTPStatus.CONFLICT, detail="Filter already exists")

    firestore.client.filters.put(str(user.id), filter_)
    return filter_.json()


@router.patch("/{id_filter}", status_code=HTTPStatus.OK)
def _patch_filter(request: Request, payload: dict, id_filter: str) -> dict:
    """
    Updates a filter configuration.
    """
    user = cast(User, request.state.user)
    if not (filter_ := user.filters.get(id_filter)):
        raise HTTPException(HTTPStatus.NOT_FOUND)

    try:
        new_filter = FilterConfiguration.model_validate({**filter_.model_dump(), **payload})
    except ValidationError as error:
        raise HTTPException(HTTPStatus.UNPROCESSABLE_ENTITY, detail=error.errors()) from error

    if new_filter == filter_:
        raise HTTPException(HTTPStatus.BAD_REQUEST, detail="Nothing to update")

    if new_filter in user.filters.values():
        raise HTTPException(HTTPStatus.CONFLICT, detail="The updated Filter already exists")

    firestore.client.filters.put(str(user.id), new_filter)
    return new_filter.json()


@router.delete("/{id_filter}", status_code=HTTPStatus.NO_CONTENT)
def _delete_filter(request: Request, id_filter: str) -> None:
    """
    Deletes a filter configuration.
    """
    user = cast(User, request.state.user)
    if not (filter_ := user.filters.get(id_filter)):
        raise HTTPException(HTTPStatus.NOT_FOUND)

    return firestore.client.filters.delete(str(user.id), str(filter_.id))
