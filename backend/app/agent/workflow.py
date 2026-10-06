import re

from app.agent.agent import TravelAgent


AIRPORT_CODES = {
    "delhi": "DEL",
    "mumbai": "BOM",
    "bangalore": "BLR",
    "bengaluru": "BLR",
    "hyderabad": "HYD",
    "chennai": "MAA",
    "kolkata": "CCU",
    "pune": "PNQ",
}


class TravelWorkflow:
    def __init__(self):
        self.agent = TravelAgent()

    async def process_request(self, user_request: str):
        request = user_request.strip()
        lower_request = request.lower()

        # Check flight status
        if "status" in lower_request and "flight" in lower_request:
            match = re.search(
                r"\b[A-Z]{2}\d{2,4}\b",
                request,
                re.IGNORECASE,
            )

            if not match:
                raise ValueError(
                    "Please provide a flight number, such as AI202."
                )

            return await self.agent.call_tool(
                "check_flight_status",
                {"flight_number": match.group(0)},
            )

        # Search flights
        if "flight" in lower_request and any(
            word in lower_request
            for word in ["search", "find", "book", "available"]
        ):
            match = re.search(
                r"\bfrom\s+([A-Za-z ]+?)\s+to\s+([A-Za-z ]+?)(?:\s+on\s+|$)",
                request,
                re.IGNORECASE,
            )

            if not match:
                raise ValueError(
                    "Use a format like: "
                    "Search flights from Hyderabad to Delhi."
                )

            origin = match.group(1).strip()
            destination = match.group(2).strip()

            origin_code = AIRPORT_CODES.get(
                origin.lower(),
                origin,
            )

            destination_code = AIRPORT_CODES.get(
                destination.lower(),
                destination,
            )

            return await self.agent.call_tool(
                "search_flights",
                {
                    "origin": origin_code,
                    "destination": destination_code,
                },
            )

        # Search hotels
        if "hotel" in lower_request and any(
            word in lower_request
            for word in ["search", "find", "available", "book"]
        ):
            match = re.search(
                r"\b(?:in|at)\s+([A-Za-z ]+)",
                request,
                re.IGNORECASE,
            )

            if not match:
                raise ValueError(
                    "Use a format like: Find hotels in Hyderabad."
                )

            return await self.agent.call_tool(
                "search_hotels",
                {"city": match.group(1).strip()},
            )

        raise ValueError(
            "I can help check flight status, search flights, "
            "or search hotels."
        )
