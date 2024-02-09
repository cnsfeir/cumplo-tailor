from typing import Any

import ulid
from cumplo_common.models.filter_configuration import FilterConfiguration
from pydantic import TypeAdapter


class FilterConfigurationPayload(FilterConfiguration):
    """
    Represents the payload for creating or updating a filter configuration.
    """

    def __init__(self, **data: Any) -> None:
        super().__init__(id=ulid.new(), **data)

    def to_filter(self) -> FilterConfiguration:
        """
        Exports the payload as a FilterConfiguration object.

        Returns:
            FilterConfiguration: The FilterConfiguration object.
        """
        return TypeAdapter(FilterConfiguration).validate_python(self.model_dump())
