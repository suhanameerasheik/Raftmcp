import json


def parse_har(file_path: str) -> dict:
    with open(file_path, "r", encoding="utf-8") as file:
        har_data = json.load(file)

    if "log" not in har_data:
        raise ValueError("Invalid HAR file: missing 'log'")

    if "entries" not in har_data["log"]:
        raise ValueError("Invalid HAR file: missing 'entries'")

    return har_data

