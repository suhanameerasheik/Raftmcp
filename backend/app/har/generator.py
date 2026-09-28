TOOL_METADATA = {
    "/api/flights/search": {
        "name": "search_flights",
        "description": "Search available flights using origin, destination, departure date, and passenger count.",
    },
    "/api/flights/status": {
        "name": "check_flight_status",
        "description": "Check the current status of a flight by flight number and date.",
    },
    "/api/hotels/search": {
        "name": "search_hotels",
        "description": "Search hotels by city, check-in date, check-out date, and guest count.",
    },
}


def infer_type(parameter_name: str, value: str) -> str:
    integer_parameters = {
        "passengers",
        "guests",
    }

    if parameter_name in integer_parameters:
        return "integer"

    return "string"


def generate_tool(request: dict) -> dict:
    endpoint = request["endpoint"]

    if endpoint not in TOOL_METADATA:
        raise ValueError(f"Unsupported travel endpoint: {endpoint}")

    metadata = TOOL_METADATA[endpoint]

    properties = {}

    for name, value in request.get("query_parameters", {}).items():
        properties[name] = {
            "type": infer_type(name, value),
            "description": f"Value for {name}.",
        }

    return {
        "name": metadata["name"],
        "description": metadata["description"],
        "method": request["method"],
        "endpoint": endpoint,
        "input_schema": {
            "type": "object",
            "properties": properties,
            "required": list(properties.keys()),
        },
    }


def generate_tool_definitions(requests: list[dict]) -> list[dict]:
    tools = []

    for request in requests:
        tools.append(generate_tool(request))

    return tools
