import asyncio
from enum import StrEnum
from http import HTTPStatus

from fastapi import HTTPException
from google import auth
from googleapiclient.discovery import build

from cumplo_tailor.utils.constants import CLOUD_CREDENTIALS_SCOPES, CUMPLO_API_SERVICE


class CloudCredentials:
    """Google Cloud credentials integration."""

    class OperationKeys(StrEnum):
        """Keys for the operation response."""

        DONE = "done"
        ERROR = "error"
        RESPONSE = "response"

    @classmethod
    async def create_api_key(cls, name: str, delay: int = 1) -> str:
        """Create an API key for the given project ID."""
        credentials, project_id = auth.default(scopes=CLOUD_CREDENTIALS_SCOPES)
        apikeys_service = build("apikeys", version="v2", credentials=credentials)

        body = {
            "displayName": name,
            "restrictions": {"apiTargets": [{"service": CUMPLO_API_SERVICE}]},
        }

        parent = f"projects/{project_id}/locations/global"
        operation = apikeys_service.projects().locations().keys().create(parent=parent, body=body).execute()

        async def poll() -> dict:
            """
            Poll asynchronously for the operation to complete.

            Raises:
                HTTPException: If the API key creation fails.

            """
            operation_service = apikeys_service.operations()
            while True:
                result = operation_service.get(name=operation["name"]).execute()
                if cls.OperationKeys.DONE in result:
                    if cls.OperationKeys.RESPONSE in result:
                        return result[cls.OperationKeys.RESPONSE]
                    if cls.OperationKeys.ERROR in result:
                        error = result[cls.OperationKeys.ERROR]
                        raise HTTPException(HTTPStatus.BAD_GATEWAY, detail=error["message"])

                await asyncio.sleep(delay)

        response = await asyncio.wait_for(poll(), timeout=30)
        return response["keyString"]
