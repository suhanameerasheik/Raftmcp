from pydantic import BaseModel


class SearchFlightsRequest(BaseModel):
    origin: str
    destination: str
    departure_date: str | None = None
    passengers: int = 1


class FlightStatusRequest(BaseModel):
    flight_number: str
    date: str | None = None


class SearchHotelsRequest(BaseModel):
    city: str
    check_in: str | None = None
    check_out: str | None = None
    guests: int = 1
class BookHotelRequest(BaseModel):
    hotel: str
    city: str
    check_in: str
    check_out: str
    guests: int = 1
