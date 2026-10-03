
import asyncio
import os
import tempfile
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse

from .config import NODE_ID, PEERS, CLUSTER_NODES
from .node import RaftNode
from .raft.node import RaftRuntime
from .raft.messages import (
    RequestVoteRequest,
    HeartbeatRequest,
    AppendEntriesRequest,
)
from .raft.heartbeat import HeartbeatManager
from .raft.state import NodeRole

from .har.parser import parse_har
from .har.extractor import extract_travel_requests
from .har.sanitizer import sanitize_request
from .har.generator import generate_tool_definitions

from .mcp.server import call_tool, get_registered_tools
from .registry.commands import (
    ADD_TOOL,
    UPDATE_TOOL,
    DELETE_TOOL,
    validate_command,
)


node = RaftNode(node_id=NODE_ID)

raft = RaftRuntime(
    node_id=NODE_ID,
    peers=PEERS,
)

heartbeat_manager = HeartbeatManager(
    raft.state,
    raft.election,
    peers=PEERS,
)

generated_tools = []


@asynccontextmanager
async def lifespan(app: FastAPI):
    election_task = asyncio.create_task(
        raft.run_election_loop()
    )
    heartbeat_task = asyncio.create_task(
        heartbeat_manager.run_heartbeat_loop()
    )

    try:
        yield
    finally:
        election_task.cancel()
        heartbeat_task.cancel()

        await asyncio.gather(
            election_task,
            heartbeat_task,
            return_exceptions=True,
        )


app = FastAPI(
    title="RaftMCP for Travel",
    lifespan=lifespan,
)


@app.middleware("http")
async def reject_requests_when_inactive(request, call_next):
    allowed_while_inactive = {
        "/admin/kill",
        "/admin/restart",
        "/raft/status",
        "/raft/log",
        "/health",
    }

    if (
        not raft.state.is_active
        and request.url.path not in allowed_while_inactive
    ):
        return JSONResponse(
            status_code=503,
            content={
                "detail": "Node is inactive.",
                "node_id": NODE_ID,
            },
        )

    return await call_next(request)


async def submit_registry_command(command: dict) -> dict:
    try:
        validate_command(command)
    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        )

    if raft.state.role == NodeRole.LEADER:
        try:
            return await raft.submit_command(command)
        except RuntimeError as error:
            raise HTTPException(
                status_code=409,
                detail=str(error),
            )

    leader_id = raft.state.leader_id

    if not leader_id or leader_id not in CLUSTER_NODES:
        raise HTTPException(
            status_code=503,
            detail={
                "message": "Leader is unknown. Retry after an election.",
                "leader_id": leader_id,
            },
        )

    leader_url = CLUSTER_NODES[leader_id]

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(
                f"{leader_url}/registry/commands",
                json=command,
            )
            response.raise_for_status()
            return response.json()

    except httpx.HTTPStatusError as error:
        try:
            detail = error.response.json().get(
                "detail",
                "Leader rejected the registry command.",
            )
        except ValueError:
            detail = "Leader rejected the registry command."

        raise HTTPException(
            status_code=error.response.status_code,
            detail=detail,
        )
    except (httpx.HTTPError, ValueError):
        raise HTTPException(
            status_code=502,
            detail="Could not contact the Raft leader.",
        )


@app.post("/admin/kill")
async def simulate_node_failure():
    if not raft.state.is_active:
        return {
            "success": True,
            "message": "Node is already inactive.",
            "node_id": NODE_ID,
        }

    raft.state.is_active = False
    raft.state.role = NodeRole.FOLLOWER
    raft.state.leader_id = None
    raft.state.votes_received.clear()

    return {
        "success": True,
        "message": "Node failure simulated.",
        "node_id": NODE_ID,
        "is_active": raft.state.is_active,
    }


@app.post("/admin/restart")
async def restart_node():
    if raft.state.is_active:
        return {
            "success": True,
            "message": "Node is already active.",
            "node_id": NODE_ID,
            "is_active": True,
        }

    raft.state.is_active = True
    raft.state.role = NodeRole.FOLLOWER
    raft.state.leader_id = None
    raft.state.voted_for = None
    raft.state.votes_received.clear()
    raft.election.reset_timeout()

    return {
        "success": True,
        "message": "Node reactivated. Waiting for cluster synchronization.",
        "node_id": NODE_ID,
        "is_active": True,
    }


@app.get("/health")
async def health():
    result = node.health()
    result["is_active"] = raft.state.is_active
    return result


@app.get("/raft/status")
async def raft_status():
    return raft.status()


@app.get("/raft/log")
async def raft_log():
    return raft.log_status()


@app.post("/raft/request-vote")
async def request_vote(request: RequestVoteRequest):
    return raft.handle_request_vote(request)


@app.post("/raft/heartbeat")
async def receive_heartbeat(request: HeartbeatRequest):
    return heartbeat_manager.receive_heartbeat(request)


@app.post("/raft/append-entries")
async def append_entries(request: AppendEntriesRequest):
    return raft.handle_append_entries(request)


@app.post("/raft/command")
async def submit_command(command: dict):
    return await submit_registry_command(command)


@app.post("/registry/commands")
async def registry_command(command: dict):
    return await submit_registry_command(command)


@app.get("/registry/tools")
async def get_registry_tools():
    tools = raft.state.registry.list_tools()

    return {
        "node_id": NODE_ID,
        "count": len(tools),
        "commit_index": raft.state.commit_index,
        "tools": tools,
    }


@app.get("/cluster/consistency")
async def cluster_consistency():
    node_urls = {
        NODE_ID: None,
        **{
            peer_id: peer_url
            for peer_id, peer_url in CLUSTER_NODES.items()
            if peer_id != NODE_ID
        },
    }

    reports = {}
    unavailable = []

    async with httpx.AsyncClient(timeout=3.0) as client:
        for node_id, url in node_urls.items():
            try:
                if node_id == NODE_ID:
                    response_data = {
                        "node_id": NODE_ID,
                        "count": len(raft.state.registry.list_tools()),
                        "commit_index": raft.state.commit_index,
                        "tools": raft.state.registry.list_tools(),
                    }
                else:
                    response = await client.get(
                        f"{url}/registry/tools"
                    )
                    response.raise_for_status()
                    response_data = response.json()

                reports[node_id] = {
                    "count": response_data.get("count"),
                    "commit_index": response_data.get("commit_index"),
                    "tools": response_data.get("tools", []),
                }

            except (httpx.HTTPError, ValueError):
                unavailable.append(node_id)

    if unavailable:
        status = "UNAVAILABLE"
    else:
        signatures = {
            node_id: sorted(
                report["tools"],
                key=lambda item: item.get("name", ""),
            )
            for node_id, report in reports.items()
        }

        first_signature = next(iter(signatures.values()), [])
        all_match = all(
            signature == first_signature
            for signature in signatures.values()
        )

        status = "CONSISTENT" if all_match else "INCONSISTENT"

    return {
        "status": status,
        "node_count": len(node_urls),
        "available_nodes": list(reports.keys()),
        "unavailable_nodes": unavailable,
        "nodes": reports,
    }


@app.post("/registry/register-generated")
async def register_generated_tools():
    if not generated_tools:
        raise HTTPException(
            status_code=400,
            detail="No generated tools available. Upload a HAR file first.",
        )

    results = []

    for tool in generated_tools:
        command = {
            "command": ADD_TOOL,
            "tool": tool,
        }

        result = await submit_registry_command(command)

        results.append({
            "tool": tool["name"],
            "result": result,
        })

        if not result.get("success", False):
            break

    return {
        "registered": sum(
            1
            for item in results
            if item["result"].get("success", False)
        ),
        "total_generated": len(generated_tools),
        "results": results,
    }


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


@app.get("/mcp/tools")
async def list_mcp_tools():
    tools = get_registered_tools()

    return {
        "count": len(tools),
        "tools": tools,
    }


@app.post("/tools/search_flights")
async def search_flights(arguments: dict):
    try:
        return call_tool("search_flights", arguments)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))


@app.post("/tools/check_flight_status")
async def check_flight_status(arguments: dict):
    try:
        return call_tool("check_flight_status", arguments)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))


@app.post("/tools/search_hotels")
async def search_hotels(arguments: dict):
    try:
        return call_tool("search_hotels", arguments)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))