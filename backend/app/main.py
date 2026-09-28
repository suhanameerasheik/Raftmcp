import os
import tempfile

from fastapi import FastAPI, File, UploadFile

from .config import NODE_ID
from .node import RaftNode
from .har.parser import parse_har
from .har.extractor import extract_travel_requests
from .har.sanitizer import sanitize_request
from .har.generator import generate_tool_definitions


app = FastAPI(title="RaftMCP for Travel")

node = RaftNode(node_id=NODE_ID)

generated_tools = []


@app.get("/health")
async def health():
    return node.health()


@app.post("/tools/generate")
async def generate_tools(file: UploadFile = File(...)):
    contents = await file.read()

    with tempfile.NamedTemporaryFile(
        suffix=".har",
        delete=False,
    ) as temp_file:
        temp_file.write(contents)
        temp_path = temp_file.name

    try:
        har_data = parse_har(temp_path)

        extracted_requests = extract_travel_requests(har_data)

        sanitized_requests = [
            sanitize_request(request)
            for request in extracted_requests
        ]

        tools = generate_tool_definitions(sanitized_requests)

        generated_tools.clear()
        generated_tools.extend(tools)

        return {
            "count": len(tools),
            "tools": tools,
        }

    finally:
        os.unlink(temp_path)


@app.get("/tools")
async def get_tools():
    return {
        "count": len(generated_tools),
        "tools": generated_tools,
    }
