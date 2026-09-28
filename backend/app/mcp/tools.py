from .schemas import (
    FlightStatusRequest,
    SearchFlightsRequest,
    SearchHotelsRequest,
)
from ..travel.simulator import (
    check_flight_status,
    search_flights,
    search_hotels,
)


TOOLS = {
    "search_flights": {
        "name": "search_flights",
        "description": "Search available flights.",
        "input_schema": SearchFlightsRequest,
        "handler": search_flights,
    },
    "check_flight_status": {
        "name": "check_flight_status",
        "description": "Check the current status of a flight.",
        "input_schema": FlightStatusRequest,
        "handler": check_flight_status,
    },
    "search_hotels": {
        "name": "search_hotels",
        "description": "Search available hotels.",
        "input_schema": SearchHotelsRequest,
        "handler": search_hotels,
    },
}


def list_tools() -> list[dict]:
    return [
        {
            "name": tool["name"],
            "description": tool["description"],
        }
        for tool in TOOLS.values()
    ]


def invoke_tool(name: str, arguments: dict) -> dict:
    if name not in TOOLS:
        raise ValueError(f"Unknown tool: {name}")

    tool = TOOLS[name]

    request = tool["input_schema"](**arguments)

    return tool["handler"](**request.model_dump())
