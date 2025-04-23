import re
from http import HTTPStatus
from logging import getLogger

from cumplo_common.database import firestore
from cumplo_common.integrations.gmail import Gmail
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from cumplo_tailor.controllers import UsersController
from cumplo_tailor.utils.constants import PATTERN_BY_SENDER

logger = getLogger(__name__)

router = APIRouter(prefix="/subscriptions")


class SubscriptionEvent(BaseModel):
    """Model for a subscription event."""

    email: str = Field(alias="emailAddress")
    history_id: int = Field(alias="historyId")


@router.post("/renew", status_code=HTTPStatus.OK)
async def _renew() -> None:
    """Renew the subscription to the Gmail label."""
    logger.info("Renewing subscription to Gmail label")
    Gmail.subscribe()


@router.post("", status_code=HTTPStatus.OK)
async def _create_subscription(payload: SubscriptionEvent) -> None:
    """
    Create a new subscription.

    Returns:
        The response object.

    Raises:
        HTTPException: If the user is already subscribed.

    """
    if not (message := Gmail.get_message()):
        return logger.warning("Message not found")

    if not (sender := message.get("sender")):
        return logger.warning(f"Sender not found for message {message.get('id')}")

    if not (pattern := PATTERN_BY_SENDER.get(sender)):
        return logger.warning(f"Unknown sender for sender {sender}")

    snippet = message.get("snippet", "")
    if not (match := re.search(pattern, snippet)):
        return logger.warning(f"Pattern not found for sender {sender}")

    name = match.group(1)
    email = match.group(2)
    logger.info(f"Extracted {name=} and {email=} from subscription notification")

    try:
        user = firestore.client.users.get(email=email)
    except KeyError:
        pass
    else:
        logger.info(f"User {user.id} already subscribed with email {payload.email}")
        raise HTTPException(status_code=HTTPStatus.OK)

    user = await UsersController.create(payload={"email": email, "name": name})
    logger.info(f"Created user {user.id} with {email=}")
    return None
