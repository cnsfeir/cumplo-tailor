from http import HTTPStatus
from logging import getLogger
from typing import cast

import ulid
from cumplo_common.database import firestore
from cumplo_common.models.filter_configuration import FilterConfiguration
from cumplo_common.models.user import User
from fastapi import APIRouter
from fastapi.exceptions import HTTPException
from fastapi.requests import Request

from cumplo_tailor.utils.constants import MAX_FILTERS
from cumplo_tailor.utils.dictionary import update_dictionary

logger = getLogger(__name__)

router = APIRouter(prefix="/filters")


@router.get("", status_code=HTTPStatus.OK)
def _list_filters(request: Request) -> list[dict]:
    """List the existing filters."""
    user = cast(User, request.state.user)
    return [filter_.json() for filter_ in user.filters.values()]


@router.get("/{id_filter}", status_code=HTTPStatus.OK)
def _retrieve_filter(request: Request, id_filter: str) -> dict:
    """
    Retrieve a single filter configuration.

    Raises:
        HTTPException: If the filter is not found (404)

    """
    user = cast(User, request.state.user)
    if not (filter_ := user.filters.get(id_filter)):
        raise HTTPException(HTTPStatus.NOT_FOUND)

    return filter_.json()


@router.post("", status_code=HTTPStatus.CREATED)
def _create_filter(request: Request, payload: dict) -> dict:
    """
    Create a new filter configuration.

    Raises:
        HTTPException: If the max amount of filters is reached or the filter already exists (409)

    """
    user = cast(User, request.state.user)
    if len(user.filters) >= MAX_FILTERS:
        raise HTTPException(HTTPStatus.CONFLICT, detail="Max amount of filters reached")

    filter_ = FilterConfiguration.model_validate({"id": ulid.new(), **payload})

    if filter_ in user.filters.values():
        raise HTTPException(HTTPStatus.CONFLICT, detail="Filter already exists")

    user.filters[str(filter_.id)] = filter_
    firestore.client.users.put(user)
    return filter_.json()


@router.patch("/{id_filter}", status_code=HTTPStatus.OK)
def _update_filter(request: Request, payload: dict, id_filter: str) -> dict:
    """
    Update a filter configuration.

    Raises:
        HTTPException: If the filter is not found (404)
        HTTPException: If there are no changes to update (400)
        HTTPException: If the updated filter already exists (409)

    """
    user = cast(User, request.state.user)
    if not (filter_ := user.filters.get(id_filter)):
        raise HTTPException(HTTPStatus.NOT_FOUND)

    data = update_dictionary(filter_.model_dump(), payload)
    new_filter = FilterConfiguration.model_validate(data)

    # NOTE: If the only change is the name, then we don't need to check for conflicts
    if not ("name" in payload and len(payload) == 1):
        if new_filter == filter_:
            raise HTTPException(HTTPStatus.OK, detail="Nothing to update")

        if new_filter in user.filters.values():
            raise HTTPException(HTTPStatus.CONFLICT, detail="The updated filter already exists")

    user.filters[str(new_filter.id)] = new_filter
    firestore.client.users.put(user)
    return new_filter.json()


@router.delete("/{id_filter}", status_code=HTTPStatus.NO_CONTENT)
def _delete_filter(request: Request, id_filter: str) -> None:
    """
    Delete a filter configuration.

    Raises:
        HTTPException: If the filter is not found (404)

    """
    user = cast(User, request.state.user)
    if not (user.filters.get(id_filter)):
        raise HTTPException(HTTPStatus.NOT_FOUND)

    del user.filters[id_filter]
    firestore.client.users.put(user)
