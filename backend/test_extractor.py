from app.har.parser import parse_har
from app.har.extractor import extract_travel_requests
from app.har.sanitizer import sanitize_request
from app.har.generator import generate_tool_definitions


har_data = parse_har("backend/sample_data/travel.har")

requests = extract_travel_requests(har_data)

sanitized_requests = [
    sanitize_request(request)
    for request in requests
]

tools = generate_tool_definitions(sanitized_requests)

for tool in tools:
    print("=" * 60)
    print(tool)
