from .schemas import (
    FlightStatusRequest,
    SearchFlightsRequest,
    SearchHotelsRequest,
    BookHotelRequest,
)
from app.travel.simulator import (
    search_flights,
    check_flight_status,
    search_hotels,
    book_hotel,
    get_bookings,
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
        "description": "Search hotels by city, dates, and guests.",
        "input_schema": SearchHotelsRequest,
        "handler": search_hotels,
    },
    "book_hotel": {
    "name": "book_hotel",
    "description": "Book a hotel for the selected dates and guests.",
    "input_schema": BookHotelRequest,
    "handler": book_hotel,
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
