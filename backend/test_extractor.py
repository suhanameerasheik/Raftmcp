from app.har.parser import parse_har
from app.har.extractor import extract_travel_requests


def test_har_parsing():
    har_data = parse_har("sample_data/travel.har")
    assert har_data is not None


def test_travel_request_extraction():
    har_data = parse_har("sample_data/travel.har")
    requests = extract_travel_requests(har_data)
    assert isinstance(requests, list)

