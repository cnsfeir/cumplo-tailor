import json

from flask import Request

from models.configuration import FilterConfiguration


def get_configuration(request: Request) -> FilterConfiguration:
    """
    Gets the configuration from the request.
    """
    if data := request.data:
        return FilterConfiguration(**json.loads(data))

    return FilterConfiguration()
