from app.raft.node import RaftRuntime
from fastapi import FastAPI, HTTPException
from pydantic import ValidationError
import httpx
from uuid import uuid4
from fastapi.middleware.cors import CORSMiddleware

from app.mcp.tools import invoke_tool, list_tools
from app.travel.simulator import prepare_hotel_booking
from app.config import NODE_ID, PEERS, CLUSTER_NODES
from app.mcp.schemas import BookHotelRequest
from app.registry.commands import BOOK_HOTEL
from app.raft.messages import (
    AppendEntriesRequest,
    RequestVoteRequest,
)



import asyncio
from contextlib import asynccontextmanager



@asynccontextmanager
async def lifespan(app: FastAPI):
    election_task = asyncio.create_task(
        raft_node.run_election_loop()
    )
    heartbeat_task = asyncio.create_task(
        raft_node.run_heartbeat_loop()
    )

    try:
        yield
    finally:
        election_task.cancel()
        heartbeat_task.cancel()

        for task in (election_task, heartbeat_task):
            try:
                await task
            except asyncio.CancelledError:
                pass


app = FastAPI(
    title="RaftMCP Travel",
    lifespan=lifespan,
)



app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --------------------------------------------------
# Raft node
# --------------------------------------------------

raft_node = RaftRuntime(
    node_id=NODE_ID,
    peers=PEERS,
)

# --------------------------------------------------
# Helper
# --------------------------------------------------

def call_tool(name: str, arguments: dict):
    try:
        return invoke_tool(name, arguments)
    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        )


# --------------------------------------------------
# Health
# --------------------------------------------------

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "node_id": NODE_ID,
        "is_active": True,
    }


# --------------------------------------------------
# Raft status
# --------------------------------------------------


@app.get("/raft/status")
async def raft_status():
    return raft_node.status()


@app.get("/raft/log")
async def raft_log():
    return raft_node.log_status()


@app.post("/raft/request-vote")
async def request_vote(request: RequestVoteRequest):
    return raft_node.handle_request_vote(request)


@app.post("/raft/append-entries")
async def append_entries(request: AppendEntriesRequest):
    return raft_node.handle_append_entries(request)



# --------------------------------------------------
# Tool registry
# --------------------------------------------------

@app.get("/tools")
async def tools():
    return {
        "tools": list_tools()
    }


@app.get("/registry/tools")
async def registry_tools():
    return {
        "tools": list_tools()
    }


# --------------------------------------------------
# Travel demo request
# --------------------------------------------------

@app.post("/demo/travel-request")
async def travel_request(payload: dict):
    request = payload.get("request", "")

    if not request:
        raise HTTPException(
            status_code=400,
            detail="Request is required",
        )

    return {
        "request": request,
        "status": "processed",
        "message": "Travel request received successfully.",
        "node_id": NODE_ID,
    }


# --------------------------------------------------
# Flight tools
# --------------------------------------------------

@app.post("/tools/search_flights")
async def search_flights(arguments: dict):
    return call_tool(
        "search_flights",
        arguments,
    )


@app.post("/tools/check_flight_status")
async def check_flight_status(arguments: dict):
    return call_tool(
        "check_flight_status",
        arguments,
    )


# --------------------------------------------------
# Hotel tools
# --------------------------------------------------

@app.post("/tools/search_hotels")
async def search_hotels(arguments: dict):
    return call_tool(
        "search_hotels",
        arguments,
    )



@app.post("/tools/book_hotel")
async def book_hotel(arguments: dict):
    try:
        request = BookHotelRequest(**arguments)
        booking_data = request.model_dump()
        booking = prepare_hotel_booking(
            **booking_data,
            booking_id=f"HOTEL-{uuid4().hex[:8].upper()}",
        )
    except (ValidationError, ValueError, TypeError) as error:
        raise HTTPException(status_code=400, detail=str(error))

    # Forward booking requests received by a follower to its known leader.
    if raft_node.state.role.value != "leader":
        leader_id = raft_node.state.leader_id
        leader_url = CLUSTER_NODES.get(leader_id)

        if not leader_url:
            raise HTTPException(
                status_code=503,
                detail={
                    "message": "No known leader is available. Please retry.",
                    "leader_id": leader_id,
                },
            )

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f"{leader_url}/tools/book_hotel",
                    json=booking_data,
                )
            if response.status_code >= 400:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=response.json().get("detail", response.text),
                )
            return response.json()
        except httpx.RequestError:
            raise HTTPException(
                status_code=503,
                detail="The known leader could not be reached. Please retry.",
            )

    try:
        result = await raft_node.submit_command({
            "command": BOOK_HOTEL,
            "booking": booking,
        })
    except RuntimeError as error:
        raise HTTPException(status_code=503, detail=str(error))

    if not result.get("success"):
        raise HTTPException(status_code=503, detail=result)

    return {
        "booking": booking,
        "raft": {
            "committed": True,
            "commit_index": result["commit_index"],
            "acknowledgments": result["acknowledgments"],
            "required": result["required"],
        },
    }


@app.get("/trips")
async def trips():
    return {
        "trips": raft_node.state.registry.list_bookings()
    }


# --------------------------------------------------
# AI Travel Agent
# --------------------------------------------------

@app.post("/agent/request")
async def agent_request(payload: dict):
    request = payload.get("request", "")

    if not request:
        raise HTTPException(
            status_code=400,
            detail="Request is required",
        )

    request_lower = request.lower()

    # Flight search
    if "flight" in request_lower and (
        "search" in request_lower
        or "find" in request_lower
        or "flight from" in request_lower
    ):
        return {
            "agent": "travel-agent",
            "intent": "search_flights",
            "message": "Flight search request received.",
            "next_step": "Use the search_flights MCP tool.",
        }

    # Flight status
    if "flight status" in request_lower:
        return {
            "agent": "travel-agent",
            "intent": "check_flight_status",
            "message": "Flight status request received.",
            "next_step": "Use the check_flight_status MCP tool.",
        }

    # Hotel search
    if "hotel" in request_lower and (
        "search" in request_lower
        or "find" in request_lower
        or "hotel in" in request_lower
    ):
        return {
            "agent": "travel-agent",
            "intent": "search_hotels",
            "message": "Hotel search request received.",
            "next_step": "Use the search_hotels MCP tool.",
        }

    # Hotel booking
    if "book" in request_lower and "hotel" in request_lower:
        return {
            "agent": "travel-agent",
            "intent": "book_hotel",
            "message": "Hotel booking request received.",
            "next_step": "Use the book_hotel MCP tool.",
        }

    return {
        "agent": "travel-agent",
        "intent": "unknown",
        "message": "I could not determine the travel request.",
    }
