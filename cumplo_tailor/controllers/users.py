import ulid
from cumplo_common.database import firestore
from cumplo_common.models.user import User

from cumplo_tailor.integrations import CloudCredentials


class UsersController:
    """Controller for the users."""

    @staticmethod
    async def create(payload: dict) -> User:
        """Create a new user."""
        id_user = ulid.new()
        api_key = await CloudCredentials.create_api_key(str(id_user))
        user = User.model_validate({**payload, "id": id_user, "api_key": api_key})

        firestore.client.users.create(user)
        return user
