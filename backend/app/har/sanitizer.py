SENSITIVE_HEADER_NAMES = {
    "authorization",
    "cookie",
    "set-cookie",
    "x-api-key",
    "api-key",
    "token",
    "access-token",
    "refresh-token",
    "password",
}


SENSITIVE_NAME_PARTS = {
    "authorization",
    "cookie",
    "token",
    "api_key",
    "apikey",
    "password",
    "secret",
}


def is_sensitive_name(name: str) -> bool:
    normalized = name.lower().replace("-", "_")

    if normalized in SENSITIVE_HEADER_NAMES:
        return True

    return any(part in normalized for part in SENSITIVE_NAME_PARTS)


def sanitize_headers(headers: dict) -> dict:
    sanitized = {}

    for name, value in headers.items():
        if is_sensitive_name(name):
            continue

        sanitized[name] = value

    return sanitized


def sanitize_query_parameters(parameters: dict) -> dict:
    sanitized = {}

    for name, value in parameters.items():
        if is_sensitive_name(name):
            continue

        sanitized[name] = value

    return sanitized


def sanitize_request(request: dict) -> dict:
    return {
        "method": request["method"],
        "endpoint": request["endpoint"],
        "query_parameters": sanitize_query_parameters(
            request.get("query_parameters", {})
        ),
        "headers": sanitize_headers(
            request.get("headers", {})
        ),
    }
