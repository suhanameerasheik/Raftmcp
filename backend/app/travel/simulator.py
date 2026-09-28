from .data import FLIGHTS, HOTELS


def search_flights(
    origin: str,
    destination: str,
    departure_date: str | None = None,
    passengers: int = 1,
) -> dict:
    matches = [
        flight
        for flight in FLIGHTS
        if flight["from"] == origin.upper()
        and flight["to"] == destination.upper()
    ]

    return {
        "origin": origin.upper(),
        "destination": destination.upper(),
        "departure_date": departure_date,
        "passengers": passengers,
        "results": matches,
    }


def check_flight_status(
    flight_number: str,
    date: str | None = None,
) -> dict:
    for flight in FLIGHTS:
        if flight["flight"].upper() == flight_number.upper():
            return {
                "flight": flight["flight"],
                "date": date,
                "status": flight["status"],
            }

    return {
        "flight": flight_number,
        "date": date,
        "status": "NOT_FOUND",
    }


def search_hotels(
    city: str,
    check_in: str | None = None,
    check_out: str | None = None,
    guests: int = 1,
) -> dict:
    matches = [
        hotel
        for hotel in HOTELS
        if hotel["city"].lower() == city.lower()
    ]

    return {
        "city": city,
        "check_in": check_in,
        "check_out": check_out,
        "guests": guests,
        "results": matches,
    }
