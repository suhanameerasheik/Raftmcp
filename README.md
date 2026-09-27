# RaftMCP for Travel

A fault-tolerant distributed MCP tool registry for agentic travel technology.

## Project

RaftMCP for Travel provides a distributed and fault-tolerant infrastructure for travel AI agents.

The system is designed to maintain availability of travel tools such as:

- Flight status
- Flight search
- Hotel search
- Rebooking
- Cancellation
- Refund workflows

## Current Status

### Day 1

- FastAPI backend
- Basic 3-node cluster structure
- Node health endpoints
- Git/GitHub setup

## Nodes

| Node | Port |
|---|---:|
| node-1 | 8001 |
| node-2 | 8002 |
| node-3 | 8003 |

## Planned Raft Features

- Follower / Candidate / Leader
- Terms
- Leader election
- RequestVote
- Heartbeats
- AppendEntries
- Log replication
- Majority quorum
- Commit index
- Leader failure
- Automatic failover
- Node recovery

## Tech Stack

- Python
- FastAPI
- asyncio
- Raft consensus
- MCP
- React
