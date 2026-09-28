from urllib.parse import urlparse

TRAVEL_ENDPOINTS = {
    "/api/flights/search",
    "/api/flights/status",
    "/api/hotels/search",
}


def extract_travel_requests(har_data: dict) -> list[dict]:
    entries = har_data["log"]["entries"]

    extracted = []

    for entry in entries:
        request = entry.get("request", {})

        method = request.get("method", "").upper()
        url = request.get("url", "")

        if not url:
            continue

        parsed_url = urlparse(url)
        endpoint = parsed_url.path

        if endpoint not in TRAVEL_ENDPOINTS:
            continue

        query_parameters = {}

        for parameter in request.get("queryString", []):
            name = parameter.get("name")

            if name:
                query_parameters[name] = parameter.get("value", "")

        headers = {}

        for header in request.get("headers", []):
            name = header.get("name")

            if name:
                headers[name] = header.get("value", "")

        extracted.append(
            {
                "method": method,
                "endpoint": endpoint,
                "query_parameters": query_parameters,
                "headers": headers,
            }
        )

    return extracted
